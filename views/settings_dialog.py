from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
                               QStackedWidget, QFrame, QLabel, QPushButton,
                               QMessageBox, QListWidgetItem, QScrollArea, QWidget)
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize, Qt
from models.config_manager import ConfigManager
from models.app_logger import AppLogger

# Try to import resources, pass if fails
try:
    import resources_rc
except ImportError:
    pass

# Import the modular pages
from views.settings_pages.network_page import NetworkPage
from views.settings_pages.monitoring_page import MonitoringPage
from views.settings_pages.discord_page import DiscordPage
from views.settings_pages.system_page import SystemPage

class SettingsDialog(QDialog):
    """
    Local settings configuration dialog.
    Features: Sidebar Navigation, Scrollable Content, External CSS support.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cfg_mgr = ConfigManager.instance()
        self.config = self.cfg_mgr.get_config()

        self.setWindowTitle("CafeSentinel - Settings")
        self.setModal(True)
        self.setMinimumSize(800, 400)

        self.setup_ui()
        self.load_values()

    def setup_ui(self):
        # Main Layout (Vertical: Header -> Body -> Footer)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Header
        main_layout.addWidget(self.create_header())

        # 2. Body (Horizontal: Sidebar | Content)
        body_frame = QFrame()
        body_frame.setObjectName("SettingsBodyFrame")
        body_layout = QHBoxLayout(body_frame)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # --- Left Sidebar ---
        self.sidebar = QListWidget()
        self.sidebar.setObjectName("SettingsSidebar")
        self.sidebar.setFixedWidth(200)
        self.sidebar.setFrameShape(QFrame.NoFrame)
        self.sidebar.setIconSize(QSize(24, 24))
        self.sidebar.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Add Navigation Items
        self.add_nav_item("Network", ":/icons/nav_network")
        self.add_nav_item("Monitoring", ":/icons/nav_monitoring")
        self.add_nav_item("Discord", ":/icons/nav_discord")
        self.add_nav_item("System Settings", ":/icons/nav_system")


        # --- Right Content Stack ---
        self.pages_stack = QStackedWidget()
        self.pages_stack.setObjectName("SettingsContentStack")

        # Instantiate Pages
        self.network_page = NetworkPage()
        self.monitoring_page = MonitoringPage()
        self.discord_page = DiscordPage()
        self.system_page = SystemPage()

        # Add pages wrapped in ScrollAreas
        self.pages_stack.addWidget(self.create_scroll_wrapper(self.network_page))
        self.pages_stack.addWidget(self.create_scroll_wrapper(self.monitoring_page))
        self.pages_stack.addWidget(self.create_scroll_wrapper(self.discord_page))
        self.pages_stack.addWidget(self.create_scroll_wrapper(self.system_page))

        # Wiring: Sidebar Click -> Switch Page
        self.sidebar.currentRowChanged.connect(self.pages_stack.setCurrentIndex)

        # Add to Body Layout
        body_layout.addWidget(self.sidebar)
        body_layout.addWidget(self.pages_stack)

        main_layout.addWidget(body_frame)

        # 3. Footer
        main_layout.addWidget(self.create_footer())

        # Select first item by default
        self.sidebar.setCurrentRow(0)

    def create_scroll_wrapper(self, widget: QWidget) -> QScrollArea:
        """Wraps a settings page in a QScrollArea to prevent cramping."""
        scroll = QScrollArea()
        scroll.setObjectName("SettingsScrollArea")
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        return scroll

    def add_nav_item(self, name, icon_path):
        item = QListWidgetItem(name)
        icon = QIcon(icon_path)
        if not icon.isNull():
            item.setIcon(icon)
        self.sidebar.addItem(item)

    def create_header(self):
        header = QFrame()
        header.setObjectName("DialogHeader")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(25, 20, 25, 20)

        title = QLabel("Configuration Settings")
        title.setObjectName("DialogTitle")
        layout.addWidget(title)
        layout.addStretch()
        return header

    def create_footer(self):
        footer = QFrame()
        footer.setObjectName("DialogFooter")
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(20, 15, 20, 15)

        layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("SecondaryButton")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save Changes")
        save_btn.setObjectName("PrimaryButton")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)

        return footer

    def load_values(self):
        """Distribute config data to child pages"""
        self.network_page.load_data(self.config)
        self.monitoring_page.load_data(self.config)
        self.discord_page.load_data(self.config)
        self.system_page.load_data(self.config)

    def save_settings(self):
        """Gather data from all pages, validate, and save"""
        try:
            # 1. Validation Phase
            pages = [
                (self.network_page, "Network"),
                (self.monitoring_page, "Monitoring"),
                (self.discord_page, "Discord"),
                (self.system_page, "System")
            ]

            for page, name in pages:
                is_valid, error = page.validate()
                if not is_valid:
                    idx = pages.index((page, name))
                    self.sidebar.setCurrentRow(idx)
                    QMessageBox.warning(self, "Validation Error", f"Error in {name} settings:\n{error}")
                    return

            # 2. Collection Phase
            new_config = self.config.copy()
            new_config.update(self.network_page.get_data())
            new_config.update(self.monitoring_page.get_data())
            new_config.update(self.discord_page.get_data())
            new_config.update(self.system_page.get_data())

            # 3. Save Phase
            success, message = self.cfg_mgr.update_config(new_config)

            if success:
                QMessageBox.information(self, "Success", "Settings saved successfully!")
                AppLogger.log("Configuration updated via local dialog", category="SETTINGS")
                self.accept()
            else:
                QMessageBox.warning(self, "Error", f"Failed to save: {message}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unexpected error: {str(e)}")
            AppLogger.log(f"Save failed - {e}", category="SETTINGS")