from PySide6.QtWidgets import QVBoxLayout, QSpinBox
from views.settings_pages.base_page import BaseSettingsPage
from views.custom_widgets import ToggleSwitch, CardFrame


class SystemPage(BaseSettingsPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # --- System Behavior Card ---
        system_card = CardFrame("Application Behavior")

        # Stealth Mode
        self.env_state = ToggleSwitch("Enable Stealth Mode (Hide Tray Icons)")
        self.env_state.setToolTip("Runs app invisibly. Only accessible via Manager or Magic Hotkey.")
        system_card.add_full_width(self.env_state)

        layout.addWidget(system_card)

        # --- Maintenance Card ---
        maintenance_card = CardFrame("Maintenance & Hygiene")

        # Log Retention
        self.log_retention = QSpinBox()
        self.log_retention.setRange(1, 365)
        self.log_retention.setSuffix(" days")
        self.log_retention.setToolTip("Automatically delete log files older than this number of days.")

        maintenance_card.add_row(
            "Log Retention",
            self.log_retention,
            "How many days to keep historical logs in the 'probes' folder.\nFiles older than this will be deleted on startup."
        )

        layout.addWidget(maintenance_card)
        layout.addStretch()

    def load_data(self, full_config: dict):
        sys_settings = full_config.get("system_settings", {})
        self.env_state.setChecked(sys_settings.get("env_state", False))
        self.log_retention.setValue(sys_settings.get("log_retention_days", 30))

    def get_data(self) -> dict:
        return {
            'system_settings': {
                "env_state": self.env_state.isChecked(),
                "log_retention_days": self.log_retention.value()
            }
        }

    def validate(self) -> tuple[bool, str]:
        return True, ""
