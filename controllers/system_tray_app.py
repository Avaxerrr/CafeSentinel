from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QInputDialog, QMessageBox, QLineEdit
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QThread, QObject

from views.main_window import MainWindow
from models.sentinel_worker import SentinelWorker


class SystemTrayController(QObject):
    # --- CONFIGURATION ---
    ADMIN_PASSWORD = "Ayawsigeg-pang-hilabot!"

    def __init__(self, app):
        super().__init__()
        self.app = app

        # 1. Initialize View
        self.window = MainWindow()

        # 2. Initialize Model (Worker)
        self.thread = QThread()
        self.worker = SentinelWorker()
        self.worker.moveToThread(self.thread)

        # 3. Initialize System Tray
        self.tray_icon = QSystemTrayIcon(QIcon("icon.svg"), self.app)
        self.tray_icon.setToolTip("Cafe Sentinel - Active")

        # Tray Menu
        menu = QMenu()

        # SHOW Action
        action_show = QAction("Show Monitor", self.app)
        action_show.triggered.connect(self.show_window)

        # QUIT Action (Protected)
        action_quit = QAction("Stop & Exit", self.app)
        action_quit.triggered.connect(self.request_quit)  # Calls password check

        menu.addAction(action_show)
        menu.addSeparator()
        menu.addAction(action_quit)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

        # Double click tray to show
        self.tray_icon.activated.connect(self.on_tray_activation)

        # 4. WIRING
        self.worker.sig_status_update.connect(self.window.update_infrastructure)
        self.worker.sig_pc_update.connect(self.window.update_pc_grid)

        # 5. Start Worker
        self.thread.started.connect(self.worker.start_monitoring)
        self.thread.start()

        # Show window on startup
        self.window.show()

    def show_window(self):
        self.window.show()
        self.window.activateWindow()  # Bring to front
        self.window.raise_()

    def on_tray_activation(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window()

    def request_quit(self):
        """Prompts for password before allowing exit"""
        password, ok = QInputDialog.getText(
            None,
            "Admin Access",
            "Enter Password to Stop Monitoring:",
            QLineEdit.Password
        )

        if ok and password == self.ADMIN_PASSWORD:
            self.quit_app()
        elif ok:
            QMessageBox.warning(None, "Access Denied", "Incorrect Password!")

    def quit_app(self):
        # Clean shutdown
        self.worker.stop()
        self.thread.quit()
        self.thread.wait()

        # IMPORTANT: Tell Python to exit with Code 0 (Success)
        import sys
        sys.exit(0)
