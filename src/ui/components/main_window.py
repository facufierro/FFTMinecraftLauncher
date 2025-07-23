# Simple main window component using PySide6
import logging
import time
from PySide6.QtCore import Signal, QTimer, Qt
from PySide6.QtWidgets import (
    QMainWindow, QLabel, QVBoxLayout, QWidget, QHBoxLayout, QSplitter, QFrame, QPushButton, QCheckBox, QSizePolicy
)
from PySide6.QtGui import QPixmap, QFont
from src.ui.components.launch_button import LaunchButton
from src.ui.components.console import ConsoleWidget
from src.ui.components.progress_bar import ProgressBarWidget


class MainWindow(QMainWindow):
    launch_requested = Signal()  # Custom signal for launch requests

    def __init__(self):
        super().__init__()
        self.last_click_time = 0
        self._launch_callback = None
        self.setWindowTitle("FFT Minecraft Launcher")
        self.setGeometry(100, 100, 1000, 700)

        # Central widget and main layout
        central_widget = QWidget(self)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Header/title
        title = QLabel("FFT Minecraft Modpack Launcher")
        title.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setStyleSheet("color: #fff; margin-bottom: 8px;")
        main_layout.addWidget(title)

        # Info cards row
        info_row = QHBoxLayout()
        info_row.setSpacing(16)
        for label, value in [
            ("Local Directory", "Instance: FFTClient"),
            ("Last Check", "2025-07-06 18:42:34"),
            ("Current Version", "1.2.93")
        ]:
            card = QFrame()
            card.setFrameShape(QFrame.StyledPanel)
            card.setFrameShadow(QFrame.Raised)
            card.setStyleSheet("background-color: #23272e; border-radius: 12px; padding: 18px;")
            v = QVBoxLayout(card)
            icon = QLabel()
            icon.setFixedHeight(24)
            icon.setFixedWidth(24)
            # You can add icons here if you want
            v.addWidget(icon)
            l1 = QLabel(f"<span style='color:#aaa;font-size:13px;'>{label}</span>")
            l2 = QLabel(f"<b style='font-size:16px;'>{value}</b>")
            l2.setStyleSheet("color:#fff;")
            v.addWidget(l1)
            v.addWidget(l2)
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            info_row.addWidget(card)
        main_layout.addLayout(info_row)

        # Progress/status area
        progress_card = QFrame()
        progress_card.setFrameShape(QFrame.StyledPanel)
        progress_card.setFrameShadow(QFrame.Raised)
        progress_card.setStyleSheet("background-color: #23272e; border-radius: 12px; padding: 18px;")
        progress_layout = QVBoxLayout(progress_card)
        progress_label = QLabel("<b>Checking if files have changed...</b>")
        progress_label.setStyleSheet("color:#bfcfff;font-size:15px;")
        progress_layout.addWidget(progress_label)
        self.progress_bar = ProgressBarWidget()
        progress_layout.addWidget(self.progress_bar)
        main_layout.addWidget(progress_card)

        # Launch button area
        launch_area = QVBoxLayout()
        launch_area.setAlignment(Qt.AlignHCenter)
        self.launch_button = LaunchButton("Launch", self)
        self.launch_button.setMinimumHeight(56)
        self.launch_button.setMinimumWidth(220)
        self.launch_button.setStyleSheet('''
            QPushButton {
                background-color: #444aee;
                color: #fff;
                border: none;
                border-radius: 16px;
                font-size: 22px;
                font-weight: bold;
                padding: 16px 0;
            }
            QPushButton:hover {
                background-color: #357ae8;
            }
            QPushButton:disabled {
                background-color: #888;
                color: #ccc;
            }
        ''')
        self.launch_button.clicked.connect(self._handle_launch_button_click)
        launch_area.addWidget(self.launch_button, alignment=Qt.AlignHCenter)
        # Launch after update toggle
        self.launch_after_update = QCheckBox("Launch After Update")
        self.launch_after_update.setStyleSheet('''
            QCheckBox {
                color: #ccc;
                font-size: 14px;
                padding-left: 8px;
            }
        ''')
        launch_area.addWidget(self.launch_after_update, alignment=Qt.AlignHCenter)
        main_layout.addLayout(launch_area)

        # Console area
        console_card = QFrame()
        console_card.setFrameShape(QFrame.StyledPanel)
        console_card.setFrameShadow(QFrame.Raised)
        console_card.setStyleSheet("background-color: #181a1b; border-radius: 12px; padding: 12px;")
        console_layout = QVBoxLayout(console_card)
        console_label_row = QHBoxLayout()
        console_label = QLabel("<b>Activity Console</b>")
        console_label.setStyleSheet("color:#bfcfff;font-size:15px;")
        console_label_row.addWidget(console_label)
        console_label_row.addStretch()
        self.console_clear_btn = QPushButton("Clear")
        self.console_clear_btn.setStyleSheet('''
            QPushButton {
                background-color: #23272e;
                color: #bfcfff;
                border: 1px solid #444a57;
                border-radius: 8px;
                font-size: 13px;
                padding: 4px 16px;
            }
            QPushButton:hover {
                background-color: #2e3240;
            }
        ''')
        console_label_row.addWidget(self.console_clear_btn)
        console_layout.addLayout(console_label_row)
        self.console = ConsoleWidget()
        console_layout.addWidget(self.console)
        main_layout.addWidget(console_card)

        # Modern dark theme
        self.setStyleSheet('''
            QMainWindow {
                background-color: #181a1b;
            }
            QWidget {
                background-color: #181a1b;
                color: #f3f3f3;
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 15px;
            }
        ''')

    def on_launch_button_clicked(self, callback=None):
        """
        Set a callback to be called when the launch button is clicked.
        If called with no arguments, triggers the click handler (for backward compatibility).
        """
        if callback is not None:
            self._launch_callback = callback
        else:
            self._handle_launch_button_click()

    def _handle_launch_button_click(self):
        current_time = time.time()
        if current_time - self.last_click_time > 0.5:
            self.last_click_time = current_time
            if self._launch_callback:
                self._launch_callback()
            self.launch_requested.emit()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # The layout will handle the resizing automatically now
