from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

class StatusLight(QFrame):
    def __init__(self, label_text):
        super().__init__()
        self.setFixedSize(100, 80)
        self.layout = QVBoxLayout(self)
        self.light = QLabel()
        self.light.setFixedSize(30, 30)
        self.light.setStyleSheet("background-color: #444; border-radius: 15px; border: 2px solid #222;")
        self.light.setAlignment(Qt.AlignCenter)
        self.label = QLabel(label_text)
        self.label.setStyleSheet("color: #AAA; font-weight: bold; font-size: 12px;")
        self.label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.light, alignment=Qt.AlignCenter)
        self.layout.addWidget(self.label, alignment=Qt.AlignCenter)

    def set_status(self, status):
        if status == 'good':
            self.light.setStyleSheet("background-color: #00FF00; border-radius: 15px;")
        elif status == 'bad':
            self.light.setStyleSheet("background-color: #FF0000; border-radius: 15px;")
        else:
            self.light.setStyleSheet("background-color: #444; border-radius: 15px;")


class PCBox(QFrame):
    def __init__(self, pc_name):
        super().__init__()
        self.setFixedSize(80, 60)
        self.setStyleSheet("background-color: #333; border-radius: 5px; border: 1px solid #555;")
        layout = QVBoxLayout(self)
        self.name_lbl = QLabel(pc_name)
        self.name_lbl.setAlignment(Qt.AlignCenter)
        self.name_lbl.setStyleSheet("color: white; font-weight: bold;")
        self.status_lbl = QLabel("Checking...")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(self.name_lbl)
        layout.addWidget(self.status_lbl)

    def set_active(self, is_alive):
        if is_alive:
            self.setStyleSheet("background-color: #005500; border-radius: 5px; border: 1px solid #00FF00;")
            self.status_lbl.setText("ONLINE")
            self.status_lbl.setStyleSheet("color: #00FF00; font-size: 10px;")
        else:
            self.setStyleSheet("background-color: #333; border-radius: 5px; border: 1px solid #555;")
            self.status_lbl.setText("OFFLINE")
            self.status_lbl.setStyleSheet("color: #888; font-size: 10px;")
