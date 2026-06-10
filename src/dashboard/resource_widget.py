import os
import tempfile
import folium
from datetime import datetime
from bson.objectid import ObjectId

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QComboBox, QLineEdit, QDialog,
    QFormLayout, QMessageBox, QHeaderView, QGraphicsDropShadowEffect,
    QScrollArea, QGridLayout, QSpinBox, QAbstractItemView, QSizePolicy,
    QStackedWidget, QInputDialog, QMenu, QAction, QCheckBox, QFileDialog
)
import csv
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QByteArray, QSize, QUrl, QRect
from PyQt5.QtGui import QIcon, QFont, QColor, QPainter, QPixmap
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWebEngineWidgets import QWebEngineView

from db.connection import db_connection
from src.utils.map_generator import generate_location_picker_map

FEATHER_ICONS = {
    'search': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>',
    'plus': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>',
    'grid': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>',
    'list': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>',
    'package': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="16.5" y1="9.4" x2="7.5" y2="4.21"></line><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>',
    'eye': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>',
    'edit-2': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"></path></svg>',
    'trash-2': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>'
}

def create_svg_icon(name, color="#8B9DC3", size=24):
    svg = FEATHER_ICONS.get(name, FEATHER_ICONS['package'])
    svg = svg.replace('currentColor', color)
    renderer = QSvgRenderer(QByteArray(svg.encode('utf-8')))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)

def get_status_color(status):
    colors = { 'Available': '#27AE60', 'Deployed': '#F39C12', 'Maintenance': '#E74C3C', 'Reserved': '#8B9DC3' }
    return colors.get(status, '#95A5A6')

def create_pill_badge(text, color):
    w = QWidget()
    l = QHBoxLayout(w)
    l.setContentsMargins(4, 2, 4, 2)
    l.setAlignment(Qt.AlignCenter)
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet(f"""
        background-color: {color};
        color: white; border-radius: 10px; padding: 2px 8px; font-weight: bold; font-size: 8pt;
    """)
    l.addWidget(lbl)
    return w

class MapPickerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pick Location on Map")
        self.resize(800, 600)
        self.selected_lat = None
        self.selected_lng = None
        layout = QVBoxLayout(self)
        self.map_widget = QWebEngineView()
        self.map_widget.setHtml(generate_location_picker_map(), QUrl("about:blank"))
        layout.addWidget(self.map_widget)
        
        bottom_layout = QHBoxLayout()
        info_lbl = QLabel("Click anywhere on the map to drop a pin, then click Confirm.")
        info_lbl.setStyleSheet("color: #6C757D; font-style: italic;")
        
        confirm_btn = QPushButton("Confirm Location")
        confirm_btn.setCursor(Qt.PointingHandCursor)
        confirm_btn.setStyleSheet("padding: 8px 16px; border: none; border-radius: 4px; background: #1F6FEB; color: white; font-weight: bold;")
        confirm_btn.clicked.connect(self._on_confirm_clicked)
        
        bottom_layout.addWidget(info_lbl)
        bottom_layout.addStretch()
        bottom_layout.addWidget(confirm_btn)
        
        layout.addLayout(bottom_layout)
        
    def _on_confirm_clicked(self):
        self.map_widget.page().runJavaScript(
            "document.getElementById('selected_coordinates').innerText;",
            self._on_js_result
        )
        
    def _on_js_result(self, result):
        if result:
            try:
                lat_str, lng_str = result.split(',')
                self.selected_lat = float(lat_str)
                self.selected_lng = float(lng_str)
                self.accept()
            except Exception:
                QMessageBox.warning(self, "Error", "Please click on the map to select a location first.")
        else:
            QMessageBox.warning(self, "Error", "Please click on the map to select a location first.")

