# handle launcher operations
from PyQt6.QtWidgets import QApplication
from src.ui.components.main_window import MainWindow
import sys

def run_launcher():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
