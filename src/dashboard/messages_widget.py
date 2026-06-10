import os
import random
from datetime import datetime, timedelta
from bson.objectid import ObjectId

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QListWidget, QListWidgetItem, QScrollArea, QFileDialog,
    QSizePolicy, QGraphicsDropShadowEffect, QGridLayout
)
from PyQt5.QtCore import Qt, QTimer, QSize, QByteArray, pyqtSignal, QEvent, QPoint
from PyQt5.QtGui import QIcon, QFont, QColor, QPainter, QPixmap, QPainterPath
from PyQt5.QtSvg import QSvgRenderer

from db.connection import db_connection

FEATHER_ICONS = {
    'edit': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>',
    'search': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>',
    'smile': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M8 14s1.5 2 4 2 4-2 4-2"></path><line x1="9" y1="9" x2="9.01" y2="9"></line><line x1="15" y1="9" x2="15.01" y2="9"></line></svg>',
    'paperclip': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path></svg>',
    'send': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>',
    'phone': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>',
    'video': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg>',
    'alert-circle': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>',
    'hash': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="9" x2="20" y2="9"></line><line x1="4" y1="15" x2="20" y2="15"></line><line x1="10" y1="3" x2="8" y2="21"></line><line x1="16" y1="3" x2="14" y2="21"></line></svg>'
}

def create_svg_icon(name, color="#8B9DC3", size=24):
    svg = FEATHER_ICONS.get(name, FEATHER_ICONS['hash'])
    svg = svg.replace('currentColor', color)
    renderer = QSvgRenderer(QByteArray(svg.encode('utf-8')))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)

def time_ago(dt):
    if not dt: return ""
    diff = datetime.now() - dt
    if diff.days > 0: return f"{diff.days}d"
    hours = diff.seconds // 3600
    if hours > 0: return f"{hours}h"
    minutes = (diff.seconds % 3600) // 60
    if minutes > 0: return f"{minutes}m"
    return "now"

def get_avatar_color(name):
    colors = ['#E74C3C', '#F39C12', '#3498DB', '#27AE60', '#8E44AD', '#16A085', '#D35400', '#2C3E50']
    idx = sum(ord(c) for c in name) % len(colors)
    return colors[idx]

