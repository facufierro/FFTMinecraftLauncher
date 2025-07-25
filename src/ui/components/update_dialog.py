import logging
import sys
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Signal


class UpdateDialog(QDialog):
    accept_pressed = Signal()

    def __init__(self, parent=None, label_text="An update is needed."):
        super().__init__(parent)
        self.setWindowTitle("Update Needed")
        layout = QVBoxLayout()
        self.label = QLabel(label_text)
        layout.addWidget(self.label)
        self.accept_button = QPushButton("Accept")
        layout.addWidget(self.accept_button)
        self.accept_button.clicked.connect(self.on_accept_pressed)
        self.setLayout(layout)

    def on_accept_pressed(self):
        self.accept_pressed.emit()
        logging.info("Exiting launcher...")
        sys.exit()