class ResourceDialog(QDialog):
    def __init__(self, parent=None, res_data=None):
        super().__init__(parent)
        self.res_data = res_data
        self.setWindowTitle("Edit Resource" if res_data else "Add New Resource")
        self.setFixedSize(480, 500)
        self.setModal(True)
        self.selected_lat = None
        self.selected_lng = None
        
        self.setStyleSheet("""
            QDialog { background-color: white; }
            QLineEdit, QComboBox, QSpinBox {
                padding: 8px; border: 1px solid #E5E7EB; border-radius: 4px; background-color: #F9FAFB;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border: 1px solid #1F6FEB; background-color: white;
            }
        """)
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        title_lbl = QLabel("Add New Resource" if not self.res_data else "Edit Resource")
        title_lbl.setStyleSheet("font-size: 16pt; font-weight: bold; color: #111827; margin-bottom: 12px;")
        layout.addWidget(title_lbl)
        
        form = QFormLayout()
        form.setSpacing(16)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Resource name")
        
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "Medical Team", "Fire Truck", "Ambulance", "Rescue Helicopter",
            "Food Supply", "Water Supply", "Shelter Materials", "Generators"
        ])
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Available", "Deployed", "Maintenance", "Reserved"])
        
        self.capacity_spin = QSpinBox()
        self.capacity_spin.setRange(1, 100000)
        
        loc_widget = QWidget()
        loc_layout = QHBoxLayout(loc_widget)
        loc_layout.setContentsMargins(0,0,0,0)
        self.loc_input = QLineEdit()
        self.loc_input.setReadOnly(True)
        self.loc_input.setPlaceholderText("Coordinates...")
        self.pick_btn = QPushButton("Pick on Map")
        self.pick_btn.setStyleSheet("background-color: #F3F4F6; color: #374151; padding: 8px; border: 1px solid #E5E7EB; border-radius: 4px;")
        self.pick_btn.setCursor(Qt.PointingHandCursor)
        self.pick_btn.clicked.connect(self._open_map_picker)
        loc_layout.addWidget(self.loc_input)
        loc_layout.addWidget(self.pick_btn)
        
        form.addRow("Name *", self.name_input)
        form.addRow("Type *", self.type_combo)
        form.addRow("Status *", self.status_combo)
        form.addRow("Capacity *", self.capacity_spin)
        form.addRow("Location *", loc_widget)
        layout.addLayout(form)
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet("padding: 8px 16px; border: 1px solid #D1D5DB; border-radius: 4px; background: white; color: #374151;")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Save Resource")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet("padding: 8px 16px; border: none; border-radius: 4px; background: #1F6FEB; color: white; font-weight: bold;")
        save_btn.clicked.connect(self._validate_and_save)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
        
        if self.res_data:
            self._populate_fields()
            
    def _populate_fields(self):
        self.name_input.setText(self.res_data.get('name', ''))
        self.type_combo.setCurrentText(self.res_data.get('type', ''))
        self.status_combo.setCurrentText(self.res_data.get('status', 'Available'))
        self.capacity_spin.setValue(self.res_data.get('capacity', 1))
        loc = self.res_data.get('location', {})
        if loc and loc.get('lat') and loc.get('lng'):
            self.selected_lat = loc.get('lat')
            self.selected_lng = loc.get('lng')
            self.loc_input.setText(f"{self.selected_lat:.4f}, {self.selected_lng:.4f}")
            
    def _open_map_picker(self):
        picker = MapPickerDialog(self)
        if picker.exec_() == QDialog.Accepted and picker.selected_lat:
            self.selected_lat = picker.selected_lat
            self.selected_lng = picker.selected_lng
            self.loc_input.setText(f"{self.selected_lat:.4f}, {self.selected_lng:.4f}")
            
    def _validate_and_save(self):
        if not self.name_input.text().strip():
            self.name_input.setStyleSheet("border: 1px solid red;")
            return
        if self.selected_lat is None:
            self.loc_input.setStyleSheet("border: 1px solid red;")
            return
        self.accept()
        
    def get_resource_data(self):
        return {
            'name': self.name_input.text().strip(),
            'type': self.type_combo.currentText(),
            'status': self.status_combo.currentText(),
            'capacity': self.capacity_spin.value(),
            'location': {
                'type': 'Point',
                'coordinates': [self.selected_lng, self.selected_lat],
                'lat': self.selected_lat,
                'lng': self.selected_lng,
                'area': 'Custom Selection'
            }
        }

