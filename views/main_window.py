from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QTimer, QDateTime, QSettings
from views.custom_widgets import StatusIndicator, SentinelPCBox, ResponsivePCGrid, HeartbeatBar

class MainWindow(QMainWindow):
    sig_close_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cafe Sentinel - Monitor")
        self.resize(950, 750)
        self.settings = QSettings("CafeSentinel", "MonitorApp")
        self.load_window_state()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Diagnostics row
        diag_layout = QHBoxLayout()
        self.router_stat = StatusIndicator("ROUTER")
        self.server_stat = StatusIndicator("SERVER")
        self.net_stat   = StatusIndicator("INTERNET")
        diag_layout.addStretch()
        diag_layout.addWidget(self.router_stat)
        diag_layout.addWidget(self.server_stat)
        diag_layout.addWidget(self.net_stat)
        diag_layout.addStretch()
        main_layout.addLayout(diag_layout)

        # Clock & heartbeat
        clock_container = QFrame()
        clock_layout = QVBoxLayout(clock_container)
        clock_layout.setSpacing(5)
        clock_layout.setContentsMargins(0, 0, 0, 0)
        self.clock_lbl = QLabel("--:--:--")
        self.clock_lbl.setAlignment(Qt.AlignCenter)
        self.clock_lbl.setProperty("class", "dashboard-clock")
        self.heartbeat_bar = HeartbeatBar()
        hb_layout = QHBoxLayout()
        hb_layout.addStretch()
        hb_layout.addWidget(self.heartbeat_bar)
        hb_layout.addStretch()
        clock_layout.addWidget(self.clock_lbl)
        clock_layout.addLayout(hb_layout)
        main_layout.addWidget(clock_container)
        # PC grid
        self.pc_widgets = {}
        self.responsive_grid = ResponsivePCGrid([])
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setProperty("class", "dashboard-scroll")
        scroll.setWidget(self.responsive_grid)
        main_layout.addWidget(scroll)

        # Footer (Last Scan + Uptime)
        footer_frame = QFrame()
        footer_frame.setProperty("class", "dashboard-footer")
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(15, 8, 15, 8)
        self.scan_lbl = QLabel("Last Scan: Just now")
        self.scan_lbl.setProperty("class", "dashboard-footer-label")
        self.uptime_lbl = QLabel("Sentinel Uptime: 00h 00m")
        self.uptime_lbl.setProperty("class", "dashboard-uptime")
        footer_layout.addWidget(self.scan_lbl)
        footer_layout.addStretch()
        footer_layout.addWidget(self.uptime_lbl)
        main_layout.addWidget(footer_frame)

        # Timers
        self.startup_time = QDateTime.currentDateTime()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_clock_logic)
        self.timer.start(1000)
        self.update_clock()

    def update_clock_logic(self):
        now = QDateTime.currentDateTime()
        self.clock_lbl.setText(now.toString("hh:mm:ss AP"))
        # Uptime
        seconds_diff = self.startup_time.secsTo(now)
        hours = seconds_diff // 3600
        minutes = (seconds_diff % 3600) // 60
        self.uptime_lbl.setText(f"Sentinel Uptime: {hours:02d}h {minutes:02d}m")

    def update_clock(self):
        now = QDateTime.currentDateTime().toString("hh:mm:ss AP")
        self.clock_lbl.setText(now)

    def load_window_state(self):
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.resize(950, 750)

    def save_window_state(self):
        self.settings.setValue("geometry", self.saveGeometry())

    def closeEvent(self, event):
        self.save_window_state()
        event.ignore()
        self.hide()
        self.sig_close_requested.emit()

    # --- BACKEND SLOTS ---
    def update_infrastructure(self, status_dict):
        self.scan_lbl.setText(f"Last Scan: {status_dict['timestamp']}")
        if status_dict["router"]:
            self.router_stat.set_online()
        else:
            self.router_stat.set_offline()
        if status_dict["server"]:
            self.server_stat.set_online()
        else:
            self.server_stat.set_offline()
        if status_dict["internet"]:
            self.net_stat.set_online()
        else:
            self.net_stat.set_offline()

    def update_pc_grid(self, pc_data_list):
        unique_names = [pc['name'] for pc in pc_data_list]
        if set(self.pc_widgets.keys()) != set(unique_names):
            for widget in self.pc_widgets.values():
                widget.setParent(None)
            pc_widget_objs = []
            self.pc_widgets = {}
            for pc in pc_data_list:
                widget = SentinelPCBox(pc['name'])
                self.pc_widgets[pc['name']] = widget
                pc_widget_objs.append(widget)
            self.responsive_grid.pc_widgets = pc_widget_objs
            self.responsive_grid.reflow_items()
        for pc in pc_data_list:
            widget = self.pc_widgets.get(pc['name'])
            if widget:
                if pc['is_alive']:
                    widget.set_active()
                else:
                    widget.set_offline()