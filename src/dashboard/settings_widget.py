import os
import json
import re

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QListWidget, QListWidgetItem, QStackedWidget, QFileDialog,
    QMessageBox, QRadioButton, QButtonGroup, QSlider, QCheckBox, QTextEdit,
    QFormLayout, QGridLayout, QApplication, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QSize, QByteArray, QUrl, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QColor, QPainter, QPixmap, QPainterPath, QDesktopServices
from PyQt5.QtSvg import QSvgRenderer

from db.connection import db_connection

FEATHER_ICONS = {
    'check': '<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>',
    'shield': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>'
}

def create_svg_icon(name, color="#8B9DC3", size=24):
    svg = FEATHER_ICONS.get(name, FEATHER_ICONS['shield'])
    svg = svg.replace('currentColor', color)
    renderer = QSvgRenderer(QByteArray(svg.encode('utf-8')))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)

def create_avatar(text, size=80, img_path=None):
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    path = QPainterPath()
    path.addEllipse(0, 0, size, size)
    painter.setClipPath(path)
    
    if img_path and os.path.exists(img_path):
        img = QPixmap(img_path).scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        painter.drawPixmap(0, 0, img)
    else:
        painter.fillPath(path, QColor("#1F6FEB"))
        painter.setPen(QColor("white"))
        font = QFont("Segoe UI", size // 3, QFont.Bold)
        painter.setFont(font)
        painter.drawText(0, 0, size, size, Qt.AlignCenter, text[:2].upper() if text else "U")
        
    painter.end()
    return pixmap

class ColorSwatch(QWidget):
    clicked = pyqtSignal(str)
    
    def __init__(self, color_hex):
        super().__init__()
        self.color_hex = color_hex
        self.setFixedSize(36, 36)
        self.setCursor(Qt.PointingHandCursor)
        self.selected = False
        
        # Pre-render the checkmark to avoid paintEvent crashes
        self.check_pixmap = QPixmap(20, 20)
        self.check_pixmap.fill(Qt.transparent)
        p2 = QPainter(self.check_pixmap)
        p2.setRenderHint(QPainter.Antialiasing)
        renderer = QSvgRenderer(QByteArray(FEATHER_ICONS['check'].encode('utf-8')))
        renderer.render(p2)
        p2.end()
        
    def set_selected(self, val):
        self.selected = val
        self.update()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.color_hex)
            
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        path = QPainterPath()
        path.addEllipse(2, 2, 32, 32)
        painter.fillPath(path, QColor(self.color_hex))
        
        if self.selected:
            painter.drawPixmap(8, 8, self.check_pixmap)
            
        painter.end()

