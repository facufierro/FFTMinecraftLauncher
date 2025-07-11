# Simple LaunchButton component using PyQt6

from PyQt6.QtWidgets import QPushButton

class LaunchButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__("Launch", parent)
        self.setFixedSize(160, 80)
        self.center_x = 0
        self.center_y = 0

    def set_center(self, x, y):
        self.center_x = x
        self.center_y = y
        # Move the button so that its center is at (x, y)
        self.move(int(x - self.width() / 2), int(y - self.height() / 2))
