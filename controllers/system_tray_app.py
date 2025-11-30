import sys
import os
import subprocess
from threading import Thread
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QFont, QBrush
from PySide6.QtCore import QObject, Qt, QRect, QTimer

import resources_rc
import api_server
from models.security_manager import SecurityManager
from views.main_window import MainWindow
from models.sentinel_worker import SentinelWorker
from models.app_logger import AppLogger
from views.settings_dialog import SettingsDialog


# --- HELPER FUNCTIONS FOR WATCHDOG ---
def is_compiled():
    """Check if running as compiled EXE (Nuitka or PyInstaller)."""
    if getattr(sys, 'frozen', False):  # PyInstaller
        return True
    try:
        from __main__ import __compiled__  # Nuitka
        return True
    except ImportError:
        return False


def process_exists(process_name):
    """Check if a process is running using tasklist."""
    try:
        cmd = f'tasklist /FI "IMAGENAME eq {process_name}" /NH'
        output = subprocess.check_output(cmd, shell=True, creationflags=0x08000000).decode()
        return process_name.lower() in output.lower()
    except Exception as e:
        AppLogger.log(f"ERROR: process_exists check failed for {process_name}: {e}")
        return False


def ensure_watchdog_running():
    """Checks if SentinelService is running, if not, launches it."""

    # Skip in script/dev mode
    if not is_compiled():
        return

    watchdog_name = "SentinelService.exe"

    # Already running? All good.
    if process_exists(watchdog_name):
        return

    # Not running - attempt revival
    AppLogger.log(f"WATCHDOG: {watchdog_name} not found. Attempting to revive...")

    base_dir = os.path.dirname(sys.executable)
    watchdog_path = os.path.join(base_dir, "SentinelService", watchdog_name)

    if not os.path.exists(watchdog_path):
        AppLogger.log(f"WATCHDOG ERROR: File not found at: {watchdog_path}")
        return

    try:
        AppLogger.log(f"WATCHDOG: Launching {watchdog_path}...")
        subprocess.Popen([watchdog_path], close_fds=True, creationflags=0x00000008)
        AppLogger.log("WATCHDOG: Launch command sent successfully.")
    except Exception as e:
        AppLogger.log(f"WATCHDOG FATAL: Failed to launch service: {e}")


# -------------------------------------

