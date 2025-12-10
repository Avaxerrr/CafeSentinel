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

        # --- System Behavior Card (Stealth Mode) ---
        system_card = CardFrame("Application Behavior")

        # Stealth Mode
        self.env_state = ToggleSwitch("Enable Stealth Mode (Hide All Tray Icons)")
        self.env_state.setToolTip("Runs app invisibly. Overrides individual icon settings.")
        system_card.add_full_width(self.env_state)

        layout.addWidget(system_card)

        # --- Tray Icon Visibility Card (NEW) ---
        tray_card = CardFrame("Tray Icon Visibility")

        self.toggle_router = ToggleSwitch("Show Router Status")
        self.toggle_server = ToggleSwitch("Show Server Status")
        self.toggle_internet = ToggleSwitch("Show Internet Status")
        self.toggle_clients = ToggleSwitch("Show Active Clients Count")

        tray_card.add_full_width(self.toggle_router)
        tray_card.add_full_width(self.toggle_server)
        tray_card.add_full_width(self.toggle_internet)
        tray_card.add_full_width(self.toggle_clients)

        layout.addWidget(tray_card)

        # --- Maintenance Card ---
        maintenance_card = CardFrame("Data Management")

        # Log Retention
        self.log_retention = QSpinBox()
        self.log_retention.setRange(1, 365)
        self.log_retention.setSuffix(" days")
        self.log_retention.setToolTip("Automatically delete log files older than this number of days.")

        maintenance_card.add_row(
            "Log Retention Period",
            self.log_retention,
            "How many days to keep historical logs in the 'probes' folder.\nFiles older than this will be deleted on startup."
        )

        layout.addWidget(maintenance_card)
        layout.addStretch()

    def load_data(self, full_config: dict):
        sys_settings = full_config.get("system_settings", {})

        # Load Stealth Mode
        self.env_state.setChecked(sys_settings.get("env_state", False))

        # Load Retention
        self.log_retention.setValue(sys_settings.get("log_retention_days", 30))

        # Load Tray Visibility (Default to True if missing)
        visibility = sys_settings.get("tray_visibility", {})
        self.toggle_router.setChecked(visibility.get("router", True))
        self.toggle_server.setChecked(visibility.get("server", True))
        self.toggle_internet.setChecked(visibility.get("internet", True))
        self.toggle_clients.setChecked(visibility.get("clients", True))

    def get_data(self) -> dict:
        return {
            'system_settings': {
                "env_state": self.env_state.isChecked(),
                "log_retention_days": self.log_retention.value(),
                "tray_visibility": {
                    "router": self.toggle_router.isChecked(),
                    "server": self.toggle_server.isChecked(),
                    "internet": self.toggle_internet.isChecked(),
                    "clients": self.toggle_clients.isChecked()
                }
            }
        }

    def validate(self) -> tuple[bool, str]:
        # Rule: At least one icon must be visible if Stealth Mode is OFF
        # (Though effectively we just want to prevent a user from accidentally hiding everything)
        # Even if Stealth Mode is ON, we should probably enforce at least one check
        # so when they turn Stealth Mode OFF, something appears.

        any_checked = (
                self.toggle_router.isChecked() or
                self.toggle_server.isChecked() or
                self.toggle_internet.isChecked() or
                self.toggle_clients.isChecked()
        )

        if not any_checked:
            return False, "At least one tray icon must be enabled!"

        return True, ""
