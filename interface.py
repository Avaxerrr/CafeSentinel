import sys
import ctypes

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog

from controllers.system_tray_app import SystemTrayController
from models.security_manager import SecurityManager
from views.setup_wizard import SetupWizard

EXIT_CODE_SETUP_CANCEL = 100


def is_admin():
    """Check if the script has Admin rights."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def check_and_create_vault():
    """Checks if security vault exists, if not, runs setup wizard."""
    if SecurityManager.vault_exists():
        return True

    wizard = SetupWizard()
    if wizard.exec() == QDialog.Accepted:
        admin_pwd, privacy_pwd = wizard.get_passwords()
        success = SecurityManager.create_vault(admin_pwd, privacy_pwd)

        if success:
            QMessageBox.information(None, "Setup Complete", "Security vault created successfully!")
            return True
        else:
            QMessageBox.critical(None, "Setup Failed", "Failed to create security vault.")
            return False
    else:
        QMessageBox.warning(None, "Setup Cancelled", "Setup was cancelled.")
        return False


def main():
    # 1. Check Admin Privileges (Required for ICMP)
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit(0)

    # 2. Initialize Qt Application
    app = QApplication(sys.argv)

    from PySide6.QtGui import QFontDatabase, QFont
    import resources_rc  # This imports the compiled QRC

    font_id = QFontDatabase.addApplicationFont(":/fonts/SUSE")

    if font_id == -1:
        print("⚠️ WARNING: Failed to load SUSE font from QRC. Falling back to default.")
    else:
        families = QFontDatabase.applicationFontFamilies(font_id)
        print(f"✅ SUSE Font Loaded from QRC: {families}")

        # Apply optimal rendering settings globally
        app_font = QFont("SUSE", 10)
        app_font.setStyleStrategy(
            QFont.StyleStrategy.PreferQuality | QFont.StyleStrategy.PreferAntialias
        )
        app_font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
        app.setFont(app_font)
        print("✅ Font rendering optimized (PreferQuality + NoHinting)")

    with open("cafesentinel_styles.qss", "r") as f:
        app.setStyleSheet(f.read())
    app.setQuitOnLastWindowClosed(False)

    # 3. Check/Create Security Vault
    if not check_and_create_vault():
        sys.exit(EXIT_CODE_SETUP_CANCEL)

    # 4. Launch the System Tray Controller
    # (The controller now handles Watchdog monitoring automatically via QTimer)
    controller = SystemTrayController(app)

    # 5. Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()