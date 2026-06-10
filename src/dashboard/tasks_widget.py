import os
from datetime import datetime, timedelta
from bson.objectid import ObjectId

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QScrollArea, QComboBox, QDialog, QFormLayout, QTextEdit, QDateEdit,
    QSizePolicy, QGraphicsDropShadowEffect, QInputDialog
)
from PyQt5.QtCore import Qt, QSize, QByteArray, pyqtSignal, QDate, QMimeData
from PyQt5.QtGui import QIcon, QFont, QColor, QPainter, QPixmap, QDrag, QPainterPath
from PyQt5.QtSvg import QSvgRenderer

from db.connection import db_connection

FEATHER_ICONS = {
    'search': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>',
    'plus': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>',
    'calendar': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>'
}

def create_svg_icon(name, color="#8B9DC3", size=24):
    svg = FEATHER_ICONS.get(name, FEATHER_ICONS['plus'])
    svg = svg.replace('currentColor', color)
    renderer = QSvgRenderer(QByteArray(svg.encode('utf-8')))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)

def get_avatar_color(name):
    if not name: return '#95A5A6'
    colors = ['#E74C3C', '#F39C12', '#3498DB', '#27AE60', '#8E44AD', '#16A085', '#D35400', '#2C3E50']
    idx = sum(ord(c) for c in name) % len(colors)
    return colors[idx]

def create_avatar(text, size=24):
    text = text[:2].upper() if text else "?"
    bg_color = get_avatar_color(text)
    
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    path = QPainterPath()
    path.addEllipse(0, 0, size, size)
    painter.fillPath(path, QColor(bg_color))
    
    painter.setPen(QColor("white"))
    font = QFont("Segoe UI", size // 2 - 2, QFont.Bold)
    painter.setFont(font)
    painter.drawText(0, 0, size, size, Qt.AlignCenter, text)
    
    painter.end()
    return pixmap

def get_priority_color(priority):
    return {"High": "#EF4444", "Medium": "#F59E0B", "Low": "#10B981"}.get(priority, "#6B7280")

def create_pill_badge(text, color, outline=False):
    w = QWidget()
    l = QHBoxLayout(w)
    l.setContentsMargins(6, 2, 6, 2)
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignCenter)
    
    if outline:
        lbl.setStyleSheet(f"color: {color}; border: 1px solid {color}; border-radius: 10px; font-weight: bold; font-size: 8pt;")
    else:
        lbl.setStyleSheet(f"background-color: {color}; color: white; border-radius: 10px; font-weight: bold; font-size: 8pt;")
        
    l.addWidget(lbl)
    return w

