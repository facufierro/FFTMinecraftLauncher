import logging
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton


class MainWindow(QMainWindow):
    launch_requested = pyqtSignal()  # Custom signal for launch requests

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
        self.launch_button = QPushButton(
            "Launch", central_widget
        )  # Assuming LaunchButton is QPushButton
        self.launch_button.clicked.connect(
            self.on_launch_button_clicked
        )  # Connect button click to method
        layout.addWidget(self.launch_button)

    def on_launch_button_clicked(self):
        logging.info("Launch button clicked")
        self.launch_requested.emit()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        central = self.centralWidget()
        if central is not None:
            w = central.width()
            h = central.height()
            x = w / 2
            y = h - (h / 3)
            self.launch_button.move(int(x), int(y))
