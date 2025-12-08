from PySide6.QtWidgets import (QCheckBox, QFrame, QVBoxLayout, QLabel,
                               QWidget, QGridLayout, QHBoxLayout)
from PySide6.QtGui import QPainter, QColor, QIcon
from PySide6.QtCore import Qt, QRect, QSize, QTimer



class ToggleSwitch(QCheckBox):
    """
    Simple Toggle Switch (Manager Style - No Animation).
    Includes sizeHint to ensure text is never cut off in layouts.
    """

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        # We do NOT setFixedSize here because width depends on text length

    def hitButton(self, pos):
        """Allow clicking anywhere on the widget (text or switch)."""
        return self.contentsRect().contains(pos)

    def sizeHint(self):
        """Tell the layout exactly how big we need to be."""
        switch_width = 36
        gap = 10
        # Calculate text width based on current font
        text_width = self.fontMetrics().horizontalAdvance(self.text())

        # Total width = Switch + Gap + Text
        total_width = switch_width + gap + text_width
        # Height is fixed at 20px (matches Manager)
        return QSize(total_width, 20)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # --- Colors ---
        if not self.isEnabled():
            bar_color = QColor("#252526")
            handle_color = QColor("#666666")
        elif self.isChecked():
            bar_color = QColor("#00C853")
            handle_color = QColor("#FFFFFF")
        else:
            bar_color = QColor("#4F5458")
            handle_color = QColor("#FFFFFF")

        # --- 1. Draw Toggle Switch ---
        switch_width = 36
        switch_height = 20
        # The switch sits at the left-most side (x=0)
        switch_rect = QRect(0, 0, switch_width, switch_height)

        # Draw background track
        p.setBrush(bar_color)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(switch_rect, 10, 10)

        # Draw handle (circle)
        handle_size = 16
        padding = 2

        if self.isChecked():
            handle_x = switch_width - handle_size - padding
        else:
            handle_x = padding

        handle_rect = QRect(handle_x, padding, handle_size, handle_size)
        p.setBrush(handle_color)
        p.drawEllipse(handle_rect)

        # --- 2. Draw Text Label (if present) ---
        if self.text():
            text_x = switch_width + 10  # 10px gap
            p.setPen(QColor("#E0E0E0"))
            # Vertically center the text
            p.drawText(text_x, 0, self.width() - text_x, self.height(),
                       Qt.AlignLeft | Qt.AlignVCenter, self.text())

        p.end()


class CardFrame(QFrame):
    """
    A styling wrapper that replaces QGroupBox.
    - Uses setObjectName("Card") to match Manager styling logic.
    """

    def __init__(self, title, layout_to_wrap):
        super().__init__()
        self.setObjectName("Card")  # Critical for CSS

        # Main Layout of the Card
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(15)

        # 1. Title Label
        self.lbl_title = QLabel(title)
        self.lbl_title.setObjectName("CardTitle")  # Critical for CSS
        self.main_layout.addWidget(self.lbl_title)

        # 2. Add the content layout
        self.main_layout.addLayout(layout_to_wrap)



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
        self.setFixedSize(140, 120)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # --- Icon Label ---
        self.icon_lbl = QLabel()
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        self.icon_lbl.setProperty("class", "status-icon")

        # Load icons based on title
        title_lower = title.lower()
        icon_on = QIcon(f":/icons/{title_lower}_on")
        icon_off = QIcon(f":/icons/{title_lower}_off")

        # Generate pixmaps from icons
        icon_size = 28
        self.icon_on_pixmap = icon_on.pixmap(icon_size, icon_size)
        self.icon_off_pixmap = icon_off.pixmap(icon_size, icon_size)

        # Title Label (ROUTER/SERVER/INTERNET)
        self.label = QLabel(title)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setProperty("class", "status-title")

        # ====== STATUS TEXT WITH CIRCLE (ONLINE/OFFLINE) ======
        # Container for status text + circle
        status_container = QWidget()
        status_container.setProperty("class", "status-container")
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(5)

        # Circle/Light indicator
        self.light = QLabel()
        self.light.setFixedSize(12, 12)  # Smaller circle (was 14x14)
        self.light.setProperty("class", "status-light")

        self.status_lbl = QLabel("WAITING")
        self.status_lbl.setProperty("class", "status-label")

        status_layout.addStretch()
        status_layout.addWidget(self.light)
        status_layout.addWidget(self.status_lbl)
        status_layout.addStretch()

        # Add all to main layout
        self.layout.addWidget(self.icon_lbl)
        self.layout.addWidget(self.label)
        self.layout.addWidget(status_container)

        self.set_offline()

    def set_online(self):
        self.light.setProperty("state", "online")
        self.label.setProperty("state", "online")
        self.status_lbl.setProperty("state", "online")
        self.status_lbl.setText("ONLINE")
        self.icon_lbl.setPixmap(self.icon_on_pixmap)
        self._refresh_style()

    def set_offline(self):
        self.light.setProperty("state", "offline")
        self.label.setProperty("state", "offline")
        self.status_lbl.setProperty("state", "offline")
        self.status_lbl.setText("OFFLINE")
        self.icon_lbl.setPixmap(self.icon_off_pixmap)
        self._refresh_style()

    def _refresh_style(self):
        self.light.style().unpolish(self.light)
        self.light.style().polish(self.light)
        self.label.style().unpolish(self.label)
        self.label.style().polish(self.label)
        self.status_lbl.style().unpolish(self.status_lbl)
        self.status_lbl.style().polish(self.status_lbl)


class SentinelPCBox(QFrame):
    WIDTH, HEIGHT = 100, 90

    def __init__(self, pc_name):
        super().__init__()
        self.setFixedSize(self.WIDTH, self.HEIGHT)
        self.setProperty("class", "pc-box")

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(4, 10, 4, 8)

        # --- Icon Label ---
        self.icon_lbl = QLabel()
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        self.icon_lbl.setFixedHeight(32)

        # Load as QIcon first
        icon_on_vec = QIcon(":/icons/pc_on")
        icon_off_vec = QIcon(":/icons/pc_off")

        target_size = 28
        self.icon_on = icon_on_vec.pixmap(target_size, target_size)
        self.icon_off = icon_off_vec.pixmap(target_size, target_size)

        self.name_lbl = QLabel(pc_name)
        self.name_lbl.setAlignment(Qt.AlignCenter)
        self.name_lbl.setProperty("class", "pc-name")

        self.status_lbl = QLabel("OFFLINE")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setProperty("class", "pc-status")

        # Add widgets to layout
        self.layout.addWidget(self.icon_lbl)
        self.layout.addWidget(self.name_lbl)
        self.layout.addWidget(self.status_lbl)

        self.set_offline()

    def set_active(self):
        self.setProperty("state", "online")
        self.name_lbl.setProperty("state", "online")
        self.status_lbl.setProperty("state", "online")
        self.status_lbl.setText("ACTIVE")
        self.icon_lbl.setPixmap(self.icon_on)
        self._refresh_style()

    def set_offline(self):
        self.setProperty("state", "offline")
        self.name_lbl.setProperty("state", "offline")
        self.status_lbl.setProperty("state", "offline")
        self.status_lbl.setText("OFFLINE")
        self.icon_lbl.setPixmap(self.icon_off)
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
