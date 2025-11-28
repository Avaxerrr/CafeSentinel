import json
import os
import shutil
from datetime import datetime
from models.app_logger import AppLogger
from utils.resource_manager import ResourceManager


class ConfigManager:
    DEFAULT_CONFIG = {
        "targets": {
            "router": "192.168.1.1",
            "server": "192.168.1.200",
            "internet": "8.8.8.8"
        },
        "monitor_settings": {
            "interval_seconds": 2,
            "pc_subnet": "192.168.1",
            "pc_start_range": 110,
            "pc_count": 20
        },
        "verification_settings": {
            "retry_delay_seconds": 1.0,
            "secondary_target": "1.1.1.1",
            "min_incident_duration_seconds": 10
        },
        "screenshot_settings": {
            "enabled": True,
            "interval_minutes": 60,
            "resize_ratio": 1.0,
            "quality": 80
        },
        "occupancy_settings": {
            "enabled": True,
            "mode": "session",
            "min_session_minutes": 3,
            "batch_delay_seconds": 30,
            "hourly_snapshot_enabled": True
        },
        "discord_settings": {
            "enabled": False,
            "shop_name": "My Internet Cafe",
            "webhook_alerts": "",
            "webhook_occupancy": "",
            "webhook_screenshots": ""
        }
    }

    @staticmethod
    def ensure_config_exists(config_rel_path="config.json"):
        """
        Checks if config exists. If not, creates it from DEFAULT_CONFIG.
        Returns the absolute path to the config file.
        """
        abs_path = ResourceManager.get_resource_path(config_rel_path)

        if not os.path.exists(abs_path):
            AppLogger.log("CONFIG: File missing. Generating default config...")
            try:
                with open(abs_path, 'w') as f:
                    json.dump(ConfigManager.DEFAULT_CONFIG, f, indent=4)
                AppLogger.log(f"CONFIG: Created new config at {abs_path}")
            except Exception as e:
                AppLogger.log(f"CONFIG: Failed to create config! {e}")

        return abs_path

    @staticmethod
    def load_config(abs_path):
        """
        Loads the JSON config safely.
        """
        try:
            with open(abs_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            AppLogger.log("CONFIG: ⚠️ JSON Syntax Error. File is corrupt.")
            return {}  # Return empty, worker handles missing keys
        except Exception as e:
            AppLogger.log(f"CONFIG: Read Error: {e}")
            return {}
