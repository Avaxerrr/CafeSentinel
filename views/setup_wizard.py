from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit,
                               QPushButton, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class SetupWizard(QDialog):
    """
    First-run setup dialog to collect Admin and Privacy passwords.
    Only appears when .dll does not exist.
    """

    def __init__(self):
        super().__init__()
        self.admin_password = None
        self.privacy_password = None
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("CafeSentinel - Initial Setup")
        self.setFixedSize(300, 450)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Title
        title = QLabel("🔐 First-Time Setup")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Instructions
        instructions = QLabel(
            "Please set two passwords:\n\n"
            "• Admin Password: Required to close the application\n"
            "• Privacy Password: Toggles screenshot monitoring\n\n"
            "Keep these passwords secure!"
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #666; padding: 10px;")
        layout.addWidget(instructions)

        # Admin Password Input
        admin_label = QLabel("Admin Password:")
        admin_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(admin_label)

        self.admin_input = QLineEdit()
        self.admin_input.setEchoMode(QLineEdit.Password)
        self.admin_input.setPlaceholderText("Enter admin password")
        layout.addWidget(self.admin_input)

        # Privacy Password Input
        privacy_label = QLabel("Privacy Password:")
        privacy_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(privacy_label)

        self.privacy_input = QLineEdit()
        self.privacy_input.setEchoMode(QLineEdit.Password)
        self.privacy_input.setPlaceholderText("Enter privacy password")
        layout.addWidget(self.privacy_input)

        # Confirm Button
        self.confirm_btn = QPushButton("✓ Confirm Setup")
        self.confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #00A86B;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #008C5A;
            }
        """)
        self.confirm_btn.clicked.connect(self.validate_and_accept)
        layout.addWidget(self.confirm_btn)

    def validate_and_accept(self):
        """Validate inputs and accept the dialog."""
        admin_pwd = self.admin_input.text().strip()
        privacy_pwd = self.privacy_input.text().strip()

        # Validation
        if len(admin_pwd) < 4:
            QMessageBox.warning(self, "Invalid Input",
                              "Admin password must be at least 4 characters.")
            return

        if len(privacy_pwd) < 4:
            QMessageBox.warning(self, "Invalid Input",
                              "Privacy password must be at least 4 characters.")
            return

        if admin_pwd == privacy_pwd:
            QMessageBox.warning(self, "Invalid Input",
                              "Admin and Privacy passwords must be different!")
            return

        # Store and accept
        self.admin_password = admin_pwd
        self.privacy_password = privacy_pwd
        self.accept()

    def get_passwords(self):
        """Return the entered passwords as a tuple."""
        return (self.admin_password, self.privacy_password)