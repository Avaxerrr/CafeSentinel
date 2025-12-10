import sys
import os
import subprocess
from threading import Thread
from dataclasses import dataclass
from typing import Optional

from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QFont, QBrush
from PySide6.QtCore import QObject, Qt, QRect, QTimer, Signal

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
    if getattr(sys, 'frozen', False):
        return True
    try:
        from __main__ import __compiled__
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
        AppLogger.log(f"process_exists check failed for {process_name}: {e}", category="ERROR")
        return False


def ensure_watchdog_running():
    """Checks if SentinelService is running, if not, launches it."""
    if not is_compiled():
        return

    watchdog_name = "SentinelService.exe"
    if process_exists(watchdog_name):
        return

    AppLogger.log(f"{watchdog_name} not found. Attempting to revive...", category="WATCHDOG")
    base_dir = os.path.dirname(sys.executable)
    watchdog_path = os.path.join(base_dir, "SentinelService", watchdog_name)

    if not os.path.exists(watchdog_path):
        AppLogger.log(f"File not found at: {watchdog_path}", category="ERROR")
        return

    try:
        AppLogger.log(f"Launching {watchdog_path}...", category="WATCHDOG")
        subprocess.Popen([watchdog_path], close_fds=True, creationflags=0x00000008)
        AppLogger.log("Launch command sent successfully.", category="WATCHDOG")
    except Exception as e:
        AppLogger.log(f"Failed to launch service: {e}", category="ERROR")


# -------------------------------------

# --- STRICT TYPE DEFINITION ---
@dataclass
class TrayItem:
    obj: QSystemTrayIcon
    name: str
    icon_ok: Optional[QIcon] = None
    icon_bad: Optional[QIcon] = None


