"""
DisasterConnect — Signup Window (redesigned)

Two-column layout matching the Login window aesthetics.
Fixed at 900 × 600 px, centred on screen.
"""
from __future__ import annotations

import logging
import os
import re
import bcrypt
from datetime import datetime

from PyQt5.QtCore import (
    Qt, QTimer, pyqtSignal
)
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QPushButton, QSizePolicy, QVBoxLayout, QWidget, QComboBox, QGridLayout, QMessageBox
)

from db.connection import db_connection

logger = logging.getLogger(__name__)

class SignupWindow(QMainWindow):
    """Signup window — 900 × 600, two-column layout matching Login."""

    # ── Signal ───────────────────────────────────────────────────────────────
    signup_successful = pyqtSignal(dict)
    switch_to_login = pyqtSignal()

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

    def __init__(self, auth_manager=None) -> None:
        super().__init__()
        self.auth_manager = auth_manager
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
        self.setWindowTitle("DisasterConnect — Create Account")
        self.setFixedSize(900, 600)

        icon_path = os.path.join(self._resources_dir(), "images", "logo_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        screen = QApplication.primaryScreen().availableGeometry()
        self.move(
            (screen.width()  - 900) // 2,
            (screen.height() - 600) // 2,
        )

    def _setup_styles(self) -> None:
        """Shield the signup window from intrusive global stylesheets."""
        self.setStyleSheet(f"""
            QFrame, QLabel {{
                border: none;
                margin: 0;
                padding: 0;
                background: transparent;
            }}
            QLineEdit {{ margin: 0; }}
            QPushButton {{ margin: 0; min-width: 0; }}
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

        layout.addStretch()

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

        name_lbl = QLabel("Join the Force")
        name_lbl.setFont(self._font(self.FONT_FAMILY, self.PT_APP_NAME, bold=True))
        name_lbl.setStyleSheet(f"color: {self.C_WHITE}; background: transparent;")
        name_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(name_lbl)
        layout.addSpacing(10)

        tag_lbl = QLabel("Help coordinate emergency responses effectively.")
        tag_lbl.setFont(self._font(self.FONT_FAMILY, self.PT_TAGLINE, italic=True))
        tag_lbl.setStyleSheet(f"color: {self.C_TAGLINE}; background: transparent;")
        tag_lbl.setAlignment(Qt.AlignCenter)
        tag_lbl.setWordWrap(True)
        layout.addWidget(tag_lbl)
        layout.addSpacing(52)

        layout.addStretch()
        return panel

    # ── RIGHT PANEL ───────────────────────────────────────────────────────────

    def _build_right_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("RightPanel")
        
        panel.setStyleSheet(f"""
            QFrame#RightPanel {{
                background-color: {self.C_RIGHT_BG};
                background: qradialgradient(cx: 0.5, cy: 0.5, radius: 0.8,
                                            fx: 0.5, fy: 0.5,
                                            stop: 0 #FFFFFF, stop: 1 #F0F4F8);
            }}
        """)

        grid = QGridLayout(panel)
        grid.setContentsMargins(0, 0, 0, 0)

        self._form_widget = QWidget()
        self._form_widget.setFixedWidth(380)
        self._form_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        form = QVBoxLayout(self._form_widget)
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(0)

        # ── Heading ──
        heading = QLabel("Create your account")
        heading.setFont(self._font(self.FONT_FAMILY, self.PT_HEADING, bold=True))
        heading.setStyleSheet(f"color: {self.C_HEADING};")
        heading.setAlignment(Qt.AlignCenter)
        form.addWidget(heading)
        form.addSpacing(20)

        # ── Full Name ──
        name_row = QHBoxLayout()
        name_row.setContentsMargins(0, 0, 0, 0)
        name_row.setSpacing(10)
        self.first_name_input = self._make_input("First Name")
        self.last_name_input = self._make_input("Last Name")
        name_row.addWidget(self.first_name_input)
        name_row.addWidget(self.last_name_input)
        form.addLayout(name_row)
        form.addSpacing(10)

        # ── Email ──
        self.email_input = self._make_input("Email Address")
        form.addWidget(self.email_input)
        form.addSpacing(10)

        # ── Org & Role ──
        org_row = QHBoxLayout()
        org_row.setContentsMargins(0, 0, 0, 0)
        org_row.setSpacing(10)
        
        self.org_input = self._make_input("Organization")
        org_row.addWidget(self.org_input)
        
        self.role_input = QComboBox()
        self.role_input.addItems([
            "Emergency Responder",
            "Coordinator",
            "Administrator",
            "Medical Staff",
            "Logistics",
            "Other"
        ])
        self.role_input.setFont(self._font(self.FONT_FAMILY, self.PT_INPUT))
        self.role_input.setFixedHeight(44)
        self.role_input.setStyleSheet(f"""
            QComboBox {{
                padding: 0 14px;
                border: 1.5px solid {self.C_BORDER};
                border-radius: 6px;
                background: {self.C_INPUT_BG};
                color: {self.C_HEADING};
            }}
            QComboBox:focus {{
                border: 1.5px solid {self.C_FOCUS};
                background: {self.C_WHITE};
            }}
        """)
        org_row.addWidget(self.role_input)
        form.addLayout(org_row)
        form.addSpacing(10)

        # ── Passwords ──
        self.password_input = self._make_input("Password", echo=QLineEdit.Password)
        self.password_input.textChanged.connect(self.validate_password)
        form.addWidget(self.password_input)
        form.addSpacing(10)

        self.confirm_password_input = self._make_input("Confirm Password", echo=QLineEdit.Password)
        self.confirm_password_input.textChanged.connect(self.validate_password)
        form.addWidget(self.confirm_password_input)
        
        self.password_strength_label = QLabel()
        self.password_strength_label.setFont(self._font(self.FONT_FAMILY, self.PT_SMALL))
        self.password_strength_label.setFixedHeight(20)
        form.addWidget(self.password_strength_label)
        form.addSpacing(10)

        # ── Create Account Button ──
        self.signup_button = QPushButton("Create Account")
        self.signup_button.setFixedHeight(40)
        self.signup_button.setFont(self._font(self.FONT_FAMILY, self.PT_BTN, bold=True))
        self.signup_button.setCursor(Qt.PointingHandCursor)
        self.signup_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.C_PRIMARY};
                color: {self.C_WHITE};
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {self.C_PRIMARY_HOVER};
            }}
        """)
        self.signup_button.clicked.connect(self.create_account)
        form.addWidget(self.signup_button)
        form.addSpacing(20)

        # ── Login link ──
        ca_row = QHBoxLayout()
        ca_row.setAlignment(Qt.AlignCenter)
        ca_row.setSpacing(4)

        ca_lbl = QLabel("Already have an account?")
        ca_lbl.setFont(self._font(self.FONT_FAMILY, self.PT_SMALL))
        ca_lbl.setStyleSheet(f"color: {self.C_SUBTEXT};")

        ca_btn = QPushButton("Log In")
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
        ca_btn.clicked.connect(self.switch_to_login.emit)

        ca_row.addWidget(ca_lbl)
        ca_row.addWidget(ca_btn)
        form.addLayout(ca_row)

        grid.addWidget(self._form_widget, 0, 0, alignment=Qt.AlignCenter)
        return panel

    def _field_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(self._font(self.FONT_FAMILY, self.PT_LABEL, bold=True))
        lbl.setStyleSheet(f"color: {self.C_HEADING};")
        return lbl

    def _make_input(
        self,
        placeholder: str,
        echo: QLineEdit.EchoMode = QLineEdit.Normal,
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
        """)
        return widget

    def validate_password(self):
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
        is_long_enough = len(password) >= 8
        
        strength = has_upper + has_lower + has_digit + has_special + is_long_enough
        
        if strength == 0:
            self.password_strength_label.setText("")
        elif strength < 3:
            self.password_strength_label.setText("Weak Password")
            self.password_strength_label.setStyleSheet("color: #e74c3c;")
        elif strength < 5:
            self.password_strength_label.setText("Moderate Password")
            self.password_strength_label.setStyleSheet("color: #f39c12;")
        else:
            self.password_strength_label.setText("Strong Password")
            self.password_strength_label.setStyleSheet("color: #27ae60;")
        
        if confirm_password and password != confirm_password:
            self.password_strength_label.setText("Passwords do not match")
            self.password_strength_label.setStyleSheet("color: #e74c3c;")
    
    def create_account(self):
        if not all([
            self.first_name_input.text(),
            self.last_name_input.text(),
            self.email_input.text(),
            self.password_input.text(),
            self.confirm_password_input.text()
        ]):
            QMessageBox.warning(self, "Validation Error", "Please fill in all required fields.")
            return
        
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, self.email_input.text()):
            QMessageBox.warning(self, "Validation Error", "Please enter a valid email address.")
            return
        
        if self.password_input.text() != self.confirm_password_input.text():
            QMessageBox.warning(self, "Validation Error", "Passwords do not match.")
            return
        
        try:
            if db_connection.db.users.find_one({"email": self.email_input.text()}):
                QMessageBox.warning(self, "Account Exists", "An account with this email already exists.")
                return
            
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(self.password_input.text().encode('utf-8'), salt)
            
            first_name = self.first_name_input.text().strip()
            last_name = self.last_name_input.text().strip()
            
            base_username = f"{first_name.lower()}.{last_name.lower()}"
            username = base_username
            counter = 1
            while db_connection.db.users.find_one({"username": username}):
                username = f"{base_username}{counter}"
                counter += 1
                
            initials = f"{first_name[0]}{last_name[0]}".upper() if first_name and last_name else "U"
            
            user = {
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "email": self.email_input.text().strip(),
                "organization": self.org_input.text().strip(),
                "role": self.role_input.currentText().lower(),
                "password_hash": hashed_password,
                "avatar_initials": initials,
                "created_at": datetime.utcnow(),
                "last_login": None,
                "is_active": True
            }
            
            result = db_connection.db.users.insert_one(user)
            
            if result.inserted_id:
                QMessageBox.information(self, "Success", "Account created successfully! Please log in.")
                self.switch_to_login.emit()
            else:
                QMessageBox.critical(self, "Error", "Failed to create account. Please try again.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