class ResourceDetailDialog(QDialog):
    def __init__(self, parent=None, res_data=None):
        super().__init__(parent)
        self.db = db_connection.db
        self.res_data = res_data
        self.setWindowTitle("Resource Details")
        self.setFixedSize(480, 500)
        self.setStyleSheet("QDialog { background-color: white; }")
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel(self.res_data.get("name", ""))
        title.setStyleSheet("font-size: 16pt; font-weight: bold; color: #111827;")
        header_layout.addWidget(title)
        
        status = self.res_data.get("status", "Available")
        badge = create_pill_badge(status, get_status_color(status))
        header_layout.addWidget(badge)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Details
        grid = QGridLayout()
        grid.setSpacing(12)
        grid.addWidget(QLabel("<b>Type:</b>"), 0, 0)
        grid.addWidget(QLabel(self.res_data.get("type", "")), 0, 1)
        grid.addWidget(QLabel("<b>Capacity:</b>"), 1, 0)
        grid.addWidget(QLabel(str(self.res_data.get("capacity", ""))), 1, 1)
        
        loc = self.res_data.get("location", {})
        loc_str = f"{loc.get('lat', 0):.4f}, {loc.get('lng', 0):.4f}"
        grid.addWidget(QLabel("<b>Location:</b>"), 2, 0)
        grid.addWidget(QLabel(loc_str), 2, 1)
        layout.addLayout(grid)
        
        layout.addSpacing(20)
        
        # Actions
        if status == "Available":
            self.alloc_btn = QPushButton("Allocate to Incident")
            self.alloc_btn.setStyleSheet("padding: 10px; background-color: #1F6FEB; color: white; border-radius: 4px; font-weight: bold;")
            self.alloc_btn.clicked.connect(self._allocate)
            layout.addWidget(self.alloc_btn)
        elif status == "Deployed":
            self.ret_btn = QPushButton("Return from Deployment")
            self.ret_btn.setStyleSheet("padding: 10px; background-color: #27AE60; color: white; border-radius: 4px; font-weight: bold;")
            self.ret_btn.clicked.connect(self._return_resource)
            layout.addWidget(self.ret_btn)
            
        layout.addStretch()
        
        btns = QHBoxLayout()
        edit_btn = QPushButton("Edit")
        edit_btn.setStyleSheet("padding: 8px 16px; border: 1px solid #D1D5DB; border-radius: 4px;")
        edit_btn.clicked.connect(self._edit)
        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet("padding: 8px 16px; border: none; background: #FEF2F2; color: #DC2626; border-radius: 4px;")
        delete_btn.clicked.connect(self._delete)
        
        btns.addWidget(edit_btn)
        btns.addWidget(delete_btn)
        layout.addLayout(btns)
        
    def _allocate(self):
        incidents = list(self.db.incidents.find({"status": {"$in": ["Active", "In Progress"]}}))
        if not incidents:
            QMessageBox.information(self, "No Incidents", "There are no active incidents to allocate to.")
            return
            
        incident_names = [inc["title"] for inc in incidents]
        item, ok = QInputDialog.getItem(self, "Allocate to Incident", "Select Active Incident:", incident_names, 0, False)
        
        if ok and item:
            self.db.resources.update_one({"_id": self.res_data["_id"]}, {"$set": {"status": "Deployed", "allocated_to": item}})
            self.accept()
            
    def _return_resource(self):
        self.db.resources.update_one({"_id": self.res_data["_id"]}, {"$set": {"status": "Available", "allocated_to": None}})
        self.accept()
        
    def _edit(self):
        self.done(2) # Custom code for edit
        
    def _delete(self):
        reply = QMessageBox.question(self, "Confirm Delete", "Are you sure you want to delete this resource?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.resources.delete_one({"_id": self.res_data["_id"]})
            self.accept()

class ResourceCard(QFrame):
    clicked = pyqtSignal(object)
    
    def __init__(self, res_data):
        super().__init__()
        self.res_data = res_data
        self.setMinimumSize(200, 160)
        self.setCursor(Qt.PointingHandCursor)
        
        status = res_data.get("status", "Available")
        color = get_status_color(status)
        
        self.setStyleSheet(f"""
            ResourceCard {{
                background-color: white;
                border-radius: 8px;
                border: 1px solid #E5E7EB;
            }}
            ResourceCard:hover {{
                border: 2px solid #1F6FEB;
            }}
        """)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        color_strip = QFrame()
        color_strip.setFixedHeight(4)
        color_strip.setStyleSheet(f"background-color: {color}; border-top-left-radius: 8px; border-top-right-radius: 8px;")
        layout.addWidget(color_strip)
        
        content = QWidget()
        c_layout = QVBoxLayout(content)
        c_layout.setContentsMargins(12, 12, 12, 12)
        
        top_layout = QHBoxLayout()
        icon_lbl = QLabel()
        icon_lbl.setPixmap(create_svg_icon('package', '#6C757D', 32).pixmap(32, 32))
        top_layout.addStretch()
        top_layout.addWidget(icon_lbl)
        top_layout.addStretch()
        
        self.checkbox = QCheckBox()
        self.checkbox.setStyleSheet("QCheckBox::indicator { width: 18px; height: 18px; }")
        top_layout.addWidget(self.checkbox, alignment=Qt.AlignTop | Qt.AlignRight)
        c_layout.addLayout(top_layout)
        
        name_lbl = QLabel(res_data.get("name", ""))
        name_lbl.setStyleSheet("font-size: 11pt; font-weight: bold; color: #111827;")
        name_lbl.setAlignment(Qt.AlignCenter)
        c_layout.addWidget(name_lbl)
        
        meta_lbl = QLabel(f"{res_data.get('type', '')} • Cap: {res_data.get('capacity', '')}")
        meta_lbl.setStyleSheet("color: #6B7280; font-size: 9pt;")
        meta_lbl.setAlignment(Qt.AlignCenter)
        c_layout.addWidget(meta_lbl)
        
        c_layout.addStretch()
        
        btm_layout = QHBoxLayout()
        badge = create_pill_badge(status, color)
        btm_layout.addWidget(badge)
        btm_layout.addStretch()
        
        loc_lbl = QLabel("Lat: {:.4f}".format(res_data.get("location", {}).get("lat", 0)))
        loc_lbl.setStyleSheet("color: #9CA3AF; font-size: 8pt;")
        btm_layout.addWidget(loc_lbl)
        c_layout.addLayout(btm_layout)
        
        layout.addWidget(content)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.res_data)
        super().mousePressEvent(event)
        
    def enterEvent(self, event):
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(150)
        rect = self.geometry()
        self.anim.setStartValue(rect)
        self.anim.setEndValue(QRect(rect.x() - 2, rect.y() - 2, rect.width() + 4, rect.height() + 4))
        self.anim.start()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(150)
        rect = self.geometry()
        self.anim.setStartValue(rect)
        self.anim.setEndValue(QRect(rect.x() + 2, rect.y() + 2, rect.width() - 4, rect.height() - 4))
        self.anim.start()
        super().leaveEvent(event)

