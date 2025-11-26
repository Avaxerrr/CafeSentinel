from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QInputDialog, QMessageBox, QLineEdit
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QThread, QObject

from utils.resource_manager import ResourceManager
from views.main_window import MainWindow
from models.sentinel_worker import SentinelWorker
from models.security_manager import SecurityManager


class SystemTrayController(QObject):
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
        # Use bundled resource for icon (embedded in EXE)
        icon_path = ResourceManager.get_resource_path("icon.svg")
        self.tray_icon = QSystemTrayIcon(QIcon(icon_path), self.app)
        self.tray_icon.setToolTip("Cafe Sentinel - Active")

        # Tray Menu
        menu = QMenu()

        # SHOW Action
        action_show = QAction("Show Monitor", self.app)
        action_show.triggered.connect(self.show_window)

        # QUIT Action (Password Protected)
        action_quit = QAction("Stop / Exit", self.app)
        action_quit.triggered.connect(self.request_quit)

        menu.addAction(action_show)
        menu.addSeparator()
        menu.addAction(action_quit)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

        # 4. Connect Worker Signals to Window Slots
        self.worker.sig_status_update.connect(self.window.update_infrastructure)
        self.worker.sig_pc_update.connect(self.window.update_pc_grid)

        # 5. Start Worker
        # Use start_monitoring() not run()
        self.thread.started.connect(self.worker.start_monitoring)
        self.thread.start()

        # Show window on startup
        self.window.show()

    def show_window(self):
        """Show the main monitoring window."""
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def request_quit(self):
        """
        Dual-Password Logic:
        - If Admin Password: Quit the app normally
        - If Privacy Password: Silently toggle privacy mode (no feedback)
        - If Wrong: Do nothing (dialog closes silently)
        """
        password, ok = QInputDialog.getText(
            None,
            "Authentication Required",
            "Enter Password:",
            QLineEdit.Password
        )

        if not ok or not password:
            return  # User cancelled

        # Check Admin Password (Quits the app)
        if SecurityManager.verify_admin(password):
            self.shutdown()
            return

        # Check Privacy Password (Toggle screenshot mode silently)
        if SecurityManager.verify_privacy(password):
            # Toggle privacy mode in the worker
            current_state = self.worker.privacy_mode
            self.worker.privacy_mode = not current_state

            # Silent operation - no message box, dialog just closes
            # The user sees nothing, but privacy mode has been toggled
            return

        # Wrong password - do nothing (dialog closes, no feedback)
        # This makes it look like you "tried to quit but failed"

    def shutdown(self):
        """Clean shutdown of the application."""
        # Stop the worker
        self.worker.running = False
        self.thread.quit()
        self.thread.wait()

        # Hide tray icon
        self.tray_icon.hide()

        # Exit cleanly (Exit code 0 tells the watchdog NOT to restart)
        self.app.exit(0)
