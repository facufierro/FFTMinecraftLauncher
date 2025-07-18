# Simple main window component using PyQt6
import logging
from PySide6.QtCore import Signal, Qt, QPropertyAnimation
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QSpacerItem, QSizePolicy


class AnimatedButton(QPushButton):
    def __init__(self, text, parent=None):
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


class MainWindow(QMainWindow):
    launch_requested = Signal()  # Custom signal for launch requests

    def __init__(self):
        super().__init__()
        self.setWindowTitle("FFT Minecraft Launcher")
        self.setGeometry(100, 100, 600, 400)
        self.setStyleSheet("background-color: #2C2F33; color: #FFFFFF;")

        # Central widget and layout
        central_widget = QWidget(self)
        layout = QVBoxLayout()
        layout.setSpacing(30)
        layout.setContentsMargins(40, 40, 40, 40)

        # Add a title label
        self.title_label = QLabel("FFT Minecraft Launcher", central_widget)
        self.title_label.setStyleSheet("font-size: 28px; font-weight: bold; text-align: center;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

        # Add a tagline label
        self.tagline_label = QLabel("Launch your Minecraft journey effortlessly", central_widget)
        self.tagline_label.setStyleSheet("font-size: 16px; font-style: italic; text-align: center;")
        self.tagline_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.tagline_label)

        # Add spacer above the button
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Add animated Launch button
        self.launch_button = AnimatedButton("Launch Minecraft", central_widget)
        self.launch_button.clicked.connect(self.on_launch_button_clicked)
        layout.addWidget(self.launch_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Add spacer below the button
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        logging.debug("MainWindow initialized")

    def on_launch_button_clicked(self):
        logging.info("Launch button clicked")
        self.launch_requested.emit()  # Emit the custom signal
