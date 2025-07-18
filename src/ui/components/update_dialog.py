import logging
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton


class UpdateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Update Available")
        layout = QVBoxLayout()
        self.label = QLabel("An update is available.")
        layout.addWidget(self.label)
        self.accept_button = QPushButton("Accept")
        layout.addWidget(self.accept_button)
        self.setLayout(layout)