class SettingsWidget(QWidget):
    def __init__(self, auth_manager=None):
        super().__init__()
        self.auth_manager = auth_manager
        self.settings_file = "settings.json"
        self.config = self._load_settings()
        
        self.setStyleSheet("QWidget { background-color: #F3F4F6; }")
        self.setup_ui()
        self._apply_appearance()
        
    def _load_settings(self):
        default = {
            "profile_img": "",
            "theme": "Light",
            "primary_color": "#1F6FEB",
            "font_size": 11,
            "notif_incident": True,
            "notif_status": True,
            "notif_resource": False,
            "notif_msg": True,
            "notif_sound": True
        }
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r") as f:
                    data = json.load(f)
                    default.update(data)
            except: pass
        return default
        
    def _save_settings(self):
        with open(self.settings_file, "w") as f:
            json.dump(self.config, f, indent=4)
            
    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(24)
        
        # LEFT PANE - Sidebar
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(200)
        self.sidebar.setStyleSheet("""
            QListWidget { background: white; border: 1px solid #E5E7EB; border-radius: 8px; outline: none; padding: 8px; }
            QListWidget::item { padding: 12px; border-radius: 6px; color: #4B5563; font-weight: bold; margin-bottom: 4px; }
            QListWidget::item:selected { background-color: #EFF6FF; color: #1F6FEB; }
            QListWidget::item:hover:!selected { background-color: #F3F4F6; }
        """)
        cats = ["Profile", "Appearance", "Notifications", "Database", "About"]
        self.sidebar.addItems(cats)
        self.sidebar.setCurrentRow(0)
        self.sidebar.currentRowChanged.connect(self._switch_panel)
        main_layout.addWidget(self.sidebar)
        
        # RIGHT PANE - Stack
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("QStackedWidget { background: white; border: 1px solid #E5E7EB; border-radius: 8px; }")
        
        self._build_profile_panel()
        self._build_appearance_panel()
        self._build_notifications_panel()
        self._build_database_panel()
        self._build_about_panel()
        
        main_layout.addWidget(self.stack, stretch=1)
        
    def _switch_panel(self, idx):
        self.stack.setCurrentIndex(idx)
        
    def _create_header(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 16pt; font-weight: bold; color: #111827; margin-bottom: 16px;")
        return lbl

    # ----------------------------------------------------------------
    # 1. PROFILE PANEL
    # ----------------------------------------------------------------
    def _build_profile_panel(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(32, 32, 32, 32)
        l.setSpacing(16)
        
        l.addWidget(self._create_header("Profile Settings"))
        
        # Avatar
        av_layout = QHBoxLayout()
        self.avatar_lbl = QLabel()
        self.avatar_lbl.setCursor(Qt.PointingHandCursor)
        self.avatar_lbl.mousePressEvent = self._upload_avatar
        av_layout.addWidget(self.avatar_lbl)
        
        av_text = QVBoxLayout()
        av_text.setAlignment(Qt.AlignVCenter)
        av_title = QLabel("Profile Picture")
        av_title.setStyleSheet("font-weight: bold; color: #374151;")
        av_desc = QLabel("Click the image to upload a new avatar (PNG/JPG).")
        av_desc.setStyleSheet("color: #6B7280; font-size: 9pt;")
        av_text.addWidget(av_title)
        av_text.addWidget(av_desc)
        av_layout.addLayout(av_text)
        av_layout.addStretch()
        l.addLayout(av_layout)
        
        # Form
        form = QFormLayout()
        form.setSpacing(16)
        input_style = "padding: 8px; border: 1px solid #D1D5DB; border-radius: 4px; background: white; min-width: 250px;"
        
        self.prof_name = QLineEdit()
        self.prof_name.setStyleSheet(input_style)
        
        self.prof_email = QLineEdit()
        self.prof_email.setReadOnly(True)
        self.prof_email.setStyleSheet("padding: 8px; border: 1px solid #E5E7EB; border-radius: 4px; background: #F3F4F6; color: #9CA3AF; min-width: 250px;")
        
        role_lbl = QLabel()
        role_lbl.setStyleSheet("background-color: #1F6FEB; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold; font-size: 8pt;")
        role_lbl.setFixedSize(100, 24)
        role_lbl.setAlignment(Qt.AlignCenter)
        
        if self.auth_manager and hasattr(self.auth_manager, 'get_current_user'):
            u = self.auth_manager.get_current_user()
            if u:
                self.prof_name.setText(u.get("username", "Admin User"))
                self.prof_email.setText(u.get("email", "admin@disasterconnect.org"))
                role_lbl.setText(u.get("role", "admin").upper())
        else:
            self.prof_name.setText("Admin User")
            self.prof_email.setText("admin@disasterconnect.org")
            role_lbl.setText("ADMIN")
            
        self.avatar_lbl.setPixmap(create_avatar(self.prof_name.text(), 80, self.config.get("profile_img")))
            
        form.addRow("Full Name", self.prof_name)
        form.addRow("Email", self.prof_email)
        form.addRow("Role", role_lbl)
        
        l.addLayout(form)
        
        # Save Profile Btn
        save_p = QPushButton("Save Profile")
        save_p.setFixedWidth(120)
        save_p.setStyleSheet("background-color: #1F6FEB; color: white; padding: 8px; border-radius: 4px; font-weight: bold;")
        save_p.clicked.connect(self._save_profile_info)
        l.addWidget(save_p)
        
        l.addWidget(QLabel("<hr>"))
        
        # Password
        l.addWidget(self._create_header("Change Password"))
        pform = QFormLayout()
        pform.setSpacing(16)
        
        self.pwd_curr = QLineEdit()
        self.pwd_curr.setEchoMode(QLineEdit.Password)
        self.pwd_curr.setStyleSheet(input_style)
        
        self.pwd_new = QLineEdit()
        self.pwd_new.setEchoMode(QLineEdit.Password)
        self.pwd_new.setStyleSheet(input_style)
        
        self.pwd_conf = QLineEdit()
        self.pwd_conf.setEchoMode(QLineEdit.Password)
        self.pwd_conf.setStyleSheet(input_style)
        
        pform.addRow("Current Password", self.pwd_curr)
        pform.addRow("New Password", self.pwd_new)
        pform.addRow("Confirm Password", self.pwd_conf)
        l.addLayout(pform)
        
        upd_pwd = QPushButton("Update Password")
        upd_pwd.setFixedWidth(150)
        upd_pwd.setStyleSheet("background-color: #111827; color: white; padding: 8px; border-radius: 4px; font-weight: bold;")
        upd_pwd.clicked.connect(self._update_password)
        l.addWidget(upd_pwd)
        
        l.addStretch()
        self.stack.addWidget(w)
        
    def _upload_avatar(self, event):
        path, _ = QFileDialog.getOpenFileName(self, "Select Avatar", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self.config["profile_img"] = path
            self.avatar_lbl.setPixmap(create_avatar(self.prof_name.text(), 80, path))
            self._save_settings()
            
    def _save_profile_info(self):
        # In a real app we'd update MongoDB. Here we just mock success.
        QMessageBox.information(self, "Success", "Profile updated successfully.")
        
    def _update_password(self):
        curr = self.pwd_curr.text()
        new_p = self.pwd_new.text()
        conf = self.pwd_conf.text()
        
        if not curr or not new_p or not conf:
            QMessageBox.warning(self, "Error", "All password fields are required.")
            return
            
        if new_p != conf:
            QMessageBox.warning(self, "Error", "New passwords do not match.")
            return
            
        if len(new_p) < 8 or not re.search(r'\d', new_p):
            QMessageBox.warning(self, "Weak Password", "Password must be at least 8 characters and contain at least 1 number.")
            return
            
        QMessageBox.information(self, "Success", "Password updated successfully.")
        self.pwd_curr.clear()
        self.pwd_new.clear()
        self.pwd_conf.clear()

    # ----------------------------------------------------------------
    # 2. APPEARANCE PANEL
    # ----------------------------------------------------------------
    def _build_appearance_panel(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(32, 32, 32, 32)
        l.setSpacing(24)
        
        l.addWidget(self._create_header("Appearance Settings"))
        
        # Theme
        theme_lbl = QLabel("<b>Theme Preference</b>")
        l.addWidget(theme_lbl)
        
        t_layout = QHBoxLayout()
        self.bg_theme = QButtonGroup(self)
        for t in ["Light", "Dark", "System"]:
            rb = QRadioButton(t)
            rb.setStyleSheet("font-size: 11pt;")
            if t == self.config.get("theme"): rb.setChecked(True)
            self.bg_theme.addButton(rb)
            t_layout.addWidget(rb)
            rb.toggled.connect(self._on_theme_changed)
        t_layout.addStretch()
        l.addLayout(t_layout)
        
        # Primary Color
        col_lbl = QLabel("<b>Primary Brand Colour</b>")
        l.addWidget(col_lbl)
        
        colors = ["#1F6FEB", "#27AE60", "#E74C3C", "#F39C12", "#8B5CF6", "#06B6D4"]
        c_layout = QHBoxLayout()
        self.swatches = []
        for c in colors:
            sw = ColorSwatch(c)
            sw.clicked.connect(self._on_color_selected)
            if c == self.config.get("primary_color"): sw.set_selected(True)
            self.swatches.append(sw)
            c_layout.addWidget(sw)
        c_layout.addStretch()
        l.addLayout(c_layout)
        
        # Font Size
        font_lbl = QLabel("<b>Global Font Size</b>")
        l.addWidget(font_lbl)
        
        f_layout = QHBoxLayout()
        self.font_slider = QSlider(Qt.Horizontal)
        self.font_slider.setRange(10, 16)
        self.font_slider.setValue(self.config.get("font_size", 11))
        self.font_slider.setFixedWidth(200)
        self.font_slider.valueChanged.connect(self._on_font_changed)
        
        self.font_val_lbl = QLabel(f"{self.font_slider.value()}pt")
        self.font_val_lbl.setStyleSheet("font-weight: bold; color: #1F6FEB;")
        
        self.font_preview = QLabel("The quick brown fox jumps over the lazy dog.")
        self.font_preview.setStyleSheet(f"font-size: {self.font_slider.value()}pt; color: #6B7280; margin-left: 20px;")
        
        f_layout.addWidget(self.font_slider)
        f_layout.addWidget(self.font_val_lbl)
        f_layout.addWidget(self.font_preview)
        f_layout.addStretch()
        l.addLayout(f_layout)
        
        l.addStretch()
        self.stack.addWidget(w)
        
    def _on_theme_changed(self):
        btn = self.bg_theme.checkedButton()
        if btn:
            self.config["theme"] = btn.text()
            self._save_settings()
            self._apply_appearance()
            
    def _on_color_selected(self, hex_col):
        for sw in self.swatches:
            sw.set_selected(sw.color_hex == hex_col)
        self.config["primary_color"] = hex_col
        self._save_settings()
        self._apply_appearance()
        
    def _on_font_changed(self, val):
        self.font_val_lbl.setText(f"{val}pt")
        self.font_preview.setStyleSheet(f"font-size: {val}pt; color: #6B7280; margin-left: 20px;")
        self.config["font_size"] = val
        self._save_settings()
        self._apply_appearance()
        
    def _apply_appearance(self):
        # Global apply simulation
        if self.config.get("theme") == "Dark":
            # Simulate dark mode override (in a real app we'd apply to QApplication)
            self.setStyleSheet("""
                QWidget { background-color: #0D1117; color: #C9D1D9; }
                QStackedWidget { background: #161B22; border: 1px solid #30363D; }
                QListWidget { background: #161B22; border: 1px solid #30363D; }
                QListWidget::item { color: #8B9DC3; }
                QListWidget::item:selected { background-color: #1F2937; color: white; }
                QLineEdit { background: #0D1117; border: 1px solid #30363D; color: white; }
            """)
        else:
            self.setStyleSheet("QWidget { background-color: #F3F4F6; color: #111827; } QStackedWidget { background: white; border: 1px solid #E5E7EB; } QListWidget { background: white; border: 1px solid #E5E7EB; } QListWidget::item { color: #4B5563; } QListWidget::item:selected { background-color: #EFF6FF; color: #1F6FEB; } QLineEdit { background: white; border: 1px solid #D1D5DB; color: #111827; }")

    # ----------------------------------------------------------------
    # 3. NOTIFICATIONS PANEL
    # ----------------------------------------------------------------
    def _build_notifications_panel(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(32, 32, 32, 32)
        l.setSpacing(16)
        
        l.addWidget(self._create_header("Notification Preferences"))
        
        self.chk_inc = QCheckBox("New incident alerts (Email & Push)")
        self.chk_inc.setChecked(self.config.get("notif_incident", True))
        
        self.chk_stat = QCheckBox("Incident status change alerts")
        self.chk_stat.setChecked(self.config.get("notif_status", True))
        
        self.chk_res = QCheckBox("Resource deployment alerts")
        self.chk_res.setChecked(self.config.get("notif_resource", False))
        
        self.chk_msg = QCheckBox("Direct message notifications")
        self.chk_msg.setChecked(self.config.get("notif_msg", True))
        
        self.chk_snd = QCheckBox("Play alarm sound on Critical severity incidents")
        self.chk_snd.setChecked(self.config.get("notif_sound", True))
        self.chk_snd.setStyleSheet("color: #DC2626; font-weight: bold;")
        
        opts = [self.chk_inc, self.chk_stat, self.chk_res, self.chk_msg, self.chk_snd]
        for c in opts:
            c.setStyleSheet(c.styleSheet() + "; font-size: 11pt; margin-bottom: 8px;")
            l.addWidget(c)
            
        save_n = QPushButton("Save Preferences")
        save_n.setFixedWidth(150)
        save_n.setStyleSheet("background-color: #1F6FEB; color: white; padding: 8px; border-radius: 4px; font-weight: bold; margin-top: 16px;")
        save_n.clicked.connect(self._save_notifs)
        l.addWidget(save_n)
        
        l.addStretch()
        self.stack.addWidget(w)
        
    def _save_notifs(self):
        self.config["notif_incident"] = self.chk_inc.isChecked()
        self.config["notif_status"] = self.chk_stat.isChecked()
        self.config["notif_resource"] = self.chk_res.isChecked()
        self.config["notif_msg"] = self.chk_msg.isChecked()
        self.config["notif_sound"] = self.chk_snd.isChecked()
        self._save_settings()
        QMessageBox.information(self, "Success", "Notification preferences saved.")

    # ----------------------------------------------------------------
    # 4. DATABASE PANEL
    # ----------------------------------------------------------------
    def _build_database_panel(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(32, 32, 32, 32)
        l.setSpacing(24)
        
        l.addWidget(self._create_header("Database Configuration"))
        
        form = QFormLayout()
        form.setSpacing(16)
        
        self.db_uri = QLineEdit()
        # Mask the URI
        uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        if len(uri) > 10: masked = uri[:10] + "*" * (len(uri)-10)
        else: masked = uri
        self.db_uri.setText(masked)
        self.db_uri.setReadOnly(True)
        self.db_uri.setStyleSheet("padding: 8px; border: 1px solid #D1D5DB; border-radius: 4px; background: #F9FAFB; color: #6B7280; min-width: 300px;")
        
        self.db_name = QLineEdit("disaster_connect")
        self.db_name.setReadOnly(True)
        self.db_name.setStyleSheet("padding: 8px; border: 1px solid #D1D5DB; border-radius: 4px; background: #F9FAFB; color: #6B7280; min-width: 300px;")
        
        form.addRow("MongoDB URI", self.db_uri)
        form.addRow("Database Name", self.db_name)
        l.addLayout(form)
        
        conn_l = QHBoxLayout()
        test_btn = QPushButton("Test Connection")
        test_btn.setStyleSheet("background-color: #374151; color: white; padding: 8px 16px; border-radius: 4px; font-weight: bold;")
        test_btn.clicked.connect(self._test_db)
        
        self.db_stat_dot = QLabel("●")
        self.db_stat_dot.setStyleSheet("color: #6B7280; font-size: 16pt;")
        self.db_stat_lbl = QLabel("Untested")
        self.db_stat_lbl.setStyleSheet("color: #6B7280; font-weight: bold;")
        
        conn_l.addWidget(test_btn)
        conn_l.addSpacing(16)
        conn_l.addWidget(self.db_stat_dot)
        conn_l.addWidget(self.db_stat_lbl)
        conn_l.addStretch()
        l.addLayout(conn_l)
        
        l.addStretch()
        self.stack.addWidget(w)
        
    def _test_db(self):
        try:
            db_connection.client.admin.command('ping')
            self.db_stat_dot.setStyleSheet("color: #10B981; font-size: 16pt;")
            self.db_stat_lbl.setText("Connected (Ping OK)")
            self.db_stat_lbl.setStyleSheet("color: #10B981; font-weight: bold;")
        except Exception as e:
            self.db_stat_dot.setStyleSheet("color: #EF4444; font-size: 16pt;")
            self.db_stat_lbl.setText("Connection Failed")
            self.db_stat_lbl.setStyleSheet("color: #EF4444; font-weight: bold;")
            QMessageBox.critical(self, "Database Error", str(e))

    # ----------------------------------------------------------------
    # 5. ABOUT PANEL
    # ----------------------------------------------------------------
    def _build_about_panel(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(32, 32, 32, 32)
        l.setSpacing(16)
        
        logo = QLabel()
        logo.setPixmap(create_svg_icon('shield', '#1F6FEB', 64).pixmap(64, 64))
        logo.setAlignment(Qt.AlignCenter)
        l.addWidget(logo)
        
        title = QLabel("DisasterConnect")
        title.setStyleSheet("font-size: 20pt; font-weight: bold; color: #111827;")
        title.setAlignment(Qt.AlignCenter)
        l.addWidget(title)
        
        ver = QLabel("Version 1.0.0 (Production)")
        ver.setStyleSheet("color: #6B7280; font-weight: bold;")
        ver.setAlignment(Qt.AlignCenter)
        l.addWidget(ver)
        
        desc = QLabel("Advanced Agentic Emergency Response & Resource Management System.\nBuilt with PyQt5, MongoDB, and Folium.")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #374151;")
        l.addWidget(desc)
        
        l.addSpacing(16)
        
        gh = QPushButton(" View Source on GitHub")
        gh.setCursor(Qt.PointingHandCursor)
        gh.setStyleSheet("color: #1F6FEB; font-weight: bold; text-decoration: underline; border: none; background: transparent;")
        gh.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/Safari/DisasterConnect")))
        l.addWidget(gh, alignment=Qt.AlignCenter)
        
        l.addSpacing(16)
        
        lic_lbl = QLabel("<b>MIT License</b>")
        l.addWidget(lic_lbl)
        
        lic_text = QTextEdit()
        lic_text.setReadOnly(True)
        lic_text.setText("""Copyright (c) 2026 DisasterConnect

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.""")
        lic_text.setStyleSheet("background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 4px; color: #6B7280; font-family: monospace; font-size: 9pt;")
        l.addWidget(lic_text)
        
        self.stack.addWidget(w)
