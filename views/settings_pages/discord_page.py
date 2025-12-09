from PySide6.QtWidgets import QVBoxLayout, QWidget, QLabel, QLineEdit
from views.settings_pages.base_page import BaseSettingsPage
from views.custom_widgets import ToggleSwitch, CardFrame

class DiscordPage(BaseSettingsPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # --- Discord Notifications Card ---
        discord_card = CardFrame("Discord Notifications")

        # Toggle at top
        self.discord_enabled = ToggleSwitch("Enable Notifications")
        self.discord_enabled.setToolTip("Send alerts to your Discord server.")
        discord_card.add_full_width(self.discord_enabled)

        self.shop_name = QLineEdit()
        self.shop_name.setPlaceholderText("Respawn Gaming")
        discord_card.add_row(
            "Shop Name",
            self.shop_name,
            "The name that appears at the bottom of every Discord alert.",
            stretch_input=True
        )

        self.webhook_alerts = QLineEdit()
        self.webhook_alerts.setPlaceholderText("https://discord.com/api/webhooks/...")
        discord_card.add_row(
            "Alerts Webhook",
            self.webhook_alerts,
            "Paste Discord Webhook URL here for Urgent Alerts\n(Internet Down, Server Offline).",
            stretch_input=True
        )

        self.webhook_occupancy = QLineEdit()
        self.webhook_occupancy.setPlaceholderText("https://discord.com/api/webhooks/...")
        discord_card.add_row(
            "Occupancy Webhook",
            self.webhook_occupancy,
            "Paste Discord Webhook URL here for PC Usage logs\n(PC 1 Online, Hourly Reports).",
            stretch_input=True
        )

        self.webhook_screenshots = QLineEdit()
        self.webhook_screenshots.setPlaceholderText("https://discord.com/api/webhooks/...")
        discord_card.add_row(
            "Screenshots Webhook",
            self.webhook_screenshots,
            "Paste Discord Webhook URL here for Screenshot uploads.",
            stretch_input=True
        )

        layout.addWidget(discord_card)
        layout.addStretch()

    def load_data(self, full_config: dict):
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
        if self.discord_enabled.isChecked():
            if not self.shop_name.text().strip():
                return False, "Shop Name is required when Discord is enabled."
        return True, ""