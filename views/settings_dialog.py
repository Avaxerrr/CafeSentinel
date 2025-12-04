from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                               QFrame, QLabel, QPushButton, QMessageBox)
from models.config_manager import ConfigManager
from models.app_logger import AppLogger

# Import the new modular pages
from views.settings_pages.network_page import NetworkPage
from views.settings_pages.monitoring_page import MonitoringPage
from views.settings_pages.discord_page import DiscordPage

class SettingsDialog(QDialog):
    """
    Local settings configuration dialog.
    Refactored to use modular page architecture.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cfg_mgr = ConfigManager.instance()
        self.config = self.cfg_mgr.get_config()

        self.setWindowTitle("CafeSentinel - Settings")
        self.setModal(True)
        self.setMinimumSize(900, 700)

        self.setup_ui()
        self.load_values()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = self.create_header()
        layout.addWidget(header)

        # Tabs - Now just containers for our modular pages
        self.tabs = QTabWidget()

        # Instantiate the pages
        self.network_page = NetworkPage()
        self.monitoring_page = MonitoringPage()
        self.discord_page = DiscordPage()

        # Add them to tabs
        self.tabs.addTab(self.network_page, "Network")
        self.tabs.addTab(self.monitoring_page, "Monitoring")
        self.tabs.addTab(self.discord_page, "Discord")

        layout.addWidget(self.tabs)

        # Footer
        footer = self.create_footer()
        layout.addWidget(footer)

    def create_header(self):
        header = QFrame()
        header.setObjectName("DialogHeader")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 15, 20, 15)

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
        # Each page knows how to extract what it needs from the full config
        self.network_page.load_data(self.config)
        self.monitoring_page.load_data(self.config)
        self.discord_page.load_data(self.config)

    def save_settings(self):
        """Gather data from all pages, validate, and save"""
        try:
            # 1. Validation Phase
            # We check all pages before saving anything
            pages = [
                (self.network_page, "Network"),
                (self.monitoring_page, "Monitoring"),
                (self.discord_page, "Discord")
            ]

            for page, name in pages:
                is_valid, error = page.validate()
                if not is_valid:
                    QMessageBox.warning(self, "Validation Error", f"Error in {name} tab:\n{error}")
                    return

            # 2. Collection Phase
            # Start with a copy of the old config to preserve any hidden keys
            new_config = self.config.copy()

            # Merge in updates from each page
            # Note: update() is a dictionary method that merges keys
            new_config.update(self.network_page.get_data())
            new_config.update(self.monitoring_page.get_data())
            new_config.update(self.discord_page.get_data())

            # 3. Save Phase
            success, message = self.cfg_mgr.update_config(new_config)

            if success:
                QMessageBox.information(self, "Success", "Settings saved successfully!")
                AppLogger.log("SETTINGS: Configuration updated via local dialog")
                self.accept()
            else:
                QMessageBox.warning(self, "Error", f"Failed to save: {message}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unexpected error: {str(e)}")
            AppLogger.log(f"SETTINGS: Save failed - {e}")