import json
import os
import shutil
import threading
import base64
from datetime import datetime
from cryptography.fernet import Fernet
from PySide6.QtCore import QObject, Signal
from models.app_logger import AppLogger
from utils.resource_manager import ResourceManager
from models.security_manager import SecurityManager


class ConfigManager(QObject):
    """
    Singleton Class.
    Centralizes all configuration access, file I/O, validation, and updates.
    Handles encryption using machine-specific keys (cscf.dll).
    """
    _instance = None
    _lock = threading.Lock()

    # Signal emitted whenever config is updated (from API or Local)
    sig_config_changed = Signal(dict)

    # CONSTANTS
    CONFIG_FILENAME = "cscf.dll"
    LEGACY_FILENAME = "config.json"
    BACKUP_DIR = "config_backups"

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
        },
        "system_settings": {
            "env_state": False,
            "log_retention_days": 30
        }
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        super().__init__()
        self.config = {}
        self._config_dirty = False
        self._initialized = True

        # Resolve paths
        self.abs_config_path = ResourceManager.get_resource_path(self.CONFIG_FILENAME)
        self.abs_legacy_path = ResourceManager.get_resource_path(self.LEGACY_FILENAME)
        self.abs_backup_dir = ResourceManager.get_resource_path(self.BACKUP_DIR)

        # Setup Encryption Key
        self.cipher_key = SecurityManager._generate_key()
        self.cipher = Fernet(self.cipher_key)

        # Ensure environment
        self._ensure_backup_dir()
        self._load_initial_config()

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _ensure_backup_dir(self):
        if not os.path.exists(self.abs_backup_dir):
            os.makedirs(self.abs_backup_dir)

    def _load_initial_config(self):
        """
        Loads config from disk.
        """
        # 1. Check for Encrypted Config
        if os.path.exists(self.abs_config_path):
            try:
                with open(self.abs_config_path, 'rb') as f:
                    encrypted_data = f.read()
                decrypted_data = self.cipher.decrypt(encrypted_data)
                self.config = json.loads(decrypted_data.decode())
            except Exception as e:
                AppLogger.log("Load error. Using defaults.", category="CONFIG")
                self.config = self.DEFAULT_CONFIG.copy()

        # 2. Check for Legacy JSON (Migration)
        elif os.path.exists(self.abs_legacy_path):
            AppLogger.log("Legacy format detected. Upgrading...", category="CONFIG")
            try:
                with open(self.abs_legacy_path, 'r') as f:
                    self.config = json.load(f)

                self._save_to_disk(self.config)
                os.rename(self.abs_legacy_path, self.abs_legacy_path + ".bak")
                AppLogger.log("Upgrade complete.", category="CONFIG")
            except Exception as e:
                AppLogger.log("Upgrade failed. Using defaults.", category="CONFIG")
                self.config = self.DEFAULT_CONFIG.copy()
                self._save_to_disk(self.config)

        # 3. Fresh Install
        else:
            AppLogger.log("Initializing with default settings...", category="CONFIG")
            self.config = self.DEFAULT_CONFIG.copy()
            self._save_to_disk(self.config)

    def get_config(self) -> dict:
        """Thread-safe read of the current configuration."""
        with self._lock:
            return self.config.copy()

    def update_config(self, new_config: dict) -> tuple[bool, str]:
        """
        Thread-safe update.
        """
        with self._lock:
            # Validate Structure
            valid, error_msg = self._validate_config(new_config)
            if not valid:
                return False, error_msg

            try:
                # 1. Create Backup
                self._create_backup()

                # 2. Save to Disk (Encrypted)
                self._save_to_disk(new_config)

                # 3. Update Memory
                self.config = new_config

                # 4. Set Dirty Flag (for cross-thread polling)
                self._config_dirty = True

                # 5. Emit Signal (for same-thread listeners like future GUI)
                self.sig_config_changed.emit(self.config)

                AppLogger.log("Updated successfully.", category="CONFIG")
                return True, "Configuration updated successfully"

            except Exception as e:
                AppLogger.log(f"Update Failed! {e}", category="CONFIG")
                return False, str(e)

    def check_and_clear_dirty(self) -> bool:
        """
        Check if config was updated, and clear the flag.
        Returns True if config needs to be reloaded.
        Thread-safe.
        """
        with self._lock:
            if self._config_dirty:
                self._config_dirty = False
                return True
            return False

    def _save_to_disk(self, data: dict):
        """Encrypts and writes the config to cscf.dll."""
        json_str = json.dumps(data, indent=4)
        encrypted_data = self.cipher.encrypt(json_str.encode())

        with open(self.abs_config_path, 'wb') as f:
            f.write(encrypted_data)

    def _create_backup(self):
        """Creates an ENCRYPTED backup file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}.{self.CONFIG_FILENAME}"
            backup_path = os.path.join(self.abs_backup_dir, backup_name)

            if os.path.exists(self.abs_config_path):
                shutil.copy(self.abs_config_path, backup_path)
                self._cleanup_old_backups()
        except Exception as e:
            AppLogger.log("Backup operation failed.", category="CONFIG")

    def _cleanup_old_backups(self):
        """Keeps only the last 10 backups."""
        try:
            files = sorted(
                [os.path.join(self.abs_backup_dir, f) for f in os.listdir(self.abs_backup_dir)
                 if f.startswith("backup_")],
                key=os.path.getmtime
            )
            while len(files) > 10:
                os.remove(files.pop(0))
        except Exception:
            pass

    def get_backup_list(self):
        """Returns list of backup filenames."""
        try:
            return sorted(
                [f for f in os.listdir(self.abs_backup_dir) if f.startswith("backup_")],
                reverse=True
            )
        except:
            return []

    def _validate_config(self, config):
        """Validate config has required structure."""
        required_keys = [
            'targets',
            'monitor_settings',
            'screenshot_settings',
            'discord_settings',
            'verification_settings',
            'occupancy_settings'
        ]

        for key in required_keys:
            if key not in config:
                AppLogger.log(f"Validation failed: Missing key '{key}'", category="CONFIG")
                return False, f"Missing key '{key}'"

        # Validate screenshot_settings
        screenshot = config.get('screenshot_settings', {})
        if 'interval_minutes' in screenshot:
            if not (1 <= screenshot['interval_minutes'] <= 1440):
                AppLogger.log("Validation failed: Invalid screenshot interval", category="CONFIG")
                return False, "Invalid screenshot interval (1-1440)"
        if 'quality' in screenshot:
            if not (1 <= screenshot['quality'] <= 100):
                AppLogger.log("Validation failed: Invalid screenshot quality", category="CONFIG")
                return False, "Invalid screenshot quality (1-100)"

        # Validate monitor_settings
        monitor = config.get('monitor_settings', {})
        if 'interval_seconds' in monitor:
            if not (1 <= monitor['interval_seconds'] <= 60):
                AppLogger.log("Validation failed: Invalid monitor interval", category="CONFIG")
                return False, "Invalid monitor interval (1-60)"

        return True, "Valid"