from PySide6.QtWidgets import QVBoxLayout, QWidget, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox
from views.settings_pages.base_page import BaseSettingsPage
from views.custom_widgets import CardFrame


class NetworkPage(BaseSettingsPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # --- Network Targets Card ---
        targets_card = CardFrame("Network Targets")

        self.router_ip = QLineEdit()
        self.router_ip.setPlaceholderText("192.168.0.1")
        targets_card.add_row(
            "Router IP",
            self.router_ip,
            "The IP address of your main internet router.\nUsually ends in .1 or .254.",
            stretch_input=True
        )

        self.server_ip = QLineEdit()
        self.server_ip.setPlaceholderText("192.168.0.100")
        targets_card.add_row(
            "Server IP",
            self.server_ip,
            "The IP address of your game server or timer PC.\nWe ping this to check if the local network is working.",
            stretch_input=True
        )

        self.internet_ip = QLineEdit()
        self.internet_ip.setPlaceholderText("8.8.8.8")
        targets_card.add_row(
            "Internet IP",
            self.internet_ip,
            "A reliable website IP (like Google: 8.8.8.8).\nWe ping this to see if the shop has internet access.",
            stretch_input=True
        )

        layout.addWidget(targets_card)

        # --- Verification Settings Card ---
        verification_card = CardFrame("Verification Settings")

        self.retry_delay = QDoubleSpinBox()
        self.retry_delay.setRange(0.1, 10.0)
        self.retry_delay.setSingleStep(0.1)
        self.retry_delay.setSuffix(" sec")
        verification_card.add_row(
            "Retry Delay",
            self.retry_delay,
            "Wait this long before double-checking a failed ping.\nHelps prevent false alarms."
        )

        self.secondary_dns = QLineEdit()
        self.secondary_dns.setPlaceholderText("1.1.1.1")
        verification_card.add_row(
            "Secondary DNS",
            self.secondary_dns,
            "A backup website to check (like Cloudflare: 1.1.1.1).\nUsed to confirm if the internet is really down."
        )

        self.min_incident_duration = QSpinBox()
        self.min_incident_duration.setRange(0, 300)
        self.min_incident_duration.setSuffix(" sec")
        verification_card.add_row(
            "Min Incident Duration",
            self.min_incident_duration,
            "Ignore internet drops shorter than this.\nUseful if your internet flickers often."
        )

        layout.addWidget(verification_card)
        layout.addStretch()

    def load_data(self, full_config: dict):
        # Network Targets
        targets = full_config.get('targets', {})
        self.router_ip.setText(targets.get('router', ''))
        self.server_ip.setText(targets.get('server', ''))
        self.internet_ip.setText(targets.get('internet', ''))

        # Verification
        verification = full_config.get('verification_settings', {})
        self.retry_delay.setValue(verification.get('retry_delay_seconds', 1.0))
        self.secondary_dns.setText(verification.get('secondary_target', '1.1.1.1'))
        self.min_incident_duration.setValue(verification.get('min_incident_duration_seconds', 10))

    def get_data(self) -> dict:
        return {
            'targets': {
                'router': self.router_ip.text().strip(),
                'server': self.server_ip.text().strip(),
                'internet': self.internet_ip.text().strip()
            },
            'verification_settings': {
                'retry_delay_seconds': self.retry_delay.value(),
                'secondary_target': self.secondary_dns.text().strip(),
                'min_incident_duration_seconds': self.min_incident_duration.value()
            }
        }

    def validate(self) -> tuple[bool, str]:
        # Basic IP validation
        for field, name in [(self.router_ip, "Router IP"),
                            (self.server_ip, "Server IP"),
                            (self.internet_ip, "Internet IP")]:
            if not field.text().strip():
                return False, f"{name} cannot be empty."
        return True, ""
