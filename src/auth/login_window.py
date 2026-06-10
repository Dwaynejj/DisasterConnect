"""
DisasterConnect — Login Window (redesigned)

Two-column layout: dark branding panel (left 40%) + clean form panel (right 60%).
Fixed at 900 × 580 px, centred on screen.
"""
from __future__ import annotations

import logging
import os

from PyQt5.QtCore import (
    QEasingCurve, QPoint, QPropertyAnimation, QSequentialAnimationGroup,
    Qt, QTimer, pyqtSignal, QThread
)
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QCheckBox, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QPushButton, QSizePolicy, QVBoxLayout, QWidget,
)

logger = logging.getLogger(__name__)


class AuthWorker(QThread):
    finished = pyqtSignal(bool, object, object)  # success, token/msg, user_dict/None

    def __init__(self, auth_manager, username, password):
        super().__init__()
        self.auth_manager = auth_manager
        self.username = username
        self.password = password

    def run(self):
        try:
            if self.auth_manager is not None:
                success, token_or_err, user_dict = self.auth_manager.login(self.username, self.password)
                self.finished.emit(success, token_or_err, user_dict)
            else:
                self.finished.emit(True, "dev_token", {"username": self.username, "role": "admin"})
        except Exception as exc:
            logger.error(f"Auth worker error: {exc}")
            self.finished.emit(False, str(exc), None)