class TaskDialog(QDialog):
    def __init__(self, parent=None, task_data=None, default_status="To Do"):
        super().__init__(parent)
        self.db = db_connection.db
        self.task_data = task_data
        self.default_status = default_status
        self.setWindowTitle("Edit Task" if task_data else "New Task")
        self.setFixedSize(460, 480)
        self.setStyleSheet("""
            QDialog { background-color: white; }
            QLineEdit, QComboBox, QTextEdit, QDateEdit {
                padding: 8px; border: 1px solid #E5E7EB; border-radius: 4px; background-color: #F9FAFB;
            }
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QDateEdit:focus {
                border: 1px solid #1F6FEB; background-color: white;
            }
        """)
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        title_lbl = QLabel("New Task" if not self.task_data else "Edit Task")
        title_lbl.setStyleSheet("font-size: 16pt; font-weight: bold; color: #111827; margin-bottom: 12px;")
        layout.addWidget(title_lbl)
        
        form = QFormLayout()
        form.setSpacing(12)
        
        self.title_in = QLineEdit()
        self.desc_in = QTextEdit()
        self.desc_in.setFixedHeight(80)
        self.status_combo = QComboBox()
        self.status_combo.addItems(["To Do", "In Progress", "Under Review", "Done"])
        self.status_combo.setCurrentText(self.default_status)
        
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Low", "Medium", "High"])
        self.priority_combo.setCurrentText("Medium")
        
        self.assignee_in = QLineEdit()
        
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate().addDays(1))
        
        self.inc_combo = QComboBox()
        self.inc_combo.addItem("None", None)
        active_incs = list(self.db.incidents.find({"status": {"$in": ["Active", "In Progress"]}}))
        for inc in active_incs:
            self.inc_combo.addItem(inc.get("title", "Unknown"), str(inc["_id"]))
            
        form.addRow("Title *", self.title_in)
        form.addRow("Description", self.desc_in)
        form.addRow("Status", self.status_combo)
        form.addRow("Priority", self.priority_combo)
        form.addRow("Assignee", self.assignee_in)
        form.addRow("Due Date", self.date_edit)
        form.addRow("Linked Incident", self.inc_combo)
        
        layout.addLayout(form)
        layout.addStretch()
        
        btns = QHBoxLayout()
        btns.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet("padding: 8px 16px; border: 1px solid #D1D5DB; border-radius: 4px; background: white;")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Save Task")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet("padding: 8px 16px; border: none; border-radius: 4px; background: #1F6FEB; color: white; font-weight: bold;")
        save_btn.clicked.connect(self._save)
        
        btns.addWidget(cancel_btn)
        btns.addWidget(save_btn)
        layout.addLayout(btns)
        
        if self.task_data:
            self._populate()
            
    def _populate(self):
        self.title_in.setText(self.task_data.get("title", ""))
        self.desc_in.setText(self.task_data.get("description", ""))
        self.status_combo.setCurrentText(self.task_data.get("status", "To Do"))
        self.priority_combo.setCurrentText(self.task_data.get("priority", "Medium"))
        self.assignee_in.setText(self.task_data.get("assignee", ""))
        
        dt = self.task_data.get("due_date")
        if dt:
            qdate = QDate(dt.year, dt.month, dt.day)
            self.date_edit.setDate(qdate)
            
        inc_id = self.task_data.get("incident_id")
        if inc_id:
            idx = self.inc_combo.findData(inc_id)
            if idx >= 0: self.inc_combo.setCurrentIndex(idx)

    def _save(self):
        if not self.title_in.text().strip():
            self.title_in.setStyleSheet("border: 1px solid red;")
            return
            
        qdate = self.date_edit.date()
        dt = datetime(qdate.year(), qdate.month(), qdate.day())
        
        data = {
            "title": self.title_in.text().strip(),
            "description": self.desc_in.toPlainText().strip(),
            "status": self.status_combo.currentText(),
            "priority": self.priority_combo.currentText(),
            "assignee": self.assignee_in.text().strip(),
            "due_date": dt,
            "incident_id": self.inc_combo.currentData()
        }
        
        if self.task_data:
            self.db.tasks.update_one({"_id": self.task_data["_id"]}, {"$set": data})
        else:
            data["created_at"] = datetime.now()
            self.db.tasks.insert_one(data)
            
        self.accept()

