from PySide6.QtCore import QObject, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QProgressBar, QVBoxLayout, QWidget, QLabel, QHBoxLayout
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QColor, QLinearGradient


class AnimatedProgressBar(QProgressBar):
    """Custom progress bar with smooth animations and better styling"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_style()
        self.setup_animation()
    
    def setup_style(self):
        """Setup modern progress bar styling"""
        self.setStyleSheet("""
            QProgressBar {
                border: 2px solid #555555;
                border-radius: 8px;
                background-color: #2b2b2b;
                text-align: center;
                color: white;
                font-weight: bold;
                font-size: 12px;
                min-height: 25px;
            }
            
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4a90e2, stop:0.5 #5ba3f5, stop:1 #4a90e2);
                border-radius: 6px;
                margin: 1px;
            }
            
            QProgressBar::chunk:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5ba3f5, stop:0.5 #6bb4ff, stop:1 #5ba3f5);
            }
        """)
    
    def setup_animation(self):
        """Setup smooth progress animations"""
        self.animation = QPropertyAnimation(self, b"value")
        self.animation.setDuration(300)  # 300ms animation
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def setValueAnimated(self, value):
        """Set progress value with smooth animation"""
        self.animation.setStartValue(self.value())
        self.animation.setEndValue(value)
        self.animation.start()


class ProgressBarWidget(QWidget):
    """Complete progress bar widget with label and status"""
    
    # Signals for progress updates
    progress_updated = Signal(int)  # progress value (0-100)
    status_updated = Signal(str)    # status text
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.connect_signals()
        
        # Progress tracking
        self.current_step = 0
        self.total_steps = 0
        self.step_progress = 0
    
    def setup_ui(self):
        """Setup the progress bar UI"""
        layout = QVBoxLayout(self)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
                margin: 5px;
            }
        """)
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = AnimatedProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Details label (for substep info)
        self.details_label = QLabel("")
        self.details_label.setAlignment(Qt.AlignCenter)
        self.details_label.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 11px;
                margin: 2px;
            }
        """)
        layout.addWidget(self.details_label)
        
        layout.setContentsMargins(10, 5, 10, 5)
    
    def connect_signals(self):
        """Connect internal signals"""
        self.progress_updated.connect(self._update_progress)
        self.status_updated.connect(self._update_status)
    
    def _update_progress(self, value):
        """Update progress bar value (thread-safe)"""
        self.progress_bar.setValueAnimated(max(0, min(100, value)))
    
    def _update_status(self, text):
        """Update status label (thread-safe)"""
        self.status_label.setText(text)
    
    def set_progress(self, value, status=None, details=None):
        """Set progress with optional status and details"""
        self.progress_updated.emit(value)
        
        if status:
            self.status_updated.emit(status)
        
        if details:
            self.details_label.setText(details)
    
    def set_indeterminate(self, active=True):
        """Set progress bar to indeterminate mode"""
        if active:
            self.progress_bar.setRange(0, 0)  # Indeterminate
        else:
            self.progress_bar.setRange(0, 100)  # Normal
    
    def start_multi_step(self, steps, initial_status="Starting..."):
        """Start a multi-step progress tracking"""
        self.total_steps = steps
        self.current_step = 0
        self.step_progress = 0
        self.set_progress(0, initial_status)
    
    def update_step(self, step_name, step_progress=0):
        """Update current step progress"""
        if self.total_steps == 0:
            return
        
        self.step_progress = max(0, min(100, step_progress))
        
        # Calculate overall progress
        step_weight = 100 / self.total_steps
        overall_progress = (self.current_step * step_weight) + (step_progress * step_weight / 100)
        
        self.set_progress(
            int(overall_progress),
            step_name,
            f"Step {self.current_step + 1}/{self.total_steps} - {step_progress}%"
        )
    
    def complete_step(self, next_step_name=None):
        """Mark current step as complete and move to next"""
        self.current_step += 1
        self.step_progress = 0
        
        if next_step_name and self.current_step < self.total_steps:
            self.update_step(next_step_name, 0)
        elif self.current_step >= self.total_steps:
            self.set_progress(100, "Completed!", "All steps finished")
    
    def reset(self):
        """Reset progress bar to initial state"""
        self.progress_bar.setValue(0)
        self.status_label.setText("Ready")
        self.details_label.setText("")
        self.current_step = 0
        self.total_steps = 0
        self.step_progress = 0
    
    def set_error(self, error_message):
        """Set error state"""
        self.progress_bar.setStyleSheet("""
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e74c3c, stop:0.5 #f39c12, stop:1 #e74c3c);
                border-radius: 6px;
                margin: 1px;
            }
        """)
        self.set_progress(self.progress_bar.value(), "Error", error_message)
        
        # Reset style after 3 seconds
        QTimer.singleShot(3000, self.setup_style)
