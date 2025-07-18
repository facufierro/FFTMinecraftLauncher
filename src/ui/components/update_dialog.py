import logging
import sys
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import pyqtSignal


class UpdateDialog(QDialog):
    accept_pressed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Update Available")
        layout = QVBoxLayout()
        self.label = QLabel("An update is available.")
        layout.addWidget(self.label)
        self.accept_button = QPushButton("Accept")
        layout.addWidget(self.accept_button)
        self.accept_button.clicked.connect(self.on_accept_pressed)
        self.setLayout(layout)

    def on_accept_pressed(self):
        self.accept_pressed.emit()
        logging.info("Exiting launcher...")
        sys.exit()
