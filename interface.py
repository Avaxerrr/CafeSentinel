import sys
import ctypes
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog

from controllers.system_tray_app import SystemTrayController
from models.startup_manager import StartupManager
from models.security_manager import SecurityManager
from views.setup_wizard import SetupWizard


def is_admin():
    """Check if the script has Admin rights."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def check_and_create_vault():
    """
    Check if the security vault exists.
    If not, launch the setup wizard to create it.
    Returns True if vault is ready, False if setup was cancelled.
    """
    if SecurityManager.vault_exists():
        return True  # Vault already exists

    # Show setup wizard
    wizard = SetupWizard()
    if wizard.exec() == QDialog.Accepted:  # Use QDialog.Accepted
        admin_pwd, privacy_pwd = wizard.get_passwords()

        # Create the vault
        success = SecurityManager.create_vault(admin_pwd, privacy_pwd)

        if success:
            QMessageBox.information(
                None,
                "Setup Complete",
                "Security vault created successfully!\n\n"
                "The application will now start."
            )
            return True
        else:
            QMessageBox.critical(
                None,
                "Setup Failed",
                "Failed to create security vault.\n"
                "The application cannot start."
            )
            return False
    else:
        # User cancelled setup
        QMessageBox.warning(
            None,
            "Setup Cancelled",
            "Setup was cancelled.\n"
            "The application requires initial configuration to run."
        )
        return False


def main():
    # 1. Check Admin Privileges
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit(0)

    # 2. Initialize Qt Application
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running when window is closed

    # 3. Check/Create Security Vault
    if not check_and_create_vault():
        sys.exit(1)  # Exit if setup failed or was cancelled

    # 4. Register in Startup (Task Scheduler)
    try:
        StartupManager.ensure_startup()
    except Exception as e:
        print(f"Startup registration failed: {e}")

    # 5. Launch the System Tray Controller
    controller = SystemTrayController(app)

    # 6. Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()