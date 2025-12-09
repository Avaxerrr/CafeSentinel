from PySide6.QtWidgets import (QVBoxLayout, QWidget, QLabel, QLineEdit,
                               QSpinBox, QHBoxLayout)
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

        # --- Scan Settings Card ---
        monitor_card = CardFrame("Scan Settings")

        self.monitor_interval = QSpinBox()
        self.monitor_interval.setRange(1, 60)
        self.monitor_interval.setSuffix(" sec")
        monitor_card.add_row(
            "Check Interval",
            self.monitor_interval,
            "How often to check connection status.\nLower is faster but uses more network traffic."
        )

        self.pc_subnet = QLineEdit()
        self.pc_subnet.setPlaceholderText("192.168.1")
        monitor_card.add_row(
            "PC Subnet",
            self.pc_subnet,
            "The first 3 parts of your Client PC IP addresses.\nExample: If PC is 192.168.1.10, enter '192.168.1'."
        )

        self.pc_start = QSpinBox()
        self.pc_start.setRange(1, 254)
        monitor_card.add_row(
            "PC Start Range",
            self.pc_start,
            "The last number of the first PC IP.\nExample: If first PC is 192.168.1.10, enter 10."
        )

        self.pc_count = QSpinBox()
        self.pc_count.setRange(1, 100)
        monitor_card.add_row(
            "PC Count",
            self.pc_count,
            "How many PCs to scan starting from the Start Range."
        )

        layout.addWidget(monitor_card)

        # --- Screenshot Settings Card ---
        screenshot_card = CardFrame("Screenshots")

        # Toggle at top
        self.screenshot_enabled = ToggleSwitch("Enable Screenshots")
        self.screenshot_enabled.setToolTip("Turn on/off automatic screen capture of the Timer PC.")
        screenshot_card.add_full_width(self.screenshot_enabled)

        self.screenshot_interval = QSpinBox()
        self.screenshot_interval.setRange(1, 1440)
        self.screenshot_interval.setSuffix(" min")
        screenshot_card.add_row(
            "Interval",
            self.screenshot_interval,
            "How many minutes to wait between each screenshot."
        )

        self.screenshot_quality = QSpinBox()
        self.screenshot_quality.setRange(10, 100)
        self.screenshot_quality.setSuffix("%")
        screenshot_card.add_row(
            "Quality",
            self.screenshot_quality,
            "Image clarity (10-100).\nLower quality = smaller file size."
        )

        self.resize_ratio = QSpinBox()
        self.resize_ratio.setRange(10, 100)
        self.resize_ratio.setSingleStep(5)
        self.resize_ratio.setSuffix("%")
        screenshot_card.add_row(
            "Resize Ratio",
            self.resize_ratio,
            "Shrink images to save space and upload faster.\n50% is usually readable enough."
        )

        layout.addWidget(screenshot_card)

        # --- Occupancy Tracking Card ---
        occupancy_card = CardFrame("Occupancy Tracking")

        # Toggles at top
        toggles_container = QWidget()
        toggles_layout = QHBoxLayout(toggles_container)
        toggles_layout.setContentsMargins(0, 0, 0, 0)
        toggles_layout.setSpacing(20)

        self.occupancy_enabled = ToggleSwitch("Enable Tracking")
        self.occupancy_enabled.setToolTip("Monitor which PCs are currently being used.")
        toggles_layout.addWidget(self.occupancy_enabled)

        self.hourly_snapshot = ToggleSwitch("Hourly Snapshots")
        self.hourly_snapshot.setToolTip("Send a summary of occupied PCs every hour to Discord.")
        toggles_layout.addWidget(self.hourly_snapshot)

        toggles_layout.addStretch()
        occupancy_card.add_full_width(toggles_container)

        self.min_session = QSpinBox()
        self.min_session.setRange(1, 60)
        self.min_session.setSuffix(" min")
        occupancy_card.add_row(
            "Min Session",
            self.min_session,
            "Ignore PC usage shorter than this time.\nFilters out quick restarts."
        )

        self.batch_delay = QSpinBox()
        self.batch_delay.setRange(1, 300)
        self.batch_delay.setSuffix(" sec")
        occupancy_card.add_row(
            "Batch Delay",
            self.batch_delay,
            "Wait this long before sending 'PC Online' alerts.\nGroups multiple startups into one message."
        )

        layout.addWidget(occupancy_card)

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

        ratio_val = int(screenshot.get('resize_ratio', 1.0) * 100)
        self.resize_ratio.setValue(ratio_val)

        # 3. Occupancy Settings
        occupancy = full_config.get('occupancy_settings', {})
        self.occupancy_enabled.setChecked(occupancy.get('enabled', True))
        self.hourly_snapshot.setChecked(occupancy.get('hourly_snapshot_enabled', True))
        self.min_session.setValue(occupancy.get('min_session_minutes', 3))
        self.batch_delay.setValue(occupancy.get('batch_delay_seconds', 30))

    def get_data(self) -> dict:
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
            }
        }

    def validate(self) -> tuple[bool, str]:
        subnet = self.pc_subnet.text().strip()
        if not subnet:
            return False, "PC Subnet cannot be empty."
        return True, ""