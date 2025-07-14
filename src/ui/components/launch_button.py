# Simple LaunchButton component using PyQt6

from PyQt6.QtWidgets import QPushButton


class LaunchButton(QPushButton):
    def __init__(self, parent=None, color="#4CAF50", label="Launch"):
        super().__init__(label, parent)
        self.setFixedSize(160, 80)
        self.center_x = 0
        self.center_y = 0
        self.color = color
        self.label = label
        self.set_color(self.color)

    def set_label(self, label):
        self.label = label
        self.setText(label)

    def set_color(self, color):
        self.color = color
        self.setStyleSheet(f"background-color: {self.color}; color: white; border-radius: 10px; font-size: 18px;")

    def set_center(self, x, y):
        self.center_x = x
        self.center_y = y
        # Move the button so that its center is at (x, y)
        self.move(int(x - self.width() / 2), int(y - self.height() / 2))