class SystemTrayController(QObject):
    def __init__(self, app):
        super().__init__()
        self.app = app

        # 1. Initialize Core Components
        self.worker = SentinelWorker()
        self.main_window = MainWindow()

        # 2. Connect Worker Signals
        self.worker.sig_status_update.connect(self.main_window.update_infrastructure)
        self.worker.sig_pc_update.connect(self.main_window.update_pc_grid)

        # 3. Menu
        self.menu = QMenu()
        self.setup_menu()

        # 4. Tray Icons
        self.trays = {
            "router": {"obj": QSystemTrayIcon(), "name": "Router", "icon_ok": QIcon(":/icons/router_ok"),
                       "icon_bad": QIcon(":/icons/router_bad")},
            "server": {"obj": QSystemTrayIcon(), "name": "Server", "icon_ok": QIcon(":/icons/server_ok"),
                       "icon_bad": QIcon(":/icons/server_bad")},
            "internet": {"obj": QSystemTrayIcon(), "name": "Internet", "icon_ok": QIcon(":/icons/net_ok"),
                         "icon_bad": QIcon(":/icons/net_bad")},
            "clients": {"obj": QSystemTrayIcon(), "name": "Active Clients", "icon_ok": None, "icon_bad": None}
        }

        # 5. Init Icons
        for key, data in self.trays.items():
            tray = data["obj"]
            tray.setContextMenu(self.menu)
            if key == "clients":
                tray.setIcon(self.generate_number_icon(0))
                tray.setToolTip("Active Clients: 0")
            else:
                tray.setIcon(data["icon_ok"])
                tray.setToolTip(f"{data['name']}: Initializing...")
            tray.show()
            tray.activated.connect(self.on_tray_icon_activated)

        # 6. Worker Signals
        self.worker.sig_status_update.connect(self.update_infrastructure_icons)
        self.worker.sig_pc_update.connect(self.update_client_count)

        # 7. Thread
        from PySide6.QtCore import QThread
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.start_monitoring)
        self.worker_thread.start()

        # 7.5. Start Remote Config API
        self.start_api_server()

        # 8. Watchdog Heartbeat (Mutual Monitoring)
        self.watchdog_timer = QTimer(self)
        self.watchdog_timer.setInterval(5000)  # Check every 5 seconds
        self.watchdog_timer.timeout.connect(self.check_watchdog_status)
        self.watchdog_timer.start()

        # Initial check (don't wait 5s)
        self.check_watchdog_status()

    def check_watchdog_status(self):
        """Periodic heartbeat to ensure watchdog is alive."""
        ensure_watchdog_running()

    def start_api_server(self):
        """Start Flask API server for remote configuration."""
        try:
            api_thread = Thread(
                target=api_server.run_api_server,
                args=('0.0.0.0', 5000),
                daemon=True  # Dies when main app exits
            )
            api_thread.start()
            AppLogger.log("✅ Remote Config API started on port 5000")
        except Exception as e:
            AppLogger.log(f"⚠️ API server failed to start: {e}")
            AppLogger.log("⚠️ App will continue without remote config capability")

    def setup_menu(self):
        self.action_settings = QAction("Settings", self.menu)
        self.action_settings.triggered.connect(self.open_settings_dialog)
        self.menu.addAction(self.action_settings)
        self.action_open = QAction("Open Monitor", self.menu)
        self.action_open.triggered.connect(self.show_window)
        self.menu.addAction(self.action_open)
        self.menu.addSeparator()
        self.action_quit = QAction("Exit Sentinel", self.menu)
        self.action_quit.triggered.connect(self.verify_quit)
        self.menu.addAction(self.action_quit)

    def update_infrastructure_icons(self, timestamp, router_ok, server_ok, internet_ok):
        def update_single(key, is_online):
            data = self.trays[key]
            tray = data["obj"]
            tray.setIcon(data["icon_ok"] if is_online else data["icon_bad"])
            status = "ONLINE" if is_online else "OFFLINE"
            tray.setToolTip(f"{data['name']}: {status}\nLast Scan: {timestamp}")

        update_single("router", router_ok)
        update_single("server", server_ok)
        update_single("internet", internet_ok)

    def update_client_count(self, pc_data_list):
        online_count = sum(1 for pc in pc_data_list if pc['is_alive'])
        total_count = len(pc_data_list)
        icon = self.generate_number_icon(online_count)
        tray = self.trays["clients"]["obj"]
        tray.setIcon(icon)
        tray.setToolTip(f"Active Clients: {online_count} / {total_count}")

    def generate_number_icon(self, number):
        size = 64
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        bg_color = QColor("#333333")
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.NoPen)
        rect = QRect(0, 0, size, size)
        painter.drawRoundedRect(rect, 15, 15)
        text_color = QColor("white")
        painter.setPen(text_color)
        font_size = 32 if number < 100 else 24
        font = QFont("Segoe UI", font_size)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, str(number))
        painter.end()
        return QIcon(pixmap)

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window()

    def show_window(self):
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()

    def verify_quit(self):
        from PySide6.QtWidgets import QInputDialog, QMessageBox, QLineEdit
        from models.security_manager import SecurityManager

        password, ok = QInputDialog.getText(None, "Security Check", "Enter Admin Password to Exit:",
                                            QLineEdit.Password)
        if ok and password:
            if SecurityManager.verify_admin(password):
                AppLogger.log("SYS: User requested shutdown with valid password.")
                self.worker.running = False
                self.worker_thread.quit()
                self.worker_thread.wait()
                self.app.quit()
            else:
                QMessageBox.warning(None, "Access Denied", "Incorrect Password!")

    def open_settings_dialog(self):
        """Open the settings dialog after admin password verification"""
        from PySide6.QtWidgets import QInputDialog, QLineEdit

        # Verify Admin Password
        password, ok = QInputDialog.getText(
            None,
            "Security Check",
            "Enter Admin Password to access Settings:",
            QLineEdit.Password
        )

        if ok and password:
            if SecurityManager.verify_admin(password):
                AppLogger.log("SETTINGS: Dialog opened with valid credentials")
                dialog = SettingsDialog()
                dialog.exec()
            else:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(None, "Access Denied", "Incorrect Admin Password!")
