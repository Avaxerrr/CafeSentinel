from PySide6.QtWidgets import (QVBoxLayout, QWidget, QLabel, QLineEdit,
                               QGroupBox, QGridLayout, QCheckBox)
from views.settings_pages.base_page import BaseSettingsPage

class DiscordPage(BaseSettingsPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        discord_group = QGroupBox("Discord Notifications")
        discord_layout = QGridLayout()
        discord_layout.setColumnStretch(1, 1)

        self.discord_enabled = QCheckBox("Enable Discord Notifications")
        discord_layout.addWidget(self.discord_enabled, 0, 0, 1, 2)

        discord_layout.addWidget(QLabel("Shop Name:"), 1, 0)
        self.shop_name = QLineEdit()
        discord_layout.addWidget(self.shop_name, 1, 1)

        discord_layout.addWidget(QLabel("Alerts Webhook:"), 2, 0)
        self.webhook_alerts = QLineEdit()
        self.webhook_alerts.setPlaceholderText("https://discord.com/api/webhooks/...")
        discord_layout.addWidget(self.webhook_alerts, 2, 1)

        discord_layout.addWidget(QLabel("Occupancy Webhook:"), 3, 0)
        self.webhook_occupancy = QLineEdit()
        self.webhook_occupancy.setPlaceholderText("https://discord.com/api/webhooks/...")
        discord_layout.addWidget(self.webhook_occupancy, 3, 1)

        discord_layout.addWidget(QLabel("Screenshots Webhook:"), 4, 0)
        self.webhook_screenshots = QLineEdit()
        self.webhook_screenshots.setPlaceholderText("https://discord.com/api/webhooks/...")
        discord_layout.addWidget(self.webhook_screenshots, 4, 1)

        discord_group.setLayout(discord_layout)
        layout.addWidget(discord_group)

        layout.addStretch()

    def load_data(self, full_config: dict):
        # Load Discord Settings
        discord = full_config.get('discord_settings', {})
        self.discord_enabled.setChecked(discord.get('enabled', False))
        self.shop_name.setText(discord.get('shop_name', ''))
        self.webhook_alerts.setText(discord.get('webhook_alerts', ''))
        self.webhook_occupancy.setText(discord.get('webhook_occupancy', ''))
        self.webhook_screenshots.setText(discord.get('webhook_screenshots', ''))

    def get_data(self) -> dict:
        return {
            'discord_settings': {
                'enabled': self.discord_enabled.isChecked(),
                'shop_name': self.shop_name.text().strip(),
                'webhook_alerts': self.webhook_alerts.text().strip(),
                'webhook_occupancy': self.webhook_occupancy.text().strip(),
                'webhook_screenshots': self.webhook_screenshots.text().strip()
            }
        }

    def validate(self) -> tuple[bool, str]:
        # If enabled, at least one webhook should probably be present,
        # but we won't force it strictly to avoid annoyance.
        # We can add logic here if needed.
        return True, ""