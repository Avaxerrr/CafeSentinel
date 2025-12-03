from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit,
                               QPushButton, QMessageBox, QSpacerItem, QSizePolicy, QLayout)
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

        # Remove fixed size, use minimum width + auto-height
        self.setMinimumWidth(350)
        self.setModal(True)

        # MAIN LAYOUT
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)  # Generous gap between separate sections
        main_layout.setContentsMargins(25, 25, 25, 25)

        # This ensures the window automatically fits the content height
        main_layout.setSizeConstraint(QLayout.SetFixedSize)

        # 1. TITLE
        title = QLabel("First-Time Setup")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setProperty("class", "wizard-title")
        main_layout.addWidget(title)

        # 2. INSTRUCTIONS
        instructions = QLabel(
            "Please set two passwords:\n\n"
            "• Admin Password: Required to close the application\n"
            "• Privacy Password: Toggles screenshot monitoring\n\n"
            "Keep these passwords secure!"
        )
        instructions.setWordWrap(True)
        instructions.setProperty("class", "wizard-instructions")
        instructions.setStyleSheet("margin-bottom: 10px;")
        main_layout.addWidget(instructions)

        # 3. FORM FIELDS (Using scalable helper)

        # Admin Password
        self.admin_input = QLineEdit()
        self.admin_input.setEchoMode(QLineEdit.Password)
        self.admin_input.setPlaceholderText("Enter admin password")
        self.add_form_row(main_layout, "Admin Password:", self.admin_input)

        # Privacy Password
        self.privacy_input = QLineEdit()
        self.privacy_input.setEchoMode(QLineEdit.Password)
        self.privacy_input.setPlaceholderText("Enter privacy password")
        self.add_form_row(main_layout, "Privacy Password:", self.privacy_input)

        # Spacer to push button to the bottom
        vertical_spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        main_layout.addItem(vertical_spacer)

        # 4. CONFIRM BUTTON
        self.confirm_btn = QPushButton("Confirm Setup")
        self.confirm_btn.setObjectName("PrimaryButton")
        self.confirm_btn.setCursor(Qt.PointingHandCursor)
        self.confirm_btn.clicked.connect(self.validate_and_accept)
        main_layout.addWidget(self.confirm_btn)

    def add_form_row(self, parent_layout, label_text, widget):
        """
        Helper to add a Label + Widget pair with tight spacing
        to the parent layout.
        """
        # Create a container for this specific row
        row_layout = QVBoxLayout()
        row_layout.setSpacing(2)
        row_layout.setContentsMargins(0, 0, 0, 0)

        # Create the label
        label = QLabel(label_text)
        label.setProperty("class", "field-label")
        row_layout.addWidget(label)

        # Add the widget (Input, Combo, etc.)
        row_layout.addWidget(widget)

        # Add this row to the main layout
        parent_layout.addLayout(row_layout)

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