class TaskCard(QFrame):
    clicked = pyqtSignal(object)
    
    def __init__(self, task_data):
        super().__init__()
        self.task_data = task_data
        self.setCursor(Qt.OpenHandCursor)
        self.setStyleSheet("""
            TaskCard { background-color: white; border: 1px solid #E5E7EB; border-radius: 6px; }
            TaskCard:hover { border: 1px solid #1F6FEB; }
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0,0,0,15))
        shadow.setOffset(0,2)
        self.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)
        
        # Title
        t_lbl = QLabel(task_data.get("title", ""))
        t_lbl.setStyleSheet("font-weight: bold; font-size: 10pt; color: #111827; border: none;")
        t_lbl.setWordWrap(True)
        layout.addWidget(t_lbl)
        
        # Description excerpt
        desc = task_data.get("description", "")
        if desc:
            d_lbl = QLabel(desc.split('\n')[0][:40] + ('...' if len(desc)>40 else ''))
            d_lbl.setStyleSheet("color: #6B7280; font-style: italic; font-size: 9pt; border: none;")
            layout.addWidget(d_lbl)
            
        # Incident Tag
        inc_id = task_data.get("incident_id")
        if inc_id:
            db = db_connection.db
            inc = db.incidents.find_one({"_id": ObjectId(inc_id)})
            if inc:
                tag = create_pill_badge("Incident: " + inc.get("title", "")[:15], "#1F6FEB", outline=True)
                layout.addWidget(tag)
                
        # Bottom Row
        btm = QHBoxLayout()
        pri = task_data.get("priority", "Medium")
        btm.addWidget(create_pill_badge(pri, get_priority_color(pri)))
        
        btm.addStretch()
        
        dt = task_data.get("due_date")
        if dt:
            dt_lbl = QLabel(dt.strftime("%b %d"))
            dt_lbl.setStyleSheet("color: #6B7280; font-size: 8pt; border: none;")
            btm.addWidget(dt_lbl)
            
        assignee = task_data.get("assignee")
        if assignee:
            av = QLabel()
            av.setPixmap(create_avatar(assignee, 20))
            av.setStyleSheet("border: none;")
            av.setToolTip(assignee)
            btm.addWidget(av)
            
        layout.addLayout(btm)
        
        self.drag_start_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.OpenHandCursor)
        super().mouseReleaseEvent(event)
        
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.task_data)
            
    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton): return
        if (event.pos() - self.drag_start_pos).manhattanLength() < 5: return
        
        mime = QMimeData()
        mime.setText(str(self.task_data["_id"]))
        
        drag = QDrag(self)
        drag.setMimeData(mime)
        
        # Create ghost pixmap (70% opacity)
        pixmap = self.grab()
        ghost = QPixmap(pixmap.size())
        ghost.fill(Qt.transparent)
        painter = QPainter(ghost)
        painter.setOpacity(0.7)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()
        
        drag.setPixmap(ghost)
        drag.setHotSpot(event.pos())
        
        self.hide() # hide temporarily
        drag.exec_(Qt.MoveAction)
        self.show()

class KanbanColumn(QFrame):
    taskDropped = pyqtSignal(str, str) # task_id, new_status
    
    def __init__(self, title, bg_color, accent_color):
        super().__init__()
        self.title = title
        self.bg_color = bg_color
        self.accent_color = accent_color
        self.setAcceptDrops(True)
        
        self.setStyleSheet(f"""
            KanbanColumn {{
                background-color: {bg_color};
                border-radius: 8px;
            }}
        """)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        
        # Header
        hl = QHBoxLayout()
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"font-weight: bold; font-size: 11pt; color: {accent_color};")
        
        self.count_badge = QLabel("0")
        self.count_badge.setStyleSheet(f"background-color: {accent_color}; color: white; border-radius: 10px; padding: 2px 8px; font-weight: bold;")
        
        hl.addWidget(title_lbl)
        hl.addStretch()
        hl.addWidget(self.count_badge)
        self.main_layout.addLayout(hl)
        
        # Scroll area for cards
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.cards_container = QWidget()
        self.cards_container.setStyleSheet("background: transparent;")
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 8, 0, 8)
        self.cards_layout.setSpacing(12)
        self.cards_layout.addStretch()
        
        self.scroll.setWidget(self.cards_container)
        self.main_layout.addWidget(self.scroll, stretch=1)
        
        self.add_btn = QPushButton(f" + Add Task")
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.setStyleSheet(f"color: {accent_color}; font-weight: bold; border: none; padding: 8px; text-align: left;")
        self.main_layout.addWidget(self.add_btn)

    def add_card(self, card_widget):
        self.cards_layout.insertWidget(self.cards_layout.count() - 1, card_widget)
        
    def set_count(self, count):
        self.count_badge.setText(str(count))
        
    def clear(self):
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()
            
    def dropEvent(self, event):
        task_id = event.mimeData().text()
        self.taskDropped.emit(task_id, self.title)
        event.accept()

class TasksWidget(QWidget):
    def __init__(self, auth_manager=None):
        super().__init__()
        self.auth_manager = auth_manager
        self.db = db_connection.db
        self._seed_tasks()
        
        self.setStyleSheet("QWidget { background-color: white; }")
        self.setup_ui()
        self.load_data()
        
    def _seed_tasks(self):
        if self.db.tasks.count_documents({}) == 0:
            active_inc = self.db.incidents.find_one({"status": "Active"})
            inc_id = str(active_inc["_id"]) if active_inc else None
            t = [
                {"title": "Deploy Sandbags", "description": "Deploy sandbags to river bank", "status": "To Do", "priority": "High", "assignee": "Field Team Alpha", "due_date": datetime.now() + timedelta(days=1), "incident_id": inc_id, "created_at": datetime.now()},
                {"title": "Check Water Levels", "description": "Verify sensor data downstream", "status": "In Progress", "priority": "Medium", "assignee": "John Doe", "due_date": datetime.now() + timedelta(days=2), "incident_id": inc_id, "created_at": datetime.now()},
                {"title": "Evacuation Report", "description": "Compile final numbers", "status": "Under Review", "priority": "Low", "assignee": "Admin", "due_date": datetime.now() - timedelta(days=1), "incident_id": None, "created_at": datetime.now()},
                {"title": "Refuel Generators", "description": "Camp 4 needs fuel", "status": "Done", "priority": "High", "assignee": "Logistics", "due_date": datetime.now(), "incident_id": None, "created_at": datetime.now()}
            ]
            self.db.tasks.insert_many(t)

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(24, 24, 24, 24)
        self.main_layout.setSpacing(16)
        
        # TOP TOOLBAR
        toolbar = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search tasks...")
        self.search_input.setFixedWidth(240)
        self.search_input.setFixedHeight(36)
        self.search_input.addAction(create_svg_icon('search', '#6B7280'), QLineEdit.LeadingPosition)
        self.search_input.setStyleSheet("padding: 0 8px; border: 1px solid #D1D5DB; border-radius: 18px; background: white;")
        self.search_input.textChanged.connect(self.load_data)
        toolbar.addWidget(self.search_input)
        
        self.pri_filter = QComboBox()
        self.pri_filter.addItems(["All Priorities", "High", "Medium", "Low"])
        self.pri_filter.setFixedHeight(36)
        self.pri_filter.currentTextChanged.connect(self.load_data)
        toolbar.addWidget(self.pri_filter)
        
        self.ass_filter = QLineEdit()
        self.ass_filter.setPlaceholderText("Filter by Assignee...")
        self.ass_filter.setFixedHeight(36)
        self.ass_filter.setStyleSheet("padding: 8px; border: 1px solid #D1D5DB; border-radius: 4px;")
        self.ass_filter.textChanged.connect(self.load_data)
        toolbar.addWidget(self.ass_filter)
        
        toolbar.addStretch()
        
        new_btn = QPushButton(" + New Task")
        new_btn.setFixedHeight(36)
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.setStyleSheet("background-color: #1F6FEB; color: white; font-weight: bold; padding: 0 16px; border-radius: 6px;")
        new_btn.clicked.connect(lambda: self.show_task_dialog())
        toolbar.addWidget(new_btn)
        
        self.main_layout.addLayout(toolbar)
        
        # BOARD
        board_layout = QHBoxLayout()
        board_layout.setSpacing(20)
        
        self.cols = {
            "To Do": KanbanColumn("To Do", "#F3F4F6", "#6B7280"),
            "In Progress": KanbanColumn("In Progress", "#EFF6FF", "#1F6FEB"),
            "Under Review": KanbanColumn("Under Review", "#FFFBEB", "#F59E0B"),
            "Done": KanbanColumn("Done", "#ECFDF5", "#10B981")
        }
        
        for name, col in self.cols.items():
            col.taskDropped.connect(self.move_task)
            col.add_btn.clicked.connect(lambda _, n=name: self.show_task_dialog(default_status=n))
            board_layout.addWidget(col)
            
        self.main_layout.addLayout(board_layout, stretch=1)
        
    def load_data(self):
        query = {}
        s = self.search_input.text().strip()
        if s: query["title"] = {"$regex": s, "$options": "i"}
        
        p = self.pri_filter.currentText()
        if p != "All Priorities": query["priority"] = p
        
        a = self.ass_filter.text().strip()
        if a: query["assignee"] = {"$regex": a, "$options": "i"}
        
        tasks = list(self.db.tasks.find(query).sort("created_at", -1))
        
        for col in self.cols.values():
            col.clear()
            col.set_count(0)
            
        counts = {k: 0 for k in self.cols.keys()}
        
        for task in tasks:
            status = task.get("status", "To Do")
            if status not in self.cols: status = "To Do"
            
            counts[status] += 1
            card = TaskCard(task)
            card.clicked.connect(self.show_task_dialog)
            self.cols[status].add_card(card)
            
        for status, count in counts.items():
            self.cols[status].set_count(count)

    def move_task(self, task_id, new_status):
        self.db.tasks.update_one({"_id": ObjectId(task_id)}, {"$set": {"status": new_status}})
        self.load_data()

    def show_task_dialog(self, task_data=None, default_status="To Do"):
        dialog = TaskDialog(self, task_data, default_status)
        if dialog.exec_() == QDialog.Accepted:
            self.load_data()
