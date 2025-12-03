from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                               QWidget, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox,
                               QPushButton, QCheckBox, QMessageBox, QComboBox,
                                QFrame, QGroupBox, QGridLayout)
from models.config_manager import ConfigManager
from models.app_logger import AppLogger


class SettingsDialog(QDialog):
    """
    Local settings configuration dialog.
    Allows on-site modification of config without using the Manager.
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

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_network_tab(), "Network")
        self.tabs.addTab(self.create_monitoring_tab(), "Monitoring")
        self.tabs.addTab(self.create_discord_tab(), "Discord")
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

    def create_network_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Targets Group
        targets_group = QGroupBox("Network Targets")
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

        targets_group.setLayout(targets_layout)
        layout.addWidget(targets_group)

        # Verification Group
        verify_group = QGroupBox("Verification Settings")
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

        verify_group.setLayout(verify_layout)
        layout.addWidget(verify_group)

        layout.addStretch()
        return widget

    def create_monitoring_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Monitor Group
        monitor_group = QGroupBox("Scan Settings")
        monitor_layout = QGridLayout()
        monitor_layout.setColumnStretch(1, 1)

        monitor_layout.addWidget(QLabel("Check Interval (sec):"), 0, 0)
        self.monitor_interval = QSpinBox()
        self.monitor_interval.setRange(1, 60)
        monitor_layout.addWidget(self.monitor_interval, 0, 1)

        monitor_layout.addWidget(QLabel("PC Subnet:"), 1, 0)
        self.pc_subnet = QLineEdit()
        self.pc_subnet.setPlaceholderText("192.168.1")
        monitor_layout.addWidget(self.pc_subnet, 1, 1)

        monitor_layout.addWidget(QLabel("PC Start Range:"), 2, 0)
        self.pc_start = QSpinBox()
        self.pc_start.setRange(1, 254)
        monitor_layout.addWidget(self.pc_start, 2, 1)

        monitor_layout.addWidget(QLabel("PC Count:"), 3, 0)
        self.pc_count = QSpinBox()
        self.pc_count.setRange(1, 100)
        monitor_layout.addWidget(self.pc_count, 3, 1)

        monitor_group.setLayout(monitor_layout)
        layout.addWidget(monitor_group)

        # Screenshot Group
        screenshot_group = QGroupBox("Screenshots")
        screenshot_layout = QGridLayout()
        screenshot_layout.setColumnStretch(1, 1)

        self.screenshot_enabled = QCheckBox("Enable Screenshots")
        screenshot_layout.addWidget(self.screenshot_enabled, 0, 0, 1, 2)

        screenshot_layout.addWidget(QLabel("Interval (min):"), 1, 0)
        self.screenshot_interval = QSpinBox()
        self.screenshot_interval.setRange(1, 1440)
        screenshot_layout.addWidget(self.screenshot_interval, 1, 1)

        screenshot_layout.addWidget(QLabel("Quality:"), 2, 0)
        self.screenshot_quality = QSpinBox()
        self.screenshot_quality.setRange(10, 100)
        screenshot_layout.addWidget(self.screenshot_quality, 2, 1)

        screenshot_layout.addWidget(QLabel("Resize Ratio:"), 3, 0)
        self.resize_ratio = QComboBox()
        self.resize_ratio.addItems(["100%", "75%", "50%"])
        screenshot_layout.addWidget(self.resize_ratio, 3, 1)

        screenshot_group.setLayout(screenshot_layout)
        layout.addWidget(screenshot_group)

        # Occupancy Group
        occupancy_group = QGroupBox("Occupancy Tracking")
        occupancy_layout = QGridLayout()
        occupancy_layout.setColumnStretch(1, 1)

        self.occupancy_enabled = QCheckBox("Enable Tracking")
        occupancy_layout.addWidget(self.occupancy_enabled, 0, 0, 1, 2)

        self.hourly_snapshot = QCheckBox("Hourly Snapshots")
        occupancy_layout.addWidget(self.hourly_snapshot, 1, 0, 1, 2)

        occupancy_layout.addWidget(QLabel("Min Session (min):"), 2, 0)
        self.min_session = QSpinBox()
        self.min_session.setRange(1, 60)
        occupancy_layout.addWidget(self.min_session, 2, 1)

        occupancy_layout.addWidget(QLabel("Batch Delay (sec):"), 3, 0)
        self.batch_delay = QSpinBox()
        self.batch_delay.setRange(1, 300)
        occupancy_layout.addWidget(self.batch_delay, 3, 1)

        occupancy_group.setLayout(occupancy_layout)
        layout.addWidget(occupancy_group)

        layout.addStretch()
        return widget

    def create_discord_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
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
        return widget

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
        """Load current config into UI fields"""
        # Targets
        targets = self.config.get('targets', {})
        self.router_ip.setText(targets.get('router', ''))
        self.server_ip.setText(targets.get('server', ''))
        self.internet_ip.setText(targets.get('internet', ''))

        # Verification
        verify = self.config.get('verification_settings', {})
        self.retry_delay.setValue(verify.get('retry_delay_seconds', 1.0))
        self.secondary_dns.setText(verify.get('secondary_target', '1.1.1.1'))
        self.min_incident.setValue(verify.get('min_incident_duration_seconds', 10))

        # Monitor
        monitor = self.config.get('monitor_settings', {})
        self.monitor_interval.setValue(monitor.get('interval_seconds', 2))
        self.pc_subnet.setText(monitor.get('pc_subnet', '192.168.1'))
        self.pc_start.setValue(monitor.get('pc_start_range', 110))
        self.pc_count.setValue(monitor.get('pc_count', 20))

        # Screenshots
        screenshot = self.config.get('screenshot_settings', {})
        self.screenshot_enabled.setChecked(screenshot.get('enabled', True))
        self.screenshot_interval.setValue(screenshot.get('interval_minutes', 60))
        self.screenshot_quality.setValue(screenshot.get('quality', 80))

        ratio_val = int(screenshot.get('resize_ratio', 1.0) * 100)
        idx = self.resize_ratio.findText(f"{ratio_val}%")
        if idx >= 0:
            self.resize_ratio.setCurrentIndex(idx)

        # Occupancy
        occupancy = self.config.get('occupancy_settings', {})
        self.occupancy_enabled.setChecked(occupancy.get('enabled', True))
        self.hourly_snapshot.setChecked(occupancy.get('hourly_snapshot_enabled', True))
        self.min_session.setValue(occupancy.get('min_session_minutes', 3))
        self.batch_delay.setValue(occupancy.get('batch_delay_seconds', 30))

        # Discord
        discord = self.config.get('discord_settings', {})
        self.discord_enabled.setChecked(discord.get('enabled', False))
        self.shop_name.setText(discord.get('shop_name', ''))
        self.webhook_alerts.setText(discord.get('webhook_alerts', ''))
        self.webhook_occupancy.setText(discord.get('webhook_occupancy', ''))
        self.webhook_screenshots.setText(discord.get('webhook_screenshots', ''))

    def save_settings(self):
        """Gather form data and save via ConfigManager"""
        try:
            # Build config dict
            new_config = self.config.copy()

            # Targets
            new_config['targets'] = {
                'router': self.router_ip.text().strip(),
                'server': self.server_ip.text().strip(),
                'internet': self.internet_ip.text().strip()
            }

            # Verification
            new_config['verification_settings'] = {
                'retry_delay_seconds': self.retry_delay.value(),
                'secondary_target': self.secondary_dns.text().strip(),
                'min_incident_duration_seconds': self.min_incident.value()
            }

            # Monitor
            new_config['monitor_settings'] = {
                'interval_seconds': self.monitor_interval.value(),
                'pc_subnet': self.pc_subnet.text().strip(),
                'pc_start_range': self.pc_start.value(),
                'pc_count': self.pc_count.value()
            }

            # Screenshots
            ratio_text = self.resize_ratio.currentText().replace('%', '')
            ratio_float = float(ratio_text) / 100.0

            new_config['screenshot_settings'] = {
                'enabled': self.screenshot_enabled.isChecked(),
                'interval_minutes': self.screenshot_interval.value(),
                'quality': self.screenshot_quality.value(),
                'resize_ratio': ratio_float
            }

            # Occupancy
            new_config['occupancy_settings'] = {
                'enabled': self.occupancy_enabled.isChecked(),
                'mode': 'session',
                'min_session_minutes': self.min_session.value(),
                'batch_delay_seconds': self.batch_delay.value(),
                'hourly_snapshot_enabled': self.hourly_snapshot.isChecked()
            }

            # Discord
            new_config['discord_settings'] = {
                'enabled': self.discord_enabled.isChecked(),
                'shop_name': self.shop_name.text().strip(),
                'webhook_alerts': self.webhook_alerts.text().strip(),
                'webhook_occupancy': self.webhook_occupancy.text().strip(),
                'webhook_screenshots': self.webhook_screenshots.text().strip()
            }

            # Save via Singleton ConfigManager
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