# Simple main window component using PySide6
import logging
import time
from PySide6.QtCore import Signal, QTimer, Qt
from PySide6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget, QHBoxLayout, QSplitter
from src.ui.components.launch_button import LaunchButton
from src.ui.components.console import ConsoleWidget
from src.ui.components.progress_bar import ProgressBarWidget


class MainWindow(QMainWindow):
    launch_requested = Signal()  # Custom signal for launch requests

    def __init__(self):
        super().__init__()
        self.last_click_time = 0  # Track the last click time
        self._launch_callback = None  # Store the callback function
        self.setWindowTitle("FFT Minecraft Launcher")
        self.setGeometry(100, 100, 900, 600)  # Larger window for console

        # Central widget and main layout
        central_widget = QWidget(self)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Launch controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Add Launch button
        self.launch_button = LaunchButton("Launch", left_panel)
        self.launch_button.clicked.connect(self._handle_launch_button_click)
        left_layout.addWidget(self.launch_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Progress bar
        self.progress_bar = ProgressBarWidget()
        left_layout.addWidget(self.progress_bar)
        
        # Add stretch to push button to center
        left_layout.addStretch()
        
        # Right panel - Console
        self.console = ConsoleWidget()
        
        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(self.console)
        
        # Set initial splitter sizes (40% left, 60% right)
        splitter.setSizes([360, 540])
        
        # Add splitter to main layout
        main_layout.addWidget(splitter)
        
        # Set dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
            }
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QSplitter::handle {
                background-color: #555555;
                width: 2px;
            }
            QSplitter::handle:hover {
                background-color: #777777;
            }
        """)

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
