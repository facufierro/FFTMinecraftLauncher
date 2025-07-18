from PySide6.QtCore import QPropertyAnimation
from PySide6.QtWidgets import QPushButton

class LaunchButton(QPushButton):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(
            "background-color: #7289DA; color: white; border-radius: 15px; font-size: 18px; padding: 15px;"
        )
        self.setFixedSize(200, 50)
        self.animation = QPropertyAnimation(self, b"geometry")

    def enterEvent(self, event):
        self.setStyleSheet(
            "background-color: #99AAB5; color: white; border-radius: 15px; font-size: 18px; padding: 15px;"
        )
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(
            "background-color: #7289DA; color: white; border-radius: 15px; font-size: 18px; padding: 15px;"
        )
        super().leaveEvent(event)

    def set_center(self, x: float, y: float):
        self.move(int(x - self.width() / 2), int(y - self.height() / 2))