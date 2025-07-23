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
    def on_launch_button_clicked(self, callback):
        """Set the callback to be called when the launch button is clicked."""
        self._launch_callback = callback
    launch_requested = Signal()  # Custom signal for launch requests

    def __init__(self):
        super().__init__()
        self.last_click_time = 0
        self._launch_callback = None
        self.setWindowTitle("FFT Minecraft Launcher")
        self.setGeometry(100, 100, 900, 540)

        # Central widget and main layout
        central_widget = QWidget(self)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Info cards row
        info_row = QHBoxLayout()
        info_row.setSpacing(8)
        for label, value in [
            ("Local Directory", "Instance: FFTClient"),
            ("Last Check", "2025-07-06 18:42:34"),
            ("Current Version", "1.2.93")
        ]:
            card = QFrame()
            card.setFrameShape(QFrame.StyledPanel)
            card.setFrameShadow(QFrame.Raised)
            card.setStyleSheet("background-color: #23272e; border-radius: 8px; padding: 8px 12px;")
            v = QVBoxLayout(card)
            v.setContentsMargins(4, 4, 4, 4)
            v.setSpacing(2)
            l1 = QLabel(f"<span style='color:#aaa;font-size:11px;'>{label}</span>")
            l2 = QLabel(f"<b style='font-size:13px;'>{value}</b>")
            l2.setStyleSheet("color:#fff;")
            v.addWidget(l1)
            v.addWidget(l2)
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            info_row.addWidget(card)
        main_layout.addLayout(info_row)

        # Progress/status area (no label, more compact)
        progress_card = QFrame()
        progress_card.setFrameShape(QFrame.StyledPanel)
        progress_card.setFrameShadow(QFrame.Raised)
        progress_card.setStyleSheet("background-color: #23272e; border-radius: 8px; padding: 0px 0px;")
        progress_layout = QVBoxLayout(progress_card)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(0)
        self.progress_bar = ProgressBarWidget()
        self.progress_bar.setMinimumHeight(22)
        self.progress_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.progress_bar.setStyleSheet('QProgressBar { background-color: #23272e; border-radius: 8px; border: 1px solid #444a57; min-height: 22px; } QProgressBar::chunk { background-color: #6c7cff; border-radius: 8px; }')
        progress_layout.addWidget(self.progress_bar)
        main_layout.addWidget(progress_card)

        # Launch button area (moved directly above console)
        launch_area = QVBoxLayout()
        launch_area.setAlignment(Qt.AlignHCenter)
        self.launch_button = LaunchButton("Launch", self)
        self.launch_button.setMinimumHeight(54)
        self.launch_button.setMinimumWidth(200)
        self.launch_button.setStyleSheet(
            "QPushButton {"
            "background-color: #444aee;"
            "color: #fff;"
            "border: none;"
            "border-radius: 10px;"
            "font-size: 15px;"
            "font-weight: bold;"
            "padding: 8px 0;"
            "}"
            "QPushButton:hover {"
            "background-color: #357ae8;"
            "}"
            "QPushButton:disabled {"
            "background-color: #888;"
            "color: #ccc;"
            "}"
        )
        self.launch_button.clicked.connect(self._handle_launch_button_click)
        launch_area.addWidget(self.launch_button, alignment=Qt.AlignHCenter)
        main_layout.addLayout(launch_area)

        # Console area
        self.console_card = QFrame()
        self.console_card.setFrameShape(QFrame.StyledPanel)
        self.console_card.setFrameShadow(QFrame.Raised)
        self.console_card.setStyleSheet("background-color: #181a1b; border-radius: 8px; padding: 6px 8px;")
        self.console_layout = QVBoxLayout(self.console_card)
        self.console_layout.setContentsMargins(4, 4, 4, 4)
        self.console_layout.setSpacing(2)
        self.console_label_row = QHBoxLayout()
        self.console_label = QLabel("<b>Activity Console</b>")
        self.console_label.setStyleSheet("color:#bfcfff;font-size:12px;")
        self.console_label_row.addWidget(self.console_label)
        self.console_label_row.addStretch()
        self.console_clear_btn = QPushButton("Clear")
        self.console_clear_btn.setStyleSheet(
            "QPushButton {"
            "background-color: #23272e;"
            "color: #bfcfff;"
            "border: 1px solid #444a57;"
            "border-radius: 6px;"
            "font-size: 11px;"
            "padding: 2px 10px;"
            "}"
            "QPushButton:hover {"
            "background-color: #2e3240;"
            "}"
        )
        self.console_label_row.addWidget(self.console_clear_btn)
        self.console_layout.addLayout(self.console_label_row)
        self.console = ConsoleWidget()
        self.console.setMinimumHeight(220)
        self.console_layout.addWidget(self.console)
        main_layout.addWidget(self.console_card)
        # Removed stray __init__ method and associated code

    def _handle_launch_button_click(self):
        """Handle the launch button click event."""
        # If you have a launch callback, call it; otherwise, emit the launch_requested signal
        if self._launch_callback:
            self._launch_callback()
        else:
            self.launch_requested.emit()
