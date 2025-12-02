# views/custom_widgets.py

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout, QWidget, QGridLayout
from PySide6.QtCore import Qt, QTimer


class HeartbeatBar(QFrame):
    """Animated horizontal green pulse bar."""

    def __init__(self):
        super().__init__()
        self.setFixedSize(240, 4)
        self.setProperty("class", "heartbeat-bg")

        self.pulse = QFrame(self)
        self.pulse.setFixedSize(60, 4)
        self.pulse.setProperty("class", "heartbeat-pulse")

        self._pulse_x, self._pulse_dir = 0, 1
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.animate)
        self._timer.start(40)

    def animate(self):
        max_x = self.width() - self.pulse.width()
        speed = 3
        self._pulse_x += (speed * self._pulse_dir)
        if self._pulse_x >= max_x:
            self._pulse_x = max_x
            self._pulse_dir = -1
        elif self._pulse_x <= 0:
            self._pulse_x = 0
            self._pulse_dir = 1
        self.pulse.move(int(self._pulse_x), 0)


class StatusIndicator(QFrame):
    """Panel for Router/Server/Internet."""

    def __init__(self, title):
        super().__init__()
        self.setProperty("class", "status-indicator")
        self.setFixedSize(140, 95)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(8, 8, 8, 8)

        h_layout = QHBoxLayout()
        self.light = QLabel()
        self.light.setFixedSize(14, 14)
        self.light.setProperty("class", "status-light")

        self.label = QLabel(title)
        self.label.setProperty("class", "status-title")

        h_layout.addStretch()
        h_layout.addWidget(self.light)
        h_layout.addWidget(self.label)
        h_layout.addStretch()
        self.layout.addLayout(h_layout)

        self.status_lbl = QLabel("WAITING")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setProperty("class", "status-label")
        self.layout.addWidget(self.status_lbl, 0, Qt.AlignCenter)

        self.set_offline()

    def set_online(self):
        self.light.setProperty("state", "online")
        self.label.setProperty("state", "online")
        self.status_lbl.setProperty("state", "online")
        self.status_lbl.setText("ONLINE")
        self._refresh_style()

    def set_offline(self):
        self.light.setProperty("state", "offline")
        self.label.setProperty("state", "offline")
        self.status_lbl.setProperty("state", "offline")
        self.status_lbl.setText("OFFLINE")
        self._refresh_style()

    def _refresh_style(self):
        self.light.style().unpolish(self.light)
        self.light.style().polish(self.light)
        self.label.style().unpolish(self.label)
        self.label.style().polish(self.label)
        self.status_lbl.style().unpolish(self.status_lbl)
        self.status_lbl.style().polish(self.status_lbl)


class SentinelPCBox(QFrame):
    WIDTH, HEIGHT = 100, 75

    def __init__(self, pc_name):
        super().__init__()
        self.setFixedSize(self.WIDTH, self.HEIGHT)
        self.setProperty("class", "pc-box")

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(2)
        self.layout.setContentsMargins(8, 6, 8, 6)

        self.name_lbl = QLabel(pc_name)
        self.name_lbl.setAlignment(Qt.AlignCenter)
        self.name_lbl.setProperty("class", "pc-name")

        self.status_lbl = QLabel("OFFLINE")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setProperty("class", "pc-status")

        self.layout.addWidget(self.name_lbl)
        self.layout.addWidget(self.status_lbl)

        self.set_offline()

    def set_active(self):
        self.setProperty("state", "online")
        self.name_lbl.setProperty("state", "online")
        self.status_lbl.setProperty("state", "online")
        self.status_lbl.setText("ACTIVE")
        self._refresh_style()

    def set_offline(self):
        self.setProperty("state", "offline")
        self.name_lbl.setProperty("state", "offline")
        self.status_lbl.setProperty("state", "offline")
        self.status_lbl.setText("OFFLINE")
        self._refresh_style()

    def _refresh_style(self):
        self.style().unpolish(self)
        self.style().polish(self)
        self.name_lbl.style().unpolish(self.name_lbl)
        self.name_lbl.style().polish(self.name_lbl)
        self.status_lbl.style().unpolish(self.status_lbl)
        self.status_lbl.style().polish(self.status_lbl)


class ResponsivePCGrid(QWidget):
    """Grid of SentinelPCBox that auto-reflows."""

    def __init__(self, pc_widgets):
        super().__init__()
        self.pc_widgets = pc_widgets
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(12)
        self._current_cols = 1
        self.reflow_items()

    def resizeEvent(self, event):
        width = event.size().width()
        item_width = SentinelPCBox.WIDTH + 12
        new_cols = max(1, width // item_width)
        if new_cols != self._current_cols:
            self._current_cols = new_cols
            self.reflow_items()
        super().resizeEvent(event)

    def reflow_items(self):
        for i in reversed(range(self.grid.count())):
            self.grid.takeAt(i)
        row, col = 0, 0
        for widget in self.pc_widgets:
            self.grid.addWidget(widget, row, col)
            col += 1
            if col >= self._current_cols:
                col = 0
                row += 1