class SystemTrayController(QObject):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.app.setQuitOnLastWindowClosed(False)
        self.env_state = False

        # 1. Initialize Core Components
        self.worker = SentinelWorker()
        self.main_window = MainWindow()

        # 2. Connect Worker Signals
        self.worker.sig_status_update.connect(self.main_window.update_infrastructure)
        self.worker.sig_pc_update.connect(self.main_window.update_pc_grid)

        # 3. Menu
        self.menu = QMenu()
        self.setup_menu()

        # 4. Tray Icons (REVERSED ORDER: Last one spawns on the Left)
        # Server (First -> Right) -> Router -> Internet -> Clients (Last -> Left)
        self.trays = {
            "server": TrayItem(
                obj=QSystemTrayIcon(),
                name="Server",
                icon_ok=QIcon(":/icons/server_white"),
                icon_bad=QIcon(":/icons/server_red")
            ),
            "router": TrayItem(
                obj=QSystemTrayIcon(),
                name="Router",
                icon_ok=QIcon(":/icons/router_white"),
                icon_bad=QIcon(":/icons/router_red")
            ),
            "internet": TrayItem(
                obj=QSystemTrayIcon(),
                name="Internet",
                icon_ok=QIcon(":/icons/internet_white"),
                icon_bad=QIcon(":/icons/internet_red")
            ),
            "clients": TrayItem(
                obj=QSystemTrayIcon(),
                name="Active Clients",
                icon_ok=None,
                icon_bad=None
            )
        }

        # 5. Init Icons
        for key, item in self.trays.items():
            # 'item' is now strictly known as a TrayItem class
            # 'item.obj' is strictly known as QSystemTrayIcon
            item.obj.setContextMenu(self.menu)

            if key == "clients":
                item.obj.setIcon(self.generate_number_icon(0))
                item.obj.setToolTip("Active Clients: 0")
            else:
                if item.icon_ok:
                    item.obj.setIcon(item.icon_ok)
                item.obj.setToolTip(f"{item.name}: Initializing...")

            item.obj.activated.connect(self.on_tray_icon_activated)

        self.apply_stealth_mode()

        # 6. Worker Signals
        self.worker.sig_status_update.connect(self.update_infrastructure_icons)
        self.worker.sig_pc_update.connect(self.update_client_count)

        # 6.5. Listen for config changes
        from models.config_manager import ConfigManager
        ConfigManager.instance().sig_config_changed.connect(self.on_config_changed)

        # 7. Thread
        from PySide6.QtCore import QThread
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.start_monitoring)
        self.worker_thread.start()

        self.start_api_server()

        # 8. Watchdog Heartbeat
        self.watchdog_timer = QTimer(self)
        self.watchdog_timer.setInterval(5000)
        self.watchdog_timer.timeout.connect(self.check_watchdog_status)
        self.watchdog_timer.start()

        self.check_watchdog_status()

    def check_watchdog_status(self):
        ensure_watchdog_running()

    def start_api_server(self):
        try:
            api_thread = Thread(
                target=api_server.run_api_server,
                args=('0.0.0.0', 5000),
                daemon=True
            )
            api_thread.start()
            AppLogger.log("Remote Config API started on port 5000", category="SYSTEM")
        except Exception as e:
            AppLogger.log(f"API server failed to start: {e}", category="ERROR")
            AppLogger.log("App will continue without remote config capability", category="SYSTEM")

    def setup_menu(self):
        menu_font = QFont("SUSE", 9)
        menu_font.setStyleStrategy(QFont.StyleStrategy.PreferQuality | QFont.StyleStrategy.PreferAntialias)
        menu_font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
        self.menu.setFont(menu_font)

        self.action_open = QAction("Open Monitor", self.menu)
        self.action_open.triggered.connect(self.show_window)
        self.menu.addAction(self.action_open)

        self.action_settings = QAction("Settings", self.menu)
        self.action_settings.triggered.connect(self.open_settings_dialog)
        self.menu.addAction(self.action_settings)

        self.menu.addSeparator()

        self.action_quit = QAction("Exit Sentinel", self.menu)
        self.action_quit.triggered.connect(self.verify_quit)
        self.menu.addAction(self.action_quit)

    def update_infrastructure_icons(self, status_dict):
        def update_single(key, is_online):
            item = self.trays[key]

            # Check if this specific tray is visible before updating tooltip/icon
            if item.obj.isVisible():
                if item.icon_ok and item.icon_bad:
                    item.obj.setIcon(item.icon_ok if is_online else item.icon_bad)
                status = "ONLINE" if is_online else "OFFLINE"
                item.obj.setToolTip(f"{item.name}: {status}\nLast Scan: {status_dict['timestamp']}")

        update_single("router", status_dict["router"])
        update_single("server", status_dict["server"])
        update_single("internet", status_dict["internet"])

    def update_client_count(self, pc_data_list):
        online_count = sum(1 for pc in pc_data_list if pc['is_alive'])
        total_count = len(pc_data_list)

        item = self.trays["clients"]
        if item.obj.isVisible():
            icon = self.generate_number_icon(online_count)
            item.obj.setIcon(icon)
            item.obj.setToolTip(f"Active Clients: {online_count} / {total_count}")

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

        font = QFont("SUSE", font_size)
        font.setWeight(QFont.Bold)
        font.setStyleStrategy(QFont.StyleStrategy.PreferQuality)
        font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)

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
                AppLogger.log("User requested shutdown with valid password.", category="SYSTEM")
                self.worker.running = False
                self.worker_thread.quit()
                self.worker_thread.wait()
                self.app.quit()
            else:
                QMessageBox.warning(None, "Access Denied", "Incorrect Password!")

    def open_settings_dialog(self):
        from PySide6.QtWidgets import QInputDialog, QLineEdit

        password, ok = QInputDialog.getText(
            None,
            "Security Check",
            "Enter Admin Password to access Settings:",
            QLineEdit.Password
        )
        if ok and password:
            if SecurityManager.verify_admin(password):
                AppLogger.log("Dialog opened with valid credentials", category="SETTINGS")
                dialog = SettingsDialog()
                dialog.exec()
            else:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(None, "Access Denied", "Incorrect Admin Password!")

    def apply_stealth_mode(self, config=None):
        if config is None:
            from models.config_manager import ConfigManager
            config = ConfigManager.instance().get_config()

        retention_days = config.get("system_settings", {}).get("log_retention_days", 30)

        AppLogger.initialize()
        AppLogger.cleanup_old_logs(retention_days)

        self.env_state = config.get("system_settings", {}).get("env_state", False)

        # New: Get visibility dictionary (default to True if not present)
        visibility = config.get("system_settings", {}).get("tray_visibility", {})

        if self.env_state:
            AppLogger.log("Entering Stealth Mode. ALL Tray icons hidden.", category="STEALTH")
            for key, item in self.trays.items():
                item.obj.hide()
        else:
            AppLogger.log("Exiting Stealth Mode. Applying icon visibility settings.", category="STEALTH")
            for key, item in self.trays.items():
                # Check individual preference. Default to True if key missing.
                should_show = visibility.get(key, True)

                if should_show:
                    item.obj.show()
                else:
                    item.obj.hide()

    def on_config_changed(self, new_config):
        """
        Triggered when config is updated.
        We just re-run apply_stealth_mode, which now handles both global stealth and individual toggles.
        """
        AppLogger.log("Config changed. Re-applying tray visibility settings.", category="SYSTEM")
        self.apply_stealth_mode(config=new_config)
