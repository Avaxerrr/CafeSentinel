import os
import sys
import json
import hashlib
from cryptography.fernet import Fernet
import base64
from utils.resource_manager import ResourceManager


class SecurityManager:
    """
    Handles encrypted storage of Admin and Privacy passwords.
    Uses a .dll disguise for the vault file.
    """
    VAULT_FILE = "cron.dll"

    @staticmethod
    def _get_vault_path():
        """Get the absolute path to the vault file."""
        return ResourceManager.get_resource_path(SecurityManager.VAULT_FILE)

    @staticmethod
    def _generate_key():
        """
        Generate a deterministic key based on machine-specific data.
        This ensures the vault can only be decrypted on this machine.
        """
        # Use a combination of factors to create a unique key
        machine_id = os.environ.get('COMPUTERNAME', 'DEFAULT_MACHINE')
        seed = f"SENTINEL_{machine_id}_VAULT"
        key_hash = hashlib.sha256(seed.encode()).digest()
        return base64.urlsafe_b64encode(key_hash)

    @staticmethod
    def vault_exists():
        """Check if the vault file exists."""
        return os.path.exists(SecurityManager._get_vault_path())

    @staticmethod
    def create_vault(admin_password, privacy_password):
        """
        Create the encrypted vault with both passwords.
        Passwords are hashed before storage.
        """
        # Hash the passwords
        admin_hash = hashlib.sha256(admin_password.encode()).hexdigest()
        privacy_hash = hashlib.sha256(privacy_password.encode()).hexdigest()

        # Create the data structure
        vault_data = {
            "admin": admin_hash,
            "privacy": privacy_hash,
            "version": "1.0"
        }

        # Encrypt and save
        key = SecurityManager._generate_key()
        cipher = Fernet(key)
        encrypted_data = cipher.encrypt(json.dumps(vault_data).encode())

        vault_path = SecurityManager._get_vault_path()
        with open(vault_path, 'wb') as f:
            f.write(encrypted_data)

        return True

    @staticmethod
    def _load_vault():
        """Load and decrypt the vault file."""
        try:
            vault_path = SecurityManager._get_vault_path()
            with open(vault_path, 'rb') as f:
                encrypted_data = f.read()

            key = SecurityManager._generate_key()
            cipher = Fernet(key)
            decrypted_data = cipher.decrypt(encrypted_data)

            return json.loads(decrypted_data.decode())
        except Exception as e:
            print(f"Vault Load Error: {e}")
            return None

    @staticmethod
    def verify_admin(password):
        """
        Verify if the provided password matches the admin password.
        Returns True if correct, False otherwise.
        """
        vault_data = SecurityManager._load_vault()
        if not vault_data:
            return False

        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return password_hash == vault_data.get("admin", "")

    @staticmethod
    def verify_privacy(password):
        """
        Verify if the provided password matches the privacy password.
        Returns True if correct, False otherwise.
        """
        vault_data = SecurityManager._load_vault()
        if not vault_data:
            return False

        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return password_hash == vault_data.get("privacy", "")