def create_avatar(text, size=40, bg_color="#3498DB"):
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Draw circle
    path = QPainterPath()
    path.addEllipse(0, 0, size, size)
    painter.fillPath(path, QColor(bg_color))
    
    # Draw text
    painter.setPen(QColor("white"))
    font = QFont("Segoe UI", size // 2 - 2, QFont.Bold)
    painter.setFont(font)
    painter.drawText(0, 0, size, size, Qt.AlignCenter, text[:2].upper())
    
    painter.end()
    return pixmap

class EmojiPicker(QFrame):
    emojiSelected = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(200, 160)
        self.setStyleSheet("""
            QFrame { background: white; border: 1px solid #E5E7EB; border-radius: 8px; }
            QPushButton { border: none; font-size: 16pt; background: transparent; padding: 4px; }
            QPushButton:hover { background: #F3F4F6; border-radius: 4px; }
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0,0,0,30))
        shadow.setOffset(0,4)
        self.setGraphicsEffect(shadow)
        
        layout = QGridLayout(self)
        layout.setContentsMargins(8,8,8,8)
        layout.setSpacing(4)
        
        emojis = ["😀","😂","🥰","😎","🤔","🙄","😭","😡","👍","👎","👏","🙏","🔥","✨","💯","🚑","🚒","🚓","⚠","✅"]
        for i, emj in enumerate(emojis):
            btn = QPushButton(emj)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, e=emj: self.emojiSelected.emit(e))
            layout.addWidget(btn, i // 5, i % 5)

class ThreadItemWidget(QWidget):
    def __init__(self, name, last_msg, dt, unread_count=0, is_channel=False):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        
        avatar_lbl = QLabel()
        if is_channel:
            avatar_lbl.setPixmap(create_svg_icon('hash', '#6C757D', 40).pixmap(40, 40))
        else:
            avatar_lbl.setPixmap(create_avatar(name, 40, get_avatar_color(name)))
        layout.addWidget(avatar_lbl)
        
        text_l = QVBoxLayout()
        text_l.setSpacing(2)
        
        top_l = QHBoxLayout()
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet("font-weight: bold; color: #111827;")
        top_l.addWidget(name_lbl)
        top_l.addStretch()
        time_lbl = QLabel(time_ago(dt))
        time_lbl.setStyleSheet("color: #9CA3AF; font-size: 8pt;")
        top_l.addWidget(time_lbl)
        text_l.addLayout(top_l)
        
        btm_l = QHBoxLayout()
        msg_preview = last_msg[:37] + "..." if len(last_msg) > 40 else last_msg
        msg_lbl = QLabel(msg_preview)
        msg_lbl.setStyleSheet(f"color: {'#111827; font-weight: bold;' if unread_count > 0 else '#6B7280;'}")
        btm_l.addWidget(msg_lbl)
        btm_l.addStretch()
        
        if unread_count > 0:
            badge = QLabel(str(unread_count))
            badge.setStyleSheet("background-color: #EF4444; color: white; border-radius: 10px; padding: 2px 6px; font-weight: bold; font-size: 8pt;")
            badge.setAlignment(Qt.AlignCenter)
            btm_l.addWidget(badge)
            
        text_l.addLayout(btm_l)
        layout.addLayout(text_l)

class MessageBubble(QWidget):
    def __init__(self, text, sender, dt, is_me=False):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        
        # Sender Label
        lbl = QLabel("You" if is_me else sender)
        lbl.setStyleSheet("color: #6B7280; font-size: 8pt; font-weight: bold; margin-left: 12px; margin-right: 12px;")
        lbl.setAlignment(Qt.AlignRight if is_me else Qt.AlignLeft)
        layout.addWidget(lbl)
        
        # Bubble
        b_layout = QHBoxLayout()
        if is_me: b_layout.addStretch()
        
        bubble = QLabel(text)
        bubble.setWordWrap(True)
        # Max width logic for bubble can be tricky, so we just use size policy
        bubble.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        bubble.setMaximumWidth(400)
        
        if is_me:
            bubble.setStyleSheet("background-color: #1F6FEB; color: white; padding: 10px 14px; border-radius: 14px; border-bottom-right-radius: 4px; font-size: 10pt;")
        else:
            bubble.setStyleSheet("background-color: white; color: #111827; padding: 10px 14px; border-radius: 14px; border-bottom-left-radius: 4px; border: 1px solid #E5E7EB; font-size: 10pt;")
            
        b_layout.addWidget(bubble)
        if not is_me: b_layout.addStretch()
        
        layout.addLayout(b_layout)

class DateSeparator(QWidget):
    def __init__(self, text):
        super().__init__()
        l = QHBoxLayout(self)
        l.setAlignment(Qt.AlignCenter)
        lbl = QLabel(text)
        lbl.setStyleSheet("background-color: #F3F4F6; color: #6B7280; padding: 4px 12px; border-radius: 12px; font-size: 8pt; font-weight: bold;")
        l.addWidget(lbl)

class MessagesWidget(QWidget):
    def __init__(self, auth_manager=None):
        super().__init__()
        self.auth_manager = auth_manager
        self.db = db_connection.db
        
        # Current user mockup
        self.current_user = 'coordinator_01'
        self.current_user_name = "System Coordinator"
        self.active_thread_id = "General"
        
        self._seed_channels()
        
        self.setStyleSheet("QWidget { background-color: white; }")
        self.setup_ui()
        self.load_threads()
        self.load_messages()
        
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.poll_messages)
        self.poll_timer.start(5000)
        
    def _seed_channels(self):
        # Seed dummy messages if none exist
        if self.db.messages.count_documents({}) == 0:
            msgs = [
                {"channel_id": "General", "sender_id": "sys", "sender_name": "System", "content": "Welcome to DisasterConnect general comms.", "timestamp": datetime.now() - timedelta(days=1)},
                {"channel_id": "Incident Alpha", "sender_id": "sys", "sender_name": "System", "content": "Incident Alpha response coordinated here.", "timestamp": datetime.now() - timedelta(hours=2)},
                {"channel_id": "Resource Coord", "sender_id": "user2", "sender_name": "Logistics Team", "content": "We need 2 more ambulances at site 4.", "timestamp": datetime.now() - timedelta(minutes=15)},
                {"channel_id": "General", "sender_id": "user3", "sender_name": "Field Ops", "content": "All units check in.", "timestamp": datetime.now() - timedelta(minutes=5)}
            ]
            self.db.messages.insert_many(msgs)
            
    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # LEFT PANE
        self.left_pane = QFrame()
        self.left_pane.setFixedWidth(280)
        self.left_pane.setStyleSheet("QFrame { background-color: #F8F9FA; border-right: 1px solid #E5E7EB; }")
        left_layout = QVBoxLayout(self.left_pane)
        left_layout.setContentsMargins(0,0,0,0)
        left_layout.setSpacing(0)
        
        # Left Header
        lh = QWidget()
        lhl = QHBoxLayout(lh)
        lhl.setContentsMargins(16, 16, 16, 16)
        m_title = QLabel("Messages")
        m_title.setStyleSheet("font-size: 16pt; font-weight: bold; color: #111827; border: none;")
        new_btn = QPushButton()
        new_btn.setIcon(create_svg_icon('edit', '#1F6FEB'))
        new_btn.setStyleSheet("border: none; background: transparent;")
        new_btn.setCursor(Qt.PointingHandCursor)
        lhl.addWidget(m_title)
        lhl.addStretch()
        lhl.addWidget(new_btn)
        left_layout.addWidget(lh)
        
        # Search
        sw = QWidget()
        sl = QVBoxLayout(sw)
        sl.setContentsMargins(16, 0, 16, 16)
        self.search_in = QLineEdit()
        self.search_in.setPlaceholderText("Search conversations...")
        self.search_in.addAction(create_svg_icon('search', '#6B7280', 16), QLineEdit.LeadingPosition)
        self.search_in.setStyleSheet("QLineEdit { padding: 8px 8px 8px 28px; border: 1px solid #D1D5DB; border-radius: 18px; background: white; }")
        sl.addWidget(self.search_in)
        left_layout.addWidget(sw)
        
        # Thread List
        self.thread_list = QListWidget()
        self.thread_list.setStyleSheet("""
            QListWidget { border: none; background: transparent; outline: none; }
            QListWidget::item { border-bottom: 1px solid #E5E7EB; }
            QListWidget::item:selected { background-color: #E5E7EB; }
            QListWidget::item:hover { background-color: #F3F4F6; }
        """)
        self.thread_list.itemClicked.connect(self._on_thread_clicked)
        left_layout.addWidget(self.thread_list)
        
        main_layout.addWidget(self.left_pane)
        
        # RIGHT PANE
        self.right_pane = QFrame()
        self.right_pane.setStyleSheet("QFrame { background-color: #F9FAFB; border: none; }")
        right_layout = QVBoxLayout(self.right_pane)
        right_layout.setContentsMargins(0,0,0,0)
        right_layout.setSpacing(0)
        
        # Priority Alert Banner
        self.alert_banner = QFrame()
        self.alert_banner.setStyleSheet("background-color: #FEF2F2; border-bottom: 1px solid #FCA5A5;")
        self.alert_banner.hide()
        al = QHBoxLayout(self.alert_banner)
        al.setContentsMargins(16, 12, 16, 12)
        al_icon = QLabel()
        al_icon.setPixmap(create_svg_icon('alert-circle', '#DC2626').pixmap(20, 20))
        self.al_text = QLabel("CRITICAL: Industrial Fire reported in Sector 4.")
        self.al_text.setStyleSheet("color: #991B1B; font-weight: bold; border: none;")
        al_btn = QPushButton("View Incident")
        al_btn.setStyleSheet("background-color: #DC2626; color: white; border: none; border-radius: 4px; padding: 4px 12px; font-weight: bold;")
        al.addWidget(al_icon)
        al.addWidget(self.al_text)
        al.addStretch()
        al.addWidget(al_btn)
        right_layout.addWidget(self.alert_banner)
        
        # Topbar
        self.topbar = QFrame()
        self.topbar.setFixedHeight(64)
        self.topbar.setStyleSheet("background-color: white; border-bottom: 1px solid #E5E7EB;")
        tl = QHBoxLayout(self.topbar)
        tl.setContentsMargins(20, 0, 20, 0)
        
        self.tb_avatar = QLabel()
        self.tb_avatar.setPixmap(create_svg_icon('hash', '#1F6FEB', 40).pixmap(40,40))
        tl.addWidget(self.tb_avatar)
        
        tb_text = QVBoxLayout()
        tb_text.setSpacing(0)
        tb_text.setAlignment(Qt.AlignVCenter)
        self.tb_name = QLabel("General")
        self.tb_name.setStyleSheet("font-weight: bold; font-size: 12pt; color: #111827; border: none;")
        
        onl_l = QHBoxLayout()
        dot = QLabel("●")
        dot.setStyleSheet("color: #10B981; font-size: 10pt; border: none;")
        stat = QLabel("Online")
        stat.setStyleSheet("color: #6B7280; font-size: 9pt; border: none;")
        onl_l.addWidget(dot)
        onl_l.addWidget(stat)
        onl_l.addStretch()
        
        tb_text.addWidget(self.tb_name)
        tb_text.addLayout(onl_l)
        tl.addLayout(tb_text)
        
        tl.addStretch()
        
        btn_phone = QPushButton()
        btn_phone.setIcon(create_svg_icon('phone', '#6B7280'))
        btn_phone.setStyleSheet("border: none; background: transparent;")
        btn_phone.setCursor(Qt.PointingHandCursor)
        
        btn_video = QPushButton()
        btn_video.setIcon(create_svg_icon('video', '#6B7280'))
        btn_video.setStyleSheet("border: none; background: transparent;")
        btn_video.setCursor(Qt.PointingHandCursor)
        
        tl.addWidget(btn_phone)
        tl.addSpacing(16)
        tl.addWidget(btn_video)
        right_layout.addWidget(self.topbar)
        
        # Message Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.msg_container = QWidget()
        self.msg_container.setStyleSheet("background: transparent;")
        self.msg_layout = QVBoxLayout(self.msg_container)
        self.msg_layout.setContentsMargins(20, 20, 20, 20)
        self.msg_layout.setSpacing(8)
        self.msg_layout.addStretch()
        self.scroll_area.setWidget(self.msg_container)
        right_layout.addWidget(self.scroll_area, stretch=1)
        
        # Input Bar
        input_bar = QFrame()
        input_bar.setStyleSheet("background-color: white; border-top: 1px solid #E5E7EB;")
        il = QHBoxLayout(input_bar)
        il.setContentsMargins(16, 12, 16, 12)
        
        self.btn_emoji = QPushButton()
        self.btn_emoji.setIcon(create_svg_icon('smile', '#6B7280'))
        self.btn_emoji.setStyleSheet("border: none; background: transparent;")
        self.btn_emoji.setCursor(Qt.PointingHandCursor)
        self.btn_emoji.clicked.connect(self._toggle_emoji)
        
        self.btn_attach = QPushButton()
        self.btn_attach.setIcon(create_svg_icon('paperclip', '#6B7280'))
        self.btn_attach.setStyleSheet("border: none; background: transparent;")
        self.btn_attach.setCursor(Qt.PointingHandCursor)
        self.btn_attach.clicked.connect(self._attach_file)
        
        self.msg_input = QLineEdit()
        self.msg_input.setPlaceholderText("Type a message...")
        self.msg_input.setStyleSheet("padding: 10px; border: 1px solid #D1D5DB; border-radius: 20px; background: #F3F4F6; font-size: 10pt;")
        self.msg_input.textChanged.connect(self._on_input_changed)
        self.msg_input.returnPressed.connect(self.send_message)
        
        self.btn_send = QPushButton()
        self.btn_send.setIcon(create_svg_icon('send', 'white'))
        self.btn_send.setFixedSize(40, 40)
        self.btn_send.setStyleSheet("background-color: #9CA3AF; border-radius: 20px; border: none;") # Grey when empty
        self.btn_send.setEnabled(False)
        self.btn_send.clicked.connect(self.send_message)
        
        il.addWidget(self.btn_emoji)
        il.addWidget(self.btn_attach)
        il.addWidget(self.msg_input)
        il.addWidget(self.btn_send)
        right_layout.addWidget(input_bar)
        
        main_layout.addWidget(self.right_pane, stretch=1)
        
        # Emoji Picker Float
        self.emoji_picker = EmojiPicker(self.right_pane)
        self.emoji_picker.hide()
        self.emoji_picker.emojiSelected.connect(self._insert_emoji)
        
        self._check_priority_alerts()
        
    def _check_priority_alerts(self):
        inc = self.db.incidents.find_one({"status": {"$in": ["Active", "In Progress"]}, "severity": {"$in": ["Critical", "High"]}})
        if inc:
            self.al_text.setText(f"CRITICAL: {inc.get('type')} reported in {inc.get('location', {}).get('area', 'Unknown Location')}.")
            self.alert_banner.show()
        else:
            self.alert_banner.hide()

    def load_threads(self):
        self.thread_list.clear()
        
        channels = ["General", "Incident Alpha", "Resource Coord"]
        
        for ch in channels:
            last_msg = self.db.messages.find_one({"channel_id": ch}, sort=[("timestamp", -1)])
            content = last_msg["content"] if last_msg else "No messages yet"
            dt = last_msg["timestamp"] if last_msg else None
            
            # Count unread (mocking as 0 for now since read state needs per-user tracking)
            unread = 0 
            
            item = QListWidgetItem(self.thread_list)
            w = ThreadItemWidget(ch, content, dt, unread, is_channel=True)
            item.setSizeHint(w.sizeHint())
            
            # Store ID in data
            item.setData(Qt.UserRole, ch)
            self.thread_list.setItemWidget(item, w)
            
            if ch == self.active_thread_id:
                item.setSelected(True)

    def _on_thread_clicked(self, item):
        ch = item.data(Qt.UserRole)
        self.active_thread_id = ch
        self.tb_name.setText(ch)
        self.load_messages()

    def load_messages(self):
        # Clear existing messages except the top stretch
        while self.msg_layout.count() > 1:
            item = self.msg_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        msgs = list(self.db.messages.find({"channel_id": self.active_thread_id}).sort("timestamp", 1))
        
        last_date = None
        for msg in msgs:
            dt = msg.get("timestamp")
            
            # Date Separator
            if dt:
                date_str = dt.strftime("%Y-%m-%d")
                if date_str != last_date:
                    if dt.date() == datetime.now().date():
                        d_text = "Today"
                    elif dt.date() == (datetime.now() - timedelta(days=1)).date():
                        d_text = "Yesterday"
                    else:
                        d_text = dt.strftime("%b %d, %Y")
                    
                    self.msg_layout.insertWidget(self.msg_layout.count() - 1, DateSeparator(d_text))
                    last_date = date_str
            
            is_me = msg.get("sender_id") == self.current_user
            sender_name = msg.get("sender_name", "Unknown")
            
            w = MessageBubble(msg.get("content", ""), sender_name, dt, is_me)
            self.msg_layout.insertWidget(self.msg_layout.count() - 1, w)
            
        # Scroll to bottom
        QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum()))

    def _on_input_changed(self, text):
        if text.strip():
            self.btn_send.setEnabled(True)
            self.btn_send.setStyleSheet("background-color: #1F6FEB; border-radius: 20px; border: none;")
        else:
            self.btn_send.setEnabled(False)
            self.btn_send.setStyleSheet("background-color: #9CA3AF; border-radius: 20px; border: none;")

    def send_message(self):
        text = self.msg_input.text().strip()
        if not text: return
        
        msg = {
            "channel_id": self.active_thread_id,
            "sender_id": self.current_user,
            "sender_name": self.current_user_name,
            "content": text,
            "timestamp": datetime.now(),
            "read": False
        }
        self.db.messages.insert_one(msg)
        self.msg_input.clear()
        self.load_threads()
        self.load_messages()
        
    def poll_messages(self):
        # In a real app we'd track last_fetch_timestamp to only get new ones.
        # For this prototype, we'll just check if counts changed.
        count = self.db.messages.count_documents({"channel_id": self.active_thread_id})
        # Approx check if we need to reload
        current_msgs = self.msg_layout.count() - 1 # -1 for stretch
        # It's better to just do a smart reload, but we'll brute force for safety on prototype
        self.load_threads()
        
    def _toggle_emoji(self):
        if self.emoji_picker.isVisible():
            self.emoji_picker.hide()
        else:
            pos = self.btn_emoji.mapTo(self.right_pane, QPoint(0, 0))
            self.emoji_picker.move(pos.x(), pos.y() - self.emoji_picker.height() - 10)
            self.emoji_picker.show()
            
    def _insert_emoji(self, emj):
        self.msg_input.insert(emj)
        self.emoji_picker.hide()
        self.msg_input.setFocus()
        
    def _attach_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Attach File")
        if path:
            filename = os.path.basename(path)
            # Send file mock
            msg = {
                "channel_id": self.active_thread_id,
                "sender_id": self.current_user,
                "sender_name": self.current_user_name,
                "content": f"📎 Attached file: {filename}",
                "timestamp": datetime.now(),
                "read": False
            }
            self.db.messages.insert_one(msg)
            self.load_threads()
            self.load_messages()