class LoginWindow(QMainWindow):
    """Login window — 900 × 580, two-column layout."""

    # ── Signal ───────────────────────────────────────────────────────────────
    login_successful = pyqtSignal(dict)

    # ── Colour palette ────────────────────────────────────────────────────────
    C_LEFT_BG       = "#0D1117"
    C_RIGHT_BG      = "#FFFFFF"
    C_HEADING       = "#1A1A2E"
    C_SUBTEXT       = "#6C757D"
    C_TAGLINE       = "#8B9DC3"
    C_PRIMARY       = "#1F6FEB"
    C_PRIMARY_HOVER = "#1558C0"
    C_PRIMARY_DIS   = "#8DB4F5"
    C_ERROR         = "#DC3545"
    C_BULLET_1      = "#FF6B6B"
    C_BULLET_2      = "#4ECDC4"
    C_BULLET_3      = "#45B7D1"
    C_DIVIDER       = "#DEE2E6"
    C_BORDER        = "#DEE2E6"
    C_FOCUS         = "#1F6FEB"
    C_WHITE         = "#FFFFFF"
    C_LINK          = "#1F6FEB"
    C_INPUT_BG      = "#FAFAFA"
    C_INPUT_DIS     = "#F1F3F5"

    # ── Typography ────────────────────────────────────────────────────────────
    FONT_FAMILY = "Segoe UI"
    PT_APP_NAME = 28
    PT_TAGLINE  = 11
    PT_HEADING  = 22
    PT_SUBTEXT  = 11
    PT_LABEL    = 10
    PT_INPUT    = 11
    PT_BTN      = 12
    PT_SMALL    = 10

    # ── Spinner frames (Braille-dot, renders without any extra font) ──────────
    _SPINNER = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, auth_manager=None) -> None:
        super().__init__()
        self.auth_manager = auth_manager
        self._authenticating = False
        self._spinner_idx = 0
        self._spinner_timer = QTimer(self)
        self._spinner_timer.setInterval(80)
        self._spinner_timer.timeout.connect(self._tick_spinner)

        self._setup_window()
        self._setup_styles()
        self._build_ui()

    # ─────────────────────────────── helpers ─────────────────────────────────

    @staticmethod
    def _font(family: str, pt: int, bold: bool = False,
              italic: bool = False) -> QFont:
        f = QFont(family, pt)
        f.setBold(bold)
        f.setItalic(italic)
        return f

    def _resources_dir(self) -> str:
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "resources",
        )

    # ─────────────────────────── window setup ────────────────────────────────

    def _setup_window(self) -> None:
        self.setWindowTitle("DisasterConnect — Sign In")
        self.setFixedSize(900, 580)

        icon_path = os.path.join(self._resources_dir(), "images", "logo_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        screen = QApplication.primaryScreen().availableGeometry()
        self.move(
            (screen.width()  - 900) // 2,
            (screen.height() - 580) // 2,
        )

    def _setup_styles(self) -> None:
        """Shield the login window from the intrusive global stylesheet."""
        self.setStyleSheet(f"""
            /* Reset globally applied QFrame/QLabel borders and margins */
            QFrame, QLabel {{
                border: none;
                margin: 0;
                padding: 0;
                background: transparent;
            }}
            /* Specific overrides for inputs and buttons to drop global paddings */
            QLineEdit {{ margin: 0; }}
            QPushButton {{ margin: 0; min-width: 0; }}
            QCheckBox {{ margin: 0; padding: 0; }}
        """)

    # ─────────────────────────────── build UI ────────────────────────────────

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        h = QHBoxLayout(root)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)
        
        h.addWidget(self._build_left_panel(),  stretch=45)
        h.addWidget(self._build_right_panel(), stretch=55)

    # ── LEFT PANEL ────────────────────────────────────────────────────────────

    def _build_left_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("LeftPanel")
        panel.setStyleSheet(f"QFrame#LeftPanel {{ background-color: {self.C_LEFT_BG}; }}")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(0)

        # Top stretch to vertically center the content
        layout.addStretch()

        # Logo
        logo_lbl = QLabel()
        logo_svg = os.path.join(self._resources_dir(), "images", "logo.svg")
        logo_png = os.path.join(self._resources_dir(), "images", "logo_large.png")
        pix = QPixmap(logo_svg if os.path.exists(logo_svg) else logo_png)
        if not pix.isNull():
            logo_lbl.setPixmap(
                pix.scaled(68, 68, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        else:
            logo_lbl.setText("🛡")
            logo_lbl.setFont(self._font(self.FONT_FAMILY, 34))
            logo_lbl.setStyleSheet(f"color: {self.C_PRIMARY};")
        logo_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_lbl)
        layout.addSpacing(22)

        # App name
        name_lbl = QLabel("DisasterConnect")
        name_lbl.setFont(self._font(self.FONT_FAMILY, self.PT_APP_NAME, bold=True))
        name_lbl.setStyleSheet(f"color: {self.C_WHITE}; background: transparent;")
        name_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(name_lbl)
        layout.addSpacing(10)

        # Tagline
        tag_lbl = QLabel("Coordinate. Respond. Recover.")
        tag_lbl.setFont(self._font(self.FONT_FAMILY, self.PT_TAGLINE, italic=True))
        tag_lbl.setStyleSheet(f"color: {self.C_TAGLINE}; background: transparent;")
        tag_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(tag_lbl)
        layout.addSpacing(52)

        # Bullet features
        bullets = [
            (self.C_BULLET_1, "Real-time Incident Tracking"),
            (self.C_BULLET_2, "Resource Coordination"),
            (self.C_BULLET_3, "Team Communication"),
        ]
        
        # Container to center the bullets as a block
        bullets_container = QWidget()
        bullets_layout = QVBoxLayout(bullets_container)
        bullets_layout.setContentsMargins(0, 0, 0, 0)
        bullets_layout.setSpacing(18)
        
        for color, text in bullets:
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(14)

            dot = QLabel("●")
            dot.setFont(self._font(self.FONT_FAMILY, 13))
            dot.setStyleSheet(f"color: {color}; background: transparent;")
            dot.setFixedWidth(16)

            txt = QLabel(text)
            txt.setFont(self._font(self.FONT_FAMILY, 11))
            txt.setStyleSheet(f"color: {self.C_WHITE}; background: transparent;")

            row.addWidget(dot)
            row.addWidget(txt)
            row.addStretch()
            bullets_layout.addLayout(row)

        # Add the bullets container centered horizontally
        h_center = QHBoxLayout()
        h_center.addStretch()
        h_center.addWidget(bullets_container)
        h_center.addStretch()
        layout.addLayout(h_center)

        layout.addStretch()
        return panel

    # ── RIGHT PANEL ───────────────────────────────────────────────────────────

    def _build_right_panel(self) -> QWidget:
        from PyQt5.QtWidgets import QGridLayout
        panel = QFrame()
        panel.setObjectName("RightPanel")
        
        # Add a subtle watermark or gradient to ensure the whitespace "has something doing"
        # We use a radial gradient to give the right panel a very subtle depth
        panel.setStyleSheet(f"""
            QFrame#RightPanel {{
                background-color: {self.C_RIGHT_BG};
                background: qradialgradient(cx: 0.5, cy: 0.5, radius: 0.8,
                                            fx: 0.5, fy: 0.5,
                                            stop: 0 #FFFFFF, stop: 1 #F0F4F8);
            }}
        """)

        # Use grid layout for perfect centering
        grid = QGridLayout(panel)
        grid.setContentsMargins(0, 0, 0, 0)

        # Animatable form container
        self._form_widget = QWidget()
        self._form_widget.setFixedWidth(380) # Slightly wider
        self._form_widget.setSizePolicy(
            QSizePolicy.Fixed, QSizePolicy.Preferred
        )

        form = QVBoxLayout(self._form_widget)
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(0)

        # ── Heading ──
        heading = QLabel("Welcome Back")
        heading.setFont(self._font(self.FONT_FAMILY, self.PT_HEADING, bold=True))
        heading.setStyleSheet(f"color: {self.C_HEADING};")
        heading.setAlignment(Qt.AlignCenter)
        form.addWidget(heading)
        form.addSpacing(6)

        sub = QLabel("Sign in to your account")
        sub.setFont(self._font(self.FONT_FAMILY, self.PT_SUBTEXT))
        sub.setStyleSheet(f"color: {self.C_SUBTEXT};")
        sub.setAlignment(Qt.AlignCenter)
        form.addWidget(sub)
        form.addSpacing(35)

        # ── Username ──
        form.addWidget(self._field_label("Username"))
        form.addSpacing(6)
        self._username_input = self._make_input("Email or Username")
        form.addWidget(self._username_input)
        form.addSpacing(16)

        # ── Password row (input + eye button) ──
        form.addWidget(self._field_label("Password"))
        form.addSpacing(6)

        # Wrapper frame so the border perfectly encapsulates both the input and the button
        self._pass_frame = QFrame()
        self._pass_frame.setObjectName("PassFrame")
        self._pass_frame.setFixedHeight(44)
        self._pass_frame.setStyleSheet(f"""
            QFrame#PassFrame {{
                background: {self.C_INPUT_BG};
                border: 1.5px solid {self.C_BORDER};
                border-radius: 6px;
            }}
        """)
        pass_row = QHBoxLayout(self._pass_frame)
        pass_row.setContentsMargins(0, 0, 0, 0)
        pass_row.setSpacing(0)

        self._password_input = QLineEdit()
        self._password_input.setPlaceholderText("Password")
        self._password_input.setEchoMode(QLineEdit.Password)
        self._password_input.setFont(self._font(self.FONT_FAMILY, self.PT_INPUT))
        self._password_input.setStyleSheet(f"""
            QLineEdit {{
                border: none;
                background: transparent;
                padding: 0 14px;
                color: {self.C_HEADING};
            }}
            QLineEdit:focus {{
                background: transparent;
            }}
            QLineEdit:disabled {{
                color: #ADB5BD;
            }}
        """)
        # Forward the focus events to style the parent frame
        self._password_input.installEventFilter(self)
        self._password_input.returnPressed.connect(self._handle_login)

        self._eye_btn = QPushButton("👁")
        self._eye_btn.setFixedSize(40, 40)
        self._eye_btn.setCursor(Qt.PointingHandCursor)
        self._eye_btn.setToolTip("Toggle password visibility")
        self._eye_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                font-size: 15px;
                color: {self.C_SUBTEXT};
            }}
            QPushButton:hover {{
                color: {self.C_HEADING};
            }}
            QPushButton:disabled {{ color: #CED4DA; }}
        """)
        self._eye_btn.clicked.connect(self._toggle_password_visibility)

        pass_row.addWidget(self._password_input)
        pass_row.addWidget(self._eye_btn)
        form.addWidget(self._pass_frame)
        form.addSpacing(8)

        # ── Inline error label ──
        self._error_label = QLabel("Invalid credentials. Please try again.")
        self._error_label.setFont(self._font(self.FONT_FAMILY, self.PT_SMALL))
        self._error_label.setStyleSheet(f"color: {self.C_ERROR};")
        self._error_label.setVisible(False)
        form.addWidget(self._error_label)
        form.addSpacing(14)

        # ── Remember me + Forgot password ──
        options_row = QHBoxLayout()
        self._remember_cb = QCheckBox("Remember me")
        self._remember_cb.setFont(self._font(self.FONT_FAMILY, self.PT_SMALL))
        self._remember_cb.setStyleSheet(f"color: {self.C_SUBTEXT};")
        options_row.addWidget(self._remember_cb)
        options_row.addStretch()

        self._forgot_btn = QPushButton("Forgot Password?")
        self._forgot_btn.setFlat(True)
        self._forgot_btn.setCursor(Qt.PointingHandCursor)
        self._forgot_btn.setFont(self._font(self.FONT_FAMILY, self.PT_SMALL))
        self._forgot_btn.setStyleSheet(f"""
            QPushButton {{
                color: {self.C_LINK}; 
                background: transparent; 
                border: none; 
                padding: 0;
            }}
            QPushButton:hover {{
                text-decoration: underline;
            }}
        """)
        self._forgot_btn.clicked.connect(self._handle_forgot)
        options_row.addWidget(self._forgot_btn)
        form.addLayout(options_row)
        form.addSpacing(20)

        # ── Login button ──
        self._login_btn = QPushButton("Sign In")
        self._login_btn.setFixedHeight(40)
        self._login_btn.setFont(self._font(self.FONT_FAMILY, self.PT_BTN, bold=True))
        self._login_btn.setCursor(Qt.PointingHandCursor)
        self._login_btn.setStyleSheet(self._login_btn_style())
        self._login_btn.clicked.connect(self._handle_login)
        form.addWidget(self._login_btn)
        form.addSpacing(24)

        # ── Divider ──
        form.addLayout(self._make_divider())
        form.addSpacing(20)

        # ── Create account link ──
        ca_row = QHBoxLayout()
        ca_row.setAlignment(Qt.AlignCenter)
        ca_row.setSpacing(4)

        ca_lbl = QLabel("Don't have an account?")
        ca_lbl.setFont(self._font(self.FONT_FAMILY, self.PT_SMALL))
        ca_lbl.setStyleSheet(f"color: {self.C_SUBTEXT};")

        ca_btn = QPushButton("Create an account")
        ca_btn.setFlat(True)
        ca_btn.setCursor(Qt.PointingHandCursor)
        ca_btn.setFont(self._font(self.FONT_FAMILY, self.PT_SMALL, bold=True))
        ca_btn.setStyleSheet(f"""
            QPushButton {{
                color: {self.C_LINK}; 
                background: transparent; 
                border: none; 
                padding: 0 2px;
            }}
            QPushButton:hover {{
                text-decoration: underline;
            }}
        """)
        ca_btn.clicked.connect(self._handle_signup)

        ca_row.addWidget(ca_lbl)
        ca_row.addWidget(ca_btn)
        form.addLayout(ca_row)

        grid.addWidget(self._form_widget, 0, 0, alignment=Qt.AlignCenter)
        return panel

    # ─────────────────────── widget factory helpers ───────────────────────────

    def _field_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(self._font(self.FONT_FAMILY, self.PT_LABEL, bold=True))
        lbl.setStyleSheet(f"color: {self.C_HEADING};")
        return lbl

    def _make_input(
        self,
        placeholder: str,
        echo: QLineEdit.EchoMode = QLineEdit.Normal,
        is_password: bool = False,
    ) -> QLineEdit:
        widget = QLineEdit()
        widget.setPlaceholderText(placeholder)
        widget.setEchoMode(echo)
        widget.setFont(self._font(self.FONT_FAMILY, self.PT_INPUT))
        widget.setFixedHeight(44)

        widget.setStyleSheet(f"""
            QLineEdit {{
                padding: 0 14px;
                border: 1.5px solid {self.C_BORDER};
                border-radius: 6px;
                background: {self.C_INPUT_BG};
                color: {self.C_HEADING};
            }}
            QLineEdit:focus {{
                border: 1.5px solid {self.C_FOCUS};
                background: {self.C_WHITE};
            }}
            QLineEdit:disabled {{
                background: {self.C_INPUT_DIS};
                color: #ADB5BD;
            }}
        """)
        return widget

    def eventFilter(self, obj, event):
        """Intercept focus events on the password input to style its wrapper frame."""
        from PyQt5.QtCore import QEvent
        if obj is getattr(self, '_password_input', None):
            if event.type() == QEvent.FocusIn:
                self._pass_frame.setStyleSheet(f"""
                    QFrame#PassFrame {{
                        background: {self.C_WHITE};
                        border: 1.5px solid {self.C_FOCUS};
                        border-radius: 6px;
                    }}
                """)
            elif event.type() == QEvent.FocusOut:
                self._pass_frame.setStyleSheet(f"""
                    QFrame#PassFrame {{
                        background: {self.C_INPUT_BG};
                        border: 1.5px solid {self.C_BORDER};
                        border-radius: 6px;
                    }}
                """)
        return super().eventFilter(obj, event)

    def _make_divider(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(12)

        for _ in range(2):
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFixedHeight(1)
            line.setStyleSheet(f"background-color: {self.C_DIVIDER}; border: none;")
            row.addWidget(line)
            if _ == 0:
                or_lbl = QLabel("or")
                or_lbl.setFont(self._font(self.FONT_FAMILY, self.PT_SMALL))
                or_lbl.setStyleSheet(f"color: {self.C_SUBTEXT};")
                or_lbl.setAlignment(Qt.AlignCenter)
                row.addWidget(or_lbl)

        return row

    def _login_btn_style(self) -> str:
        return f"""
            QPushButton {{
                background-color: {self.C_PRIMARY};
                color: {self.C_WHITE};
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {self.C_PRIMARY_HOVER};
            }}
            QPushButton:disabled {{
                background-color: {self.C_PRIMARY_DIS};
                color: #E8F0FE;
            }}
        """

    # ─────────────────────────── interactions ────────────────────────────────

    def _toggle_password_visibility(self) -> None:
        if self._password_input.echoMode() == QLineEdit.Password:
            self._password_input.setEchoMode(QLineEdit.Normal)
            self._eye_btn.setText("🙈")
        else:
            self._password_input.setEchoMode(QLineEdit.Password)
            self._eye_btn.setText("👁")

    def _handle_login(self) -> None:
        if self._authenticating:
            return

        username = self._username_input.text().strip()
        password = self._password_input.text().strip()

        if not username or not password:
            self._show_error("Please enter both username and password.")
            self._shake()
            return

        self._error_label.setVisible(False)
        self._set_loading(True)
        # Yield to the event loop so the button text updates before blocking auth
        QTimer.singleShot(60, lambda: self._authenticate(username, password))

    def _authenticate(self, username: str, password: str) -> None:
        self.worker = AuthWorker(self.auth_manager, username, password)
        self.worker.finished.connect(self._on_auth_finished)
        self.worker.start()

    def _on_auth_finished(self, success: bool, token_or_err, user_dict) -> None:
        self._set_loading(False)
        if success:
            self._error_label.setVisible(False)
            self.login_successful.emit(user_dict)
        else:
            self._show_error(str(token_or_err) if token_or_err else "Invalid credentials. Please try again.")
            self._shake()

    # ─────────────────────── loading / spinner ────────────────────────────────

    def _set_loading(self, active: bool) -> None:
        self._authenticating = active
        for w in (
            self._username_input,
            self._password_input,
            self._eye_btn,
            self._remember_cb,
            self._forgot_btn,
            self._login_btn,
        ):
            w.setEnabled(not active)

        if active:
            self._spinner_idx = 0
            self._spinner_timer.start()
        else:
            self._spinner_timer.stop()
            self._login_btn.setText("Sign In")

    def _tick_spinner(self) -> None:
        frame = self._SPINNER[self._spinner_idx % len(self._SPINNER)]
        self._login_btn.setText(f"{frame}  Signing in…")
        self._spinner_idx += 1

    # ─────────────────────── error / shake ───────────────────────────────────

    def _show_error(self, message: str) -> None:
        self._error_label.setText(message)
        self._error_label.setVisible(True)

    def _shake(self) -> None:
        """Translate the form widget ±8 px three times (60 ms per step)."""
        origin = self._form_widget.pos()
        seq = QSequentialAnimationGroup(self)

        # Build keyframe positions: 0 → +8 → 0 → -8 → 0 → +8 → 0 → -8 → 0
        key_x = [0, 8, 0, -8, 0, 8, 0, -8, 0]
        for i in range(len(key_x) - 1):
            a = QPropertyAnimation(self._form_widget, b"pos", self)
            a.setDuration(60)
            a.setStartValue(QPoint(origin.x() + key_x[i],     origin.y()))
            a.setEndValue  (QPoint(origin.x() + key_x[i + 1], origin.y()))
            a.setEasingCurve(QEasingCurve.InOutSine)
            seq.addAnimation(a)

        # Guarantee we land exactly on the original position
        restore = QPropertyAnimation(self._form_widget, b"pos", self)
        restore.setDuration(1)
        restore.setStartValue(origin)
        restore.setEndValue(origin)
        seq.addAnimation(restore)

        seq.start(QSequentialAnimationGroup.DeleteWhenStopped)

    # ─────────────────────── stub handlers ───────────────────────────────────

    def _handle_forgot(self) -> None:
        """Open forgot-password flow (extend as needed)."""
        logger.info("Forgot password requested")

    def _handle_signup(self) -> None:
        """Open registration flow (extend as needed)."""
        logger.info("Sign-up requested")
