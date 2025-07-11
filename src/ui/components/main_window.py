# Simple main window component using PyQt6
from PyQt6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FFT Minecraft Launcher")
        self.setGeometry(100, 100, 600, 400)

        # Central widget and layout
        central_widget = QWidget()
        layout = QVBoxLayout()

        # Example label
        label = QLabel("Welcome to FFT Minecraft Launcher!")
        layout.addWidget(label)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