class ResourceWidget(QWidget):
    def __init__(self, auth_manager=None):
        super().__init__()
        self.auth_manager = auth_manager
        self.db = db_connection.db
        
        self.setStyleSheet("QWidget { background-color: #F3F4F6; }")
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(24, 24, 24, 24)
        self.main_layout.setSpacing(16)
        
        # TOP TOOLBAR
        toolbar = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search resources...")
        self.search_input.setFixedWidth(260)
        self.search_input.setFixedHeight(36)
        self.search_input.addAction(create_svg_icon('search', '#6B7280'), QLineEdit.LeadingPosition)
        self.search_input.setStyleSheet("padding: 0 8px; border: 1px solid #D1D5DB; border-radius: 18px; background: white;")
        self.search_input.textChanged.connect(self.load_data)
        toolbar.addWidget(self.search_input)
        
        self.type_filter = QComboBox()
        self.type_filter.addItems(["All", "Medical Team", "Fire Truck", "Ambulance", "Rescue Helicopter", "Food Supply", "Water Supply", "Shelter Materials", "Generators"])
        self.type_filter.setFixedHeight(36)
        self.type_filter.currentTextChanged.connect(self.load_data)
        toolbar.addWidget(self.type_filter)
        
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Available", "Deployed", "Maintenance", "Reserved"])
        self.status_filter.setFixedHeight(36)
        self.status_filter.currentTextChanged.connect(self.load_data)
        toolbar.addWidget(self.status_filter)
        
        toolbar.addStretch()
        
        # Bulk Actions Button
        self.bulk_btn = QPushButton("Bulk Actions")
        self.bulk_btn.setStyleSheet("background-color: white; color: #374151; padding: 0 16px; border: 1px solid #D1D5DB; border-radius: 6px; font-weight: bold;")
        self.bulk_btn.setFixedHeight(36)
        self.bulk_btn.setCursor(Qt.PointingHandCursor)
        self.bulk_menu = QMenu(self.bulk_btn)
        
        export_act = QAction("Export Selected to CSV", self)
        export_act.triggered.connect(self._bulk_export_csv)
        self.bulk_menu.addAction(export_act)
        
        del_act = QAction("Delete Selected", self)
        del_act.triggered.connect(self._bulk_delete)
        self.bulk_menu.addAction(del_act)
        
        self.bulk_menu.addSeparator()
        
        for st in ["Available", "Deployed", "Maintenance", "Reserved"]:
            act = QAction(f"Mark as {st}", self)
            act.triggered.connect(lambda checked, s=st: self._bulk_update_status(s))
            self.bulk_menu.addAction(act)
            
        self.bulk_btn.setMenu(self.bulk_menu)
        toolbar.addWidget(self.bulk_btn)
        
        export_btn = QPushButton("Export All to CSV")
        export_btn.setStyleSheet("color: #6C757D; border: none; font-weight: bold;")
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.clicked.connect(self.export_csv)
        toolbar.addWidget(export_btn)
        
        toolbar.addSpacing(16)
        
        self.btn_grid = QPushButton()
        self.btn_grid.setIcon(create_svg_icon('grid', '#1F6FEB'))
        self.btn_grid.setFixedSize(36, 36)
        self.btn_grid.setStyleSheet("border: 1px solid #1F6FEB; background: #EFF6FF; border-radius: 4px;")
        self.btn_grid.setCursor(Qt.PointingHandCursor)
        self.btn_grid.clicked.connect(lambda: self._set_view(0))
        
        self.btn_list = QPushButton()
        self.btn_list.setIcon(create_svg_icon('list', '#6C757D'))
        self.btn_list.setFixedSize(36, 36)
        self.btn_list.setStyleSheet("border: 1px solid #D1D5DB; background: white; border-radius: 4px;")
        self.btn_list.setCursor(Qt.PointingHandCursor)
        self.btn_list.clicked.connect(lambda: self._set_view(1))
        
        toolbar.addWidget(self.btn_grid)
        toolbar.addWidget(self.btn_list)
        
        toolbar.addSpacing(16)
        
        new_btn = QPushButton(" + Add Resource")
        new_btn.setFixedHeight(36)
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.setStyleSheet("background-color: #1F6FEB; color: white; font-weight: bold; padding: 0 16px; border-radius: 6px;")
        new_btn.clicked.connect(self.show_resource_dialog)
        toolbar.addWidget(new_btn)
        
        self.main_layout.addLayout(toolbar)
        
        # VIEWS STACK
        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack, stretch=1)
        
        # 0: CARD VIEW
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(0,0,0,0)
        self.grid_layout.setSpacing(20)
        
        self.scroll_area.setWidget(self.grid_container)
        self.stack.addWidget(self.scroll_area)
        
        # 1: LIST VIEW
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["ID", "", "Name", "Type", "Status", "Capacity", "Location", "Actions"])
        self.table.setColumnHidden(0, True)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents) # Checkbox
        header.setSectionResizeMode(2, QHeaderView.Stretch)          # Name
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        header.sectionClicked.connect(self._on_header_clicked)
        
        self.table.setStyleSheet("""
            QTableWidget { border: none; background: white; border-radius: 8px; alternate-background-color: #F8F9FA; }
            QHeaderView::section { background-color: white; padding: 12px; border: none; border-bottom: 2px solid #E5E7EB; font-weight: bold; color: #6B7280; text-align: left; }
            QTableWidget::item { padding: 8px 12px; border-bottom: 1px solid #F3F4F6; }
            QTableWidget::item:selected { background-color: #EFF6FF; color: black; }
            QTableWidget::indicator { width: 18px; height: 18px; }
        """)
        self.table.cellClicked.connect(self._on_table_click)
        self.stack.addWidget(self.table)
        
    def _set_view(self, index):
        self.stack.setCurrentIndex(index)
        if index == 0:
            self.btn_grid.setStyleSheet("border: 1px solid #1F6FEB; background: #EFF6FF; border-radius: 4px;")
            self.btn_grid.setIcon(create_svg_icon('grid', '#1F6FEB'))
            self.btn_list.setStyleSheet("border: 1px solid #D1D5DB; background: white; border-radius: 4px;")
            self.btn_list.setIcon(create_svg_icon('list', '#6C757D'))
        else:
            self.btn_list.setStyleSheet("border: 1px solid #1F6FEB; background: #EFF6FF; border-radius: 4px;")
            self.btn_list.setIcon(create_svg_icon('list', '#1F6FEB'))
            self.btn_grid.setStyleSheet("border: 1px solid #D1D5DB; background: white; border-radius: 4px;")
            self.btn_grid.setIcon(create_svg_icon('grid', '#6C757D'))

    def load_data(self):
        query = {}
        s = self.search_input.text().strip()
        if s: query["name"] = {"$regex": s, "$options": "i"}
        t = self.type_filter.currentText()
        if t != "All": query["type"] = t
        st = self.status_filter.currentText()
        if st != "All": query["status"] = st
            
        items = list(self.db.resources.find(query).sort("name", 1))
        
        # Grid View Update
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        self.cards = []
        row, col = 0, 0
        for item in items:
            card = ResourceCard(item)
            card.clicked.connect(self.show_resource_detail)
            self.cards.append(card)
            self.grid_layout.addWidget(card, row, col)
            col += 1
            if col > 2:
                col = 0
                row += 1
                
        # Fill empty space so cards don't stretch to infinity
        self.grid_layout.setRowStretch(row + 1, 1)
        
        # List View Update
        self.table.setRowCount(0)
        for row_idx, res in enumerate(items):
            self.table.insertRow(row_idx)
            self.table.setRowHeight(row_idx, 48)
            
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(res["_id"])))
            
            chk_item = QTableWidgetItem()
            chk_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            chk_item.setCheckState(Qt.Unchecked)
            self.table.setItem(row_idx, 1, chk_item)
            
            self.table.setItem(row_idx, 2, QTableWidgetItem(res.get("name", "")))
            self.table.setItem(row_idx, 3, QTableWidgetItem(res.get("type", "")))
            
            status = res.get("status", "Available")
            self.table.setCellWidget(row_idx, 4, create_pill_badge(status, get_status_color(status)))
            
            self.table.setItem(row_idx, 5, QTableWidgetItem(str(res.get("capacity", ""))))
            loc = res.get("location", {})
            self.table.setItem(row_idx, 6, QTableWidgetItem(f"{loc.get('lat', 0):.4f}, {loc.get('lng', 0):.4f}"))
            
            # Actions
            action_w = QWidget()
            action_l = QHBoxLayout(action_w)
            action_l.setContentsMargins(4,4,4,4)
            action_l.setSpacing(4)
            
            btn_view = QPushButton()
            btn_view.setIcon(create_svg_icon('eye', '#1F6FEB'))
            btn_view.setStyleSheet("border: none; background: transparent;")
            btn_view.setCursor(Qt.PointingHandCursor)
            btn_view.clicked.connect(lambda _, r=res: self.show_resource_detail(r))
            
            action_l.addWidget(btn_view)
            self.table.setCellWidget(row_idx, 7, action_w)
            
    def _on_table_click(self, row, col):
        if col not in (1, 7):
            res_id = self.table.item(row, 0).text()
            res = self.db.resources.find_one({"_id": ObjectId(res_id)})
            if res: self.show_resource_detail(res)
            
    def _on_header_clicked(self, logical_index):
        if logical_index == 1:
            all_checked = True
            for r in range(self.table.rowCount()):
                if self.table.item(r, 1).checkState() == Qt.Unchecked:
                    all_checked = False
                    break
            new_state = Qt.Unchecked if all_checked else Qt.Checked
            for r in range(self.table.rowCount()):
                self.table.item(r, 1).setCheckState(new_state)

    def show_resource_dialog(self, res_data=None):
        dialog = ResourceDialog(self, res_data)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_resource_data()
            if res_data:
                self.db.resources.update_one({"_id": res_data["_id"]}, {"$set": data})
            else:
                self.db.resources.insert_one(data)
            self.load_data()

    def show_resource_detail(self, res_data):
        dialog = ResourceDetailDialog(self, res_data)
        res_code = dialog.exec_()
        
        if res_code == 2: # Custom code for Edit
            self.show_resource_dialog(res_data)
        elif res_code == QDialog.Accepted:
            self.load_data()

    def _get_selected_ids(self):
        selected = []
        if self.stack.currentIndex() == 0:
            # Grid View
            for card in getattr(self, "cards", []):
                if card.checkbox.isChecked():
                    selected.append(card.res_data["_id"])
        else:
            # List View
            for r in range(self.table.rowCount()):
                if self.table.item(r, 1).checkState() == Qt.Checked:
                    selected.append(ObjectId(self.table.item(r, 0).text()))
        return selected

    def _bulk_delete(self):
        ids = self._get_selected_ids()
        if not ids:
            QMessageBox.warning(self, "No Selection", "Please select at least one resource.")
            return
            
        reply = QMessageBox.question(self, "Confirm Delete", f"Are you sure you want to delete {len(ids)} selected resource(s)?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.resources.delete_many({"_id": {"$in": ids}})
            self.load_data()

    def _bulk_update_status(self, new_status):
        ids = self._get_selected_ids()
        if not ids:
            QMessageBox.warning(self, "No Selection", "Please select at least one resource.")
            return
            
        self.db.resources.update_many({"_id": {"$in": ids}}, {"$set": {"status": new_status}})
        self.load_data()

    def _build_query(self):
        query = {}
        s = self.search_input.text().strip()
        if s: query["name"] = {"$regex": s, "$options": "i"}
        t = self.type_filter.currentText()
        if t != "All": query["type"] = t
        st = self.status_filter.currentText()
        if st != "All": query["status"] = st
        return query

    def export_csv(self):
        self._export_to_csv(list(self.db.resources.find(self._build_query())))

    def _bulk_export_csv(self):
        ids = self._get_selected_ids()
        if not ids:
            QMessageBox.warning(self, "No Selection", "Please select at least one resource.")
            return
        self._export_to_csv(list(self.db.resources.find({"_id": {"$in": ids}})))

    def _export_to_csv(self, records):
        if not records:
            QMessageBox.warning(self, "No Data", "There are no resources to export.")
            return
            
        path, _ = QFileDialog.getSaveFileName(self, "Export Resources", "", "CSV Files (*.csv)")
        if not path: return
        
        with open(path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Name", "Type", "Status", "Capacity", "Location"])
            for res in records:
                loc = res.get("location", {})
                loc_str = f"{loc.get('lat', 0):.4f}, {loc.get('lng', 0):.4f}"
                writer.writerow([
                    str(res["_id"]),
                    res.get("name", ""),
                    res.get("type", ""),
                    res.get("status", ""),
                    str(res.get("capacity", "")),
                    loc_str
                ])
        QMessageBox.information(self, "Export Successful", f"Exported to {path}")
