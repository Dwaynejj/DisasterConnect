import os
from PyQt5.QtCore import (Qt, QTimer, pyqtSignal, QThread, QPropertyAnimation, 
                          QEasingCurve)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QProgressBar, 
                             QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QFrame)

try:
    from PyQt5.QtSvg import QSvgWidget
    HAS_SVG = True
except ImportError:
    HAS_SVG = False
    from PyQt5.QtGui import QPixmap

# We run main.py from the project root, so db should be in pythonpath
from db.connection import DatabaseConnection

class DatabasePingThread(QThread):
    result_signal = pyqtSignal(bool)

    def run(self):
        try:
            # Re-init or get the connection singleton
            db_conn = DatabaseConnection()
            db_conn.connect()
            self.result_signal.emit(True)
        except Exception:
            self.result_signal.emit(False)


class SplashScreen(QWidget):
    finished_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(520, 320) # 500x300 + 20px padding for shadow

        # ── Drop shadow setup ──
        self.shadow_effect = QGraphicsDropShadowEffect(self)
        self.shadow_effect.setBlurRadius(20)
        self.shadow_effect.setXOffset(0)
        self.shadow_effect.setYOffset(4)
        self.shadow_effect.setColor(QColor(0, 0, 0, 150))

        # ── Main container frame ──
        self.container = QFrame(self)
        self.container.setFixedSize(500, 300)
        self.container.move(10, 10)
        self.container.setGraphicsEffect(self.shadow_effect)
        self.container.setStyleSheet("""
            QFrame {
                background-color: #0D1117;
                border-radius: 12px;
            }
        """)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(40, 40, 40, 20)
        layout.setAlignment(Qt.AlignCenter)

        # ── Logo ──
        logo_svg = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                 'resources', 'images', 'logo.svg')
        logo_png = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                 'resources', 'images', 'logo_large.png')
        
        if HAS_SVG and os.path.exists(logo_svg):
            self.logo = QSvgWidget(logo_svg)
            self.logo.setFixedSize(80, 80)
            layout.addWidget(self.logo, alignment=Qt.AlignCenter)
        else:
            self.logo = QLabel()
            pix = QPixmap(logo_png)
            if not pix.isNull():
                self.logo.setPixmap(pix.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                self.logo.setText("🛡")
                self.logo.setStyleSheet("color: #1F6FEB; font-size: 40px;")
            layout.addWidget(self.logo, alignment=Qt.AlignCenter)
            
        layout.addSpacing(16)

        # ── Title ──
        self.title = QLabel("DisasterConnect")
        font = QFont("Segoe UI", 26, QFont.Bold)
        self.title.setFont(font)
        self.title.setStyleSheet("color: white; background: transparent; border: none;")
        layout.addWidget(self.title, alignment=Qt.AlignCenter)
        layout.addStretch()

        # ── Progress Bar ──
        self.progress = QProgressBar()
        self.progress.setFixedHeight(4)
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 0) # Indeterminate mode
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: #161B22;
                border: none;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #238636;
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.progress)
        layout.addSpacing(8)

        # ── Status Text ──
        self.status = QLabel("Connecting to database...")
        self.status.setFont(QFont("Segoe UI", 10))
        self.status.setStyleSheet("color: #8B9DC3; background: transparent; border: none;")
        layout.addWidget(self.status, alignment=Qt.AlignCenter)
        layout.addStretch()

        # ── Version ──
        self.version = QLabel("v1.0.0")
        self.version.setFont(QFont("Segoe UI", 8))
        self.version.setStyleSheet("color: #6C757D; background: transparent; border: none;")
        layout.addWidget(self.version, alignment=Qt.AlignCenter)

        # ── Logic Variables ──
        self._minimum_time_passed = False
        self._db_finished = False
        
        self.status_texts = [
            "Connecting to database...",
            "Loading configuration...",
            "Preparing interface...",
            "Ready!"
        ]
        self._status_idx = 0

        # Cycle texts timer
        self.text_timer = QTimer(self)
        self.text_timer.timeout.connect(self._cycle_text)
        self.text_timer.start(600)

        # Minimum time timer (2.5 seconds)
        QTimer.singleShot(2500, self._on_minimum_time_reached)

        # ── Opacity effect for fade out ──
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(1.0)

    def center_on_screen(self):
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2
        )

    def showEvent(self, event):
        super().showEvent(event)
        self.center_on_screen()
        # Start DB thread
        self.db_thread = DatabasePingThread()
        self.db_thread.result_signal.connect(self._on_db_result)
        self.db_thread.start()

    def _cycle_text(self):
        if self._db_finished:
            return
        self._status_idx = (self._status_idx + 1) % (len(self.status_texts) - 1)
        self.status.setText(self.status_texts[self._status_idx])

    def _on_db_result(self, success):
        self._db_finished = True
        if not success:
            self.progress.setStyleSheet("""
                QProgressBar {
                    background-color: #161B22;
                    border: none;
                    border-radius: 2px;
                }
                QProgressBar::chunk {
                    background-color: #F39C12;
                    border-radius: 2px;
                }
            """)
            self.status.setStyleSheet("color: #F39C12; background: transparent; border: none;")
            self.status.setText("Database unavailable — offline mode")
            # Wait 1 extra second before resolving
            QTimer.singleShot(1000, self._check_complete)
        else:
            self.status.setText("Ready!")
            self._check_complete()

    def _on_minimum_time_reached(self):
        self._minimum_time_passed = True
        self._check_complete()

    def _check_complete(self):
        if self._minimum_time_passed and self._db_finished:
            self.text_timer.stop()
            self._fade_out()

    def _fade_out(self):
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(300)
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.anim.finished.connect(self._finish)
        self.anim.start()

    def _finish(self):
        self.finished_signal.emit()
        self.close()
