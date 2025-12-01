from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QGridLayout, QFrame)
from PySide6.QtCore import Qt, Signal, QTimer, QDateTime, QSettings
from views.custom_widgets import StatusLight, PCBox

class MainWindow(QMainWindow):
    sig_close_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cafe Sentinel - Monitor")
        self.setStyleSheet("background-color: #1e1e1e;")

        self.settings = QSettings("CafeSentinel", "MonitorApp")
        self.load_window_state()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- TOP BAR ---
        top_bar = QFrame()
        top_bar.setStyleSheet("background-color: #252526; border-radius: 10px;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(20, 10, 20, 10)

        self.router_light = StatusLight("ROUTER")
        self.server_light = StatusLight("SERVER")
        self.isp_light = StatusLight("INTERNET")

        top_layout.addStretch()
        top_layout.addWidget(self.router_light)
        top_layout.addWidget(self.server_light)
        top_layout.addWidget(self.isp_light)
        top_layout.addStretch()

        main_layout.addWidget(top_bar)

        # --- LIVE CLOCK ---
        self.clock_lbl = QLabel("--:--:--")
        self.clock_lbl.setAlignment(Qt.AlignCenter)
        self.clock_lbl.setStyleSheet(
            "color: #00CCFF; font-size: 28px; font-weight: bold; margin-top: 10px; margin-bottom: 5px;")
        main_layout.addWidget(self.clock_lbl)

        # --- LAST SCAN STATUS ---
        self.status_msg = QLabel("Initializing...")
        self.status_msg.setAlignment(Qt.AlignCenter)
        self.status_msg.setStyleSheet("color: #888; font-size: 14px; font-style: italic; margin-bottom: 15px;")
        main_layout.addWidget(self.status_msg)

        # --- PC GRID ---
        grid_frame = QFrame()
        self.grid_layout = QGridLayout(grid_frame)
        self.pc_widgets = {}

        main_layout.addWidget(grid_frame)
        main_layout.addStretch()

        # --- TIMERS ---
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)
        self.update_clock()

    def update_clock(self):
        now = QDateTime.currentDateTime().toString("hh:mm:ss AP")
        self.clock_lbl.setText(now)

    def load_window_state(self):
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.resize(900, 650)

    def save_window_state(self):
        self.settings.setValue("geometry", self.saveGeometry())

    def closeEvent(self, event):
        self.save_window_state()
        event.ignore()
        self.hide()
        self.sig_close_requested.emit()

    # --- SLOTS ---
    def update_infrastructure(self, status_dict):
        # status_dict = {"timestamp": "...", "router": True, "server": False, "internet": True}
        self.status_msg.setText(f"Last Scan: {status_dict['timestamp']}  |  Monitoring Active")
        self.router_light.set_status('good' if status_dict["router"] else 'bad')
        self.server_light.set_status('good' if status_dict["server"] else 'bad')
        self.isp_light.set_status('good' if status_dict["internet"] else 'bad')

    def update_pc_grid(self, pc_data_list):
        if not self.pc_widgets:
            row, col = 0, 0
            max_cols = 6
            for pc in pc_data_list:
                widget = PCBox(pc['name'])
                self.grid_layout.addWidget(widget, row, col)
                self.pc_widgets[pc['name']] = widget
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1

        for pc in pc_data_list:
            if pc['name'] in self.pc_widgets:
                self.pc_widgets[pc['name']].set_active(pc['is_alive'])