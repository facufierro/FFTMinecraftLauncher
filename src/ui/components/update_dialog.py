import logging
import sys
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy


class UpdateDialog(QDialog):
    accept_pressed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Update Available")
        self.setStyleSheet("background-color: #2C2F33; color: #FFFFFF;")
        self.setFixedSize(400, 200)

        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Add a title label
        self.title_label = QLabel("Update Available", self)
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold; text-align: center;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

        # Add a description label
        self.description_label = QLabel("A new update is ready to install.", self)
        self.description_label.setStyleSheet("font-size: 16px; text-align: center;")
        self.description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.description_label)

        # Add spacer above the button
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Add Accept button
        self.accept_button = QPushButton("Accept Update", self)
        self.accept_button.setStyleSheet(
            "background-color: #7289DA; color: white; border-radius: 15px; font-size: 16px; padding: 10px;"
        )
        self.accept_button.clicked.connect(self.on_accept_pressed)
        layout.addWidget(self.accept_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Add spacer below the button
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.setLayout(layout)

    def on_accept_pressed(self):
        self.accept_pressed.emit()
        logging.info("Exiting launcher...")
        sys.exit()
