# Simple main window component using PyQt6
from PyQt6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget
from src.ui.components.launch_button import LaunchButton


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FFT Minecraft Launcher")
        self.setGeometry(100, 100, 600, 400)

        # Central widget and layout
        central_widget = QWidget(self)
        layout = QVBoxLayout()

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Add Launch button and position it
        self.launch_button = LaunchButton(central_widget)
        self.launch_button.show()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        central = self.centralWidget()
        if central is not None:
            w = central.width()
            h = central.height()
            x = w / 2
            y = h - (h / 3)
            self.launch_button.set_center(x, y)
