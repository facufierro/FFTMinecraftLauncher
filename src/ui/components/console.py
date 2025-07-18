import logging
from PySide6.QtCore import QObject, Signal, QMutex, QMutexLocker
from PySide6.QtWidgets import QPlainTextEdit, QVBoxLayout, QWidget, QScrollBar
from PySide6.QtGui import QTextCursor, QFont
from PySide6.QtCore import Qt


class ConsoleHandler(logging.Handler):
    """Custom logging handler that sends log messages to a console widget"""
    
    def __init__(self, console_widget):
        super().__init__()
        self.console_widget = console_widget
        self.mutex = QMutex()
        
        # Set formatter
        formatter = logging.Formatter('[%(levelname)s] [%(asctime)s]: %(message)s', '%H:%M:%S')
        self.setFormatter(formatter)
    
    def emit(self, record):
        """Emit a log record to the console widget"""
        try:
            with QMutexLocker(self.mutex):
                msg = self.format(record)
                # Use signal to ensure thread safety
                self.console_widget.append_message.emit(msg, record.levelname)
        except Exception:
            self.handleError(record)


class ConsoleWidget(QWidget):
    """Console widget for displaying log messages with real-time updates"""
    
    append_message = Signal(str, str)  # message, level
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_logging()
        
        # Connect signal to slot for thread-safe message appending
        self.append_message.connect(self._append_message_safe)
    
    def setup_ui(self):
        """Setup the console UI"""
        layout = QVBoxLayout(self)
        
        # Create text edit for console output
        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setMaximumBlockCount(1000)  # Limit to 1000 lines
        
        # Set font to monospace for better readability
        font = QFont("Consolas", 9)
        if not font.exactMatch():
            font = QFont("Courier New", 9)
        self.text_edit.setFont(font)
        
        # Dark theme styling
        self.text_edit.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #444444;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        
        layout.addWidget(self.text_edit)
        layout.setContentsMargins(0, 0, 0, 0)
    
    def setup_logging(self):
        """Setup logging handler for this console"""
        self.handler = ConsoleHandler(self)
        self.handler.setLevel(logging.DEBUG)
        
        # Add handler to root logger
        logging.getLogger().addHandler(self.handler)
    
    def _append_message_safe(self, message, level):
        """Thread-safe method to append messages to console"""
        # Color code based on log level
        color_map = {
            'DEBUG': '#888888',
            'INFO': '#ffffff', 
            'WARNING': '#ffaa00',
            'ERROR': '#ff4444',
            'CRITICAL': '#ff0000'
        }
        
        color = color_map.get(level, '#ffffff')
        
        # Move cursor to end and insert colored text
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertHtml(f'<span style="color: {color};">{message}</span><br>')
        
        # Auto-scroll to bottom
        self.text_edit.ensureCursorVisible()
    
    def clear_console(self):
        """Clear all console content"""
        self.text_edit.clear()
    
    def save_log(self, filename):
        """Save console content to file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.text_edit.toPlainText())
            logging.info(f"Console log saved to {filename}")
        except Exception as e:
            logging.error(f"Failed to save log: {e}")
    
    def closeEvent(self, event):
        """Cleanup when widget is closed"""
        if hasattr(self, 'handler'):
            logging.getLogger().removeHandler(self.handler)
        super().closeEvent(event)
