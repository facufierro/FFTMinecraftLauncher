# Simple main window component using PySide6
import logging
import time
from PySide6.QtCore import Signal, QTimer, Qt
from PySide6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget
from src.ui.components.launch_button import LaunchButton


class MainWindow(QMainWindow):
    launch_requested = Signal()  # Custom signal for launch requests

    def __init__(self):
        super().__init__()
        self.last_click_time = 0  # Track the last click time
        self.setWindowTitle("FFT Minecraft Launcher")
        self.setGeometry(100, 100, 600, 400)

        # Central widget and layout
        central_widget = QWidget(self)
        layout = QVBoxLayout()

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Add Launch button
        self.launch_button = LaunchButton("Launch", central_widget)
        self.launch_button.clicked.connect(self.on_launch_button_clicked)
        layout.addWidget(self.launch_button, alignment=Qt.AlignmentFlag.AlignCenter)
        logging.debug("MainWindow initialized")

    def on_launch_button_clicked(self):
        current_time = time.time()
        if (
            current_time - self.last_click_time > 0.5
        ):  # Debounce interval of 0.5 seconds
            logging.info("Launch button clicked")
            self.last_click_time = current_time
            self.launch_requested.emit()  # Emit the custom signal

    def resizeEvent(self, event):
        super().resizeEvent(event)
        central = self.centralWidget()
        if central is not None:
            w = central.width()
            h = central.height()
            x = w / 2
            y = h - (h / 3)
            self.launch_button.set_center(x, y)
