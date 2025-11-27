import sys
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QFont, QBrush
from PySide6.QtCore import QObject, Qt, QRect

# Ensure this matches your file name for the compiled resources
import resources_rc

from views.main_window import MainWindow
from models.sentinel_worker import SentinelWorker


class SystemTrayController(QObject):
    def __init__(self, app):
        super().__init__()
        self.app = app

        # 1. Initialize Core Components
        self.worker = SentinelWorker()
        self.main_window = MainWindow()

        # 2. Connect Worker Signals to Main Window (GUI)
        self.worker.sig_status_update.connect(self.main_window.update_infrastructure)
        self.worker.sig_pc_update.connect(self.main_window.update_pc_grid)

        # 3. Create the Shared Context Menu
        self.menu = QMenu()
        self.setup_menu()

        # 4. Define the 4 Tray Icons
        self.trays = {
            "router": {
                "obj": QSystemTrayIcon(),
                "name": "Router",
                "icon_ok": QIcon(":/icons/router_ok"),
                "icon_bad": QIcon(":/icons/router_bad")
            },
            "server": {
                "obj": QSystemTrayIcon(),
                "name": "Server",
                "icon_ok": QIcon(":/icons/server_ok"),
                "icon_bad": QIcon(":/icons/server_bad")
            },
            "internet": {
                "obj": QSystemTrayIcon(),
                "name": "Internet",
                "icon_ok": QIcon(":/icons/net_ok"),
                "icon_bad": QIcon(":/icons/net_bad")
            },
            # NEW: Client Counter
            "clients": {
                "obj": QSystemTrayIcon(),
                "name": "Active Clients",
                "icon_ok": None,  # Generated dynamically
                "icon_bad": None
            }
        }

        # 5. Initialize Icons
        for key, data in self.trays.items():
            tray = data["obj"]
            tray.setContextMenu(self.menu)

            # Special handling for the Client counter (Start at 0)
            if key == "clients":
                tray.setIcon(self.generate_number_icon(0))
                tray.setToolTip("Active Clients: 0")
            else:
                tray.setIcon(data["icon_ok"])
                tray.setToolTip(f"{data['name']}: Initializing...")

            tray.show()
            tray.activated.connect(self.on_tray_icon_activated)

        # 6. Connect Worker Signals to Tray Logic
        self.worker.sig_status_update.connect(self.update_infrastructure_icons)
        self.worker.sig_pc_update.connect(self.update_client_count)  # NEW SIGNAL

        # 7. Start the Worker Thread
        from PySide6.QtCore import QThread
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.start_monitoring)
        self.worker_thread.start()

    def setup_menu(self):
        self.action_open = QAction("Open Monitor", self.menu)
        self.action_open.triggered.connect(self.show_window)
        self.menu.addAction(self.action_open)

        self.menu.addSeparator()

        self.action_quit = QAction("Exit Sentinel", self.menu)
        self.action_quit.triggered.connect(self.verify_quit)
        self.menu.addAction(self.action_quit)

    # --- INFRASTRUCTURE UPDATER ---
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

    # --- NEW: CLIENT COUNT UPDATER ---
    def update_client_count(self, pc_data_list):
        """
        Receives list of dicts: [{'name': 'PC-1', 'is_alive': True}, ...]
        Calculates count and draws the number icon.
        """
        # 1. Calculate Count
        online_count = sum(1 for pc in pc_data_list if pc['is_alive'])
        total_count = len(pc_data_list)

        # 2. Generate Icon
        icon = self.generate_number_icon(online_count)

        # 3. Update Tray
        tray = self.trays["clients"]["obj"]
        tray.setIcon(icon)
        tray.setToolTip(f"Active Clients: {online_count} / {total_count}")

    def generate_number_icon(self, number):
        """
        Draws a dark rounded box with the white number inside.
        """
        # Create a blank transparent image (64x64 is good for high DPI)
        size = 64
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. Draw Background (Dark Grey Rounded Rect)
        # This ensures visibility on both Light and Dark Windows themes
        bg_color = QColor("#333333")
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.NoPen)

        # Draw a box that fills most of the icon
        rect = QRect(0, 0, size, size)
        painter.drawRoundedRect(rect, 15, 15)  # 15 is corner radius

        # 2. Draw Text (White Number)
        text_color = QColor("white")
        painter.setPen(text_color)

        # Dynamic font size based on digits
        font_size = 32 if number < 100 else 24
        font = QFont("Segoe UI", font_size)
        font.setBold(True)
        painter.setFont(font)

        # Align text in the center
        painter.drawText(rect, Qt.AlignCenter, str(number))

        painter.end()
        return QIcon(pixmap)

    # --- UTILS ---
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

        password, ok = QInputDialog.getText(
            None, "Security Check", "Enter Admin Password to Exit:",
            QLineEdit.Password
        )

        if ok and password:
            if SecurityManager.verify_admin(password):
                self.worker.running = False
                self.worker_thread.quit()
                self.worker_thread.wait()
                self.app.quit()
            else:
                QMessageBox.warning(None, "Access Denied", "Incorrect Password!")
