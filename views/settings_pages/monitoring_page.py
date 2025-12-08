from PySide6.QtWidgets import (QVBoxLayout, QWidget, QLabel, QLineEdit,
                               QSpinBox, QGridLayout)
from views.settings_pages.base_page import BaseSettingsPage
from views.custom_widgets import ToggleSwitch, CardFrame

class MonitoringPage(BaseSettingsPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # --- Monitor Group (CardFrame) ---
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

        # Wrap in CardFrame
        monitor_card = CardFrame("Scan Settings", monitor_layout)
        layout.addWidget(monitor_card)

        # --- Screenshot Group (CardFrame + ToggleSwitch) ---
        screenshot_layout = QGridLayout()
        screenshot_layout.setColumnStretch(1, 1)

        # Updated: ToggleSwitch
        self.screenshot_enabled = ToggleSwitch("Enable Screenshots")
        screenshot_layout.addWidget(self.screenshot_enabled, 0, 0, 1, 2)

        screenshot_layout.addWidget(QLabel("Interval (min):"), 1, 0)
        self.screenshot_interval = QSpinBox()
        self.screenshot_interval.setRange(1, 1440)
        screenshot_layout.addWidget(self.screenshot_interval, 1, 1)

        screenshot_layout.addWidget(QLabel("Quality:"), 2, 0)
        self.screenshot_quality = QSpinBox()
        self.screenshot_quality.setRange(10, 100)
        self.screenshot_quality.setSuffix("%")
        screenshot_layout.addWidget(self.screenshot_quality, 2, 1)

        screenshot_layout.addWidget(QLabel("Resize Ratio (%):"), 3, 0)
        self.resize_ratio = QSpinBox()
        self.resize_ratio.setRange(10, 100)
        self.resize_ratio.setSingleStep(5)
        self.resize_ratio.setSuffix("%")
        screenshot_layout.addWidget(self.resize_ratio, 3, 1)

        # Wrap in CardFrame
        screenshot_card = CardFrame("Screenshots", screenshot_layout)
        layout.addWidget(screenshot_card)

        # --- Occupancy Group (CardFrame + ToggleSwitch) ---
        occupancy_layout = QGridLayout()
        occupancy_layout.setColumnStretch(1, 1)

        # Updated: ToggleSwitch
        self.occupancy_enabled = ToggleSwitch("Enable Tracking")
        occupancy_layout.addWidget(self.occupancy_enabled, 0, 0, 1, 2)

        # Updated: ToggleSwitch
        self.hourly_snapshot = ToggleSwitch("Hourly Snapshots")
        occupancy_layout.addWidget(self.hourly_snapshot, 1, 0, 1, 2)

        occupancy_layout.addWidget(QLabel("Min Session (min):"), 2, 0)
        self.min_session = QSpinBox()
        self.min_session.setRange(1, 60)
        occupancy_layout.addWidget(self.min_session, 2, 1)

        occupancy_layout.addWidget(QLabel("Batch Delay (sec):"), 3, 0)
        self.batch_delay = QSpinBox()
        self.batch_delay.setRange(1, 300)
        occupancy_layout.addWidget(self.batch_delay, 3, 1)

        # Wrap in CardFrame
        occupancy_card = CardFrame("Occupancy Tracking", occupancy_layout)
        layout.addWidget(occupancy_card)

        # --- System Settings Group (CardFrame + ToggleSwitch) ---
        system_layout = QGridLayout()
        system_layout.setColumnStretch(1, 1)

        # Updated: ToggleSwitch
        self.env_state = ToggleSwitch("Enable Stealth Mode (Hide Tray Icons)")
        self.env_state.setToolTip("Runs app invisibly. Only accessible via Manager or Magic Hotkey.")
        system_layout.addWidget(self.env_state, 0, 0, 1, 2)

        # Wrap in CardFrame
        system_card = CardFrame("System Settings", system_layout)
        layout.addWidget(system_card)

        layout.addStretch()

    def load_data(self, full_config: dict):
        # 1. Monitor Settings
        monitor = full_config.get('monitor_settings', {})
        self.monitor_interval.setValue(monitor.get('interval_seconds', 2))
        self.pc_subnet.setText(monitor.get('pc_subnet', '192.168.1'))
        self.pc_start.setValue(monitor.get('pc_start_range', 110))
        self.pc_count.setValue(monitor.get('pc_count', 20))

        # 2. Screenshot Settings
        screenshot = full_config.get('screenshot_settings', {})
        self.screenshot_enabled.setChecked(screenshot.get('enabled', True))
        self.screenshot_interval.setValue(screenshot.get('interval_minutes', 60))
        self.screenshot_quality.setValue(screenshot.get('quality', 80))

        # Config has 0.75 -> Convert to 75
        ratio_val = int(screenshot.get('resize_ratio', 1.0) * 100)
        self.resize_ratio.setValue(ratio_val)

        # 3. Occupancy Settings
        occupancy = full_config.get('occupancy_settings', {})
        self.occupancy_enabled.setChecked(occupancy.get('enabled', True))
        self.hourly_snapshot.setChecked(occupancy.get('hourly_snapshot_enabled', True))
        self.min_session.setValue(occupancy.get('min_session_minutes', 3))
        self.batch_delay.setValue(occupancy.get('batch_delay_seconds', 30))

        # 4. System Settings
        sys_settings = full_config.get("system_settings", {})
        self.env_state.setChecked(sys_settings.get("env_state", False))

    def get_data(self) -> dict:
        # User enters 75 -> Return 0.75
        ratio_float = self.resize_ratio.value() / 100.0

        return {
            'monitor_settings': {
                'interval_seconds': self.monitor_interval.value(),
                'pc_subnet': self.pc_subnet.text().strip(),
                'pc_start_range': self.pc_start.value(),
                'pc_count': self.pc_count.value()
            },
            'screenshot_settings': {
                'enabled': self.screenshot_enabled.isChecked(),
                'interval_minutes': self.screenshot_interval.value(),
                'quality': self.screenshot_quality.value(),
                'resize_ratio': ratio_float
            },
            'occupancy_settings': {
                'enabled': self.occupancy_enabled.isChecked(),
                'mode': 'session',
                'min_session_minutes': self.min_session.value(),
                'batch_delay_seconds': self.batch_delay.value(),
                'hourly_snapshot_enabled': self.hourly_snapshot.isChecked()
            },
            'system_settings': {
                "env_state": self.env_state.isChecked()
            }
        }

    def validate(self) -> tuple[bool, str]:
        subnet = self.pc_subnet.text().strip()
        if not subnet:
            return False, "PC Subnet cannot be empty."
        return True, ""