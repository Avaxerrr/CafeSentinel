from PySide6.QtWidgets import (QVBoxLayout, QWidget, QLabel, QLineEdit,
                               QSpinBox, QDoubleSpinBox, QGridLayout)
from views.settings_pages.base_page import BaseSettingsPage
from views.custom_widgets import CardFrame  # <-- NEW IMPORT

class NetworkPage(BaseSettingsPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # --- Targets Group (Replaced QGroupBox with CardFrame) ---
        targets_layout = QGridLayout()
        targets_layout.setColumnStretch(1, 1)

        targets_layout.addWidget(QLabel("Router IP:"), 0, 0)
        self.router_ip = QLineEdit()
        self.router_ip.setPlaceholderText("192.168.1.1")
        targets_layout.addWidget(self.router_ip, 0, 1)

        targets_layout.addWidget(QLabel("Server IP:"), 1, 0)
        self.server_ip = QLineEdit()
        self.server_ip.setPlaceholderText("192.168.1.200")
        targets_layout.addWidget(self.server_ip, 1, 1)

        targets_layout.addWidget(QLabel("Internet Test IP:"), 2, 0)
        self.internet_ip = QLineEdit()
        self.internet_ip.setPlaceholderText("8.8.8.8")
        targets_layout.addWidget(self.internet_ip, 2, 1)

        # Wrap layout in CardFrame
        targets_card = CardFrame("Network Targets", targets_layout)
        layout.addWidget(targets_card)

        # --- Verification Group (Replaced QGroupBox with CardFrame) ---
        verify_layout = QGridLayout()
        verify_layout.setColumnStretch(1, 1)

        verify_layout.addWidget(QLabel("Retry Delay (sec):"), 0, 0)
        self.retry_delay = QDoubleSpinBox()
        self.retry_delay.setRange(0.1, 10.0)
        self.retry_delay.setSingleStep(0.1)
        verify_layout.addWidget(self.retry_delay, 0, 1)

        verify_layout.addWidget(QLabel("Secondary DNS:"), 1, 0)
        self.secondary_dns = QLineEdit()
        self.secondary_dns.setPlaceholderText("1.1.1.1")
        verify_layout.addWidget(self.secondary_dns, 1, 1)

        verify_layout.addWidget(QLabel("Min Incident Duration (sec):"), 2, 0)
        self.min_incident = QSpinBox()
        self.min_incident.setRange(0, 300)
        verify_layout.addWidget(self.min_incident, 2, 1)

        # Wrap layout in CardFrame
        verify_card = CardFrame("Verification Settings", verify_layout)
        layout.addWidget(verify_card)

        layout.addStretch()

    def load_data(self, full_config: dict):
        """
        Extracts 'targets' and 'verification_settings' from the full config.
        """
        # 1. Load Targets
        targets = full_config.get('targets', {})
        self.router_ip.setText(targets.get('router', ''))
        self.server_ip.setText(targets.get('server', ''))
        self.internet_ip.setText(targets.get('internet', ''))

        # 2. Load Verification
        verify = full_config.get('verification_settings', {})
        self.retry_delay.setValue(verify.get('retry_delay_seconds', 1.0))
        self.secondary_dns.setText(verify.get('secondary_target', '1.1.1.1'))
        self.min_incident.setValue(verify.get('min_incident_duration_seconds', 10))

    def get_data(self) -> dict:
        """
        Returns a dict with two keys: 'targets' and 'verification_settings'
        """
        return {
            'targets': {
                'router': self.router_ip.text().strip(),
                'server': self.server_ip.text().strip(),
                'internet': self.internet_ip.text().strip()
            },
            'verification_settings': {
                'retry_delay_seconds': self.retry_delay.value(),
                'secondary_target': self.secondary_dns.text().strip(),
                'min_incident_duration_seconds': self.min_incident.value()
            }
        }

    def validate(self) -> tuple[bool, str]:
        # Basic empty check
        if not self.router_ip.text().strip():
            return False, "Router IP cannot be empty."
        if not self.server_ip.text().strip():
            return False, "Server IP cannot be empty."
        return True, ""
