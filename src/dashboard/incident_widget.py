import os
import json
import csv
import tempfile
import folium
from datetime import datetime
from bson.objectid import ObjectId

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QComboBox, QLineEdit, QDialog,
    QFormLayout, QTextEdit, QMessageBox, QHeaderView, QGraphicsDropShadowEffect,
    QSplitter, QFileDialog, QAbstractItemView, QSizePolicy, QMenu, QAction
)
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QByteArray, QSize, QUrl
from PyQt5.QtGui import QIcon, QFont, QColor, QPainter, QPixmap
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWebEngineWidgets import QWebEngineView

from db.connection import db_connection
from src.utils.map_generator import generate_incident_location_thumbnail, generate_location_picker_map

FEATHER_ICONS = {
    'search': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>',
    'plus': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>',
    'download': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>',
    'eye': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>',
    'edit-2': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"></path></svg>',
    'trash-2': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>',
    'map-pin': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>',
    'x': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>',
    'chevron-left': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>',
    'chevron-right': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>'
}

def create_svg_icon(name, color="#8B9DC3"):
    svg = FEATHER_ICONS.get(name, FEATHER_ICONS['x'])
    svg = svg.replace('currentColor', color)
    renderer = QSvgRenderer(QByteArray(svg.encode('utf-8')))
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)

def get_severity_color(severity):
    colors = { 'Critical': '#E74C3C', 'High': '#F39C12', 'Medium': '#3498DB', 'Low': '#27AE60' }
    return colors.get(severity, '#95A5A6')

def get_status_color(status):
    colors = { 'Active': '#E74C3C', 'In Progress': '#F39C12', 'Resolved': '#27AE60', 'Under Review': '#8E44AD' }
    return colors.get(status, '#95A5A6')

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

class IncidentDialog(QDialog):
    def __init__(self, parent=None, incident_data=None):
        super().__init__(parent)
        self.incident_data = incident_data
        self.setWindowTitle("Edit Incident" if incident_data else "Report New Incident")
        self.setFixedSize(520, 600)
        self.setModal(True)
        
        self.selected_lat = None
        self.selected_lng = None
        
        self.setStyleSheet("""
            QDialog { background-color: white; }
            QLineEdit, QComboBox, QTextEdit {
                padding: 8px; border: 1px solid #E5E7EB; border-radius: 4px; background-color: #F9FAFB;
            }
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
                border: 1px solid #1F6FEB; background-color: white;
            }
        """)
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        
        title_lbl = QLabel("Report New Incident" if not self.incident_data else "Edit Incident")
        title_lbl.setStyleSheet("font-size: 16pt; font-weight: bold; color: #111827; margin-bottom: 12px;")
        layout.addWidget(title_lbl)
        
        form = QFormLayout()
        form.setSpacing(16)
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Incident title")
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Flood", "Fire"])
        
        self.severity_combo = QComboBox()
        self.severity_combo.addItems(["Low", "Medium", "High", "Critical"])
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Active", "In Progress", "Resolved", "Under Review"])
        
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Detailed description of the incident...")
        self.desc_input.setMinimumHeight(100)
        
        # Location Picker
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
        
        form.addRow("Title *", self.title_input)
        form.addRow("Type *", self.type_combo)
        form.addRow("Severity *", self.severity_combo)
        form.addRow("Status *", self.status_combo)
        form.addRow("Description *", self.desc_input)
        form.addRow("Location *", loc_widget)
        
        layout.addLayout(form)
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet("padding: 8px 16px; border: 1px solid #D1D5DB; border-radius: 4px; background: white; color: #374151;")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Save Incident")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet("padding: 8px 16px; border: none; border-radius: 4px; background: #1F6FEB; color: white; font-weight: bold;")
        save_btn.clicked.connect(self._validate_and_save)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
        
        if self.incident_data:
            self._populate_fields()
            
    def _populate_fields(self):
        self.title_input.setText(self.incident_data.get('title', ''))
        self.type_combo.setCurrentText(self.incident_data.get('type', 'Flood'))
        self.severity_combo.setCurrentText(self.incident_data.get('severity', 'Medium'))
        self.status_combo.setCurrentText(self.incident_data.get('status', 'Active'))
        self.desc_input.setText(self.incident_data.get('description', ''))
        loc = self.incident_data.get('location', {})
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
        # Basic validation
        if not self.title_input.text().strip():
            self.title_input.setStyleSheet("border: 1px solid red;")
            self.title_input.setToolTip("Title is required")
            return
        if not self.desc_input.toPlainText().strip():
            self.desc_input.setStyleSheet("border: 1px solid red;")
            return
        if self.selected_lat is None:
            self.loc_input.setStyleSheet("border: 1px solid red;")
            return
            
        self.accept()
        
    def get_incident_data(self):
        return {
            'title': self.title_input.text().strip(),
            'type': self.type_combo.currentText(),
            'severity': self.severity_combo.currentText(),
            'status': self.status_combo.currentText(),
            'description': self.desc_input.toPlainText().strip(),
            'location': {
                'type': 'Point',
                'coordinates': [self.selected_lng, self.selected_lat],
                'lat': self.selected_lat,
                'lng': self.selected_lng,
                'area': 'Custom Selection'
            }
        }

def create_pill_badge(text, color):
    w = QWidget()
    l = QHBoxLayout(w)
    l.setContentsMargins(4, 2, 4, 2)
    l.setAlignment(Qt.AlignCenter)
    
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet(f"""
        background-color: {color};
        color: white;
        border-radius: 10px;
        padding: 2px 8px;
        font-weight: bold;
        font-size: 8pt;
    """)
    l.addWidget(lbl)
    return w

class IncidentWidget(QWidget):
    def __init__(self, auth_manager=None):
        super().__init__()
        self.auth_manager = auth_manager
        self.db = db_connection.db
        
        self.current_page = 1
        self.items_per_page = 10
        self.total_pages = 1
        self.current_sort = ("created_at", -1)
        self.selected_incident = None
        
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
        self.search_input.setPlaceholderText("Search incidents...")
        self.search_input.setFixedWidth(260)
        self.search_input.setFixedHeight(36)
        self.search_input.addAction(create_svg_icon('search', '#6B7280'), QLineEdit.LeadingPosition)
        self.search_input.setStyleSheet("padding: 0 8px; border: 1px solid #D1D5DB; border-radius: 18px; background: white;")
        self.search_input.textChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self.search_input)
        
        self.sev_filter = QComboBox()
        self.sev_filter.addItems(["All", "Critical", "High", "Medium", "Low"])
        self.sev_filter.setFixedHeight(36)
        self.sev_filter.currentTextChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self.sev_filter)
        
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Active", "In Progress", "Resolved", "Under Review"])
        self.status_filter.setFixedHeight(36)
        self.status_filter.currentTextChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self.status_filter)
        
        self.type_filter = QComboBox()
        self.type_filter.addItems(["All", "Flood", "Fire"])
        self.type_filter.setFixedHeight(36)
        self.type_filter.currentTextChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self.type_filter)
        
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
        
        for st in ["Active", "In Progress", "Resolved", "Under Review"]:
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
        
        new_btn = QPushButton(" + New Incident")
        new_btn.setFixedHeight(36)
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.setStyleSheet("background-color: #1F6FEB; color: white; font-weight: bold; padding: 0 16px; border-radius: 6px;")
        new_btn.clicked.connect(self.show_incident_dialog)
        toolbar.addWidget(new_btn)
        
        self.main_layout.addLayout(toolbar)
        
        # SPLITTER FOR TABLE AND DRAWER
        self.splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.splitter, stretch=1)
        
        # LEFT: TABLE + PAGINATION
        table_container = QWidget()
        table_container.setStyleSheet("background: white; border-radius: 8px;")
        tc_layout = QVBoxLayout(table_container)
        tc_layout.setContentsMargins(0,0,0,0)
        tc_layout.setSpacing(0)
        
        self.table = QTableWidget()
        self.table.setColumnCount(9) # Hidden ID column at 0
        self.table.setHorizontalHeaderLabels(["ID", "", "#", "Title", "Type", "Severity", "Status", "Reported", "Actions"])
        self.table.setColumnHidden(0, True)
        
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents) # Checkbox
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents) # #
        header.setSectionResizeMode(3, QHeaderView.Stretch)          # Title
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)
        header.sectionClicked.connect(self._on_header_clicked)
        
        self.table.setStyleSheet("""
            QTableWidget { border: none; background: white; border-radius: 8px; alternate-background-color: #F8F9FA; }
            QHeaderView::section { background-color: white; padding: 12px; border: none; border-bottom: 2px solid #E5E7EB; font-weight: bold; color: #6B7280; text-align: left; }
            QTableWidget::item { padding: 8px 12px; border-bottom: 1px solid #F3F4F6; }
            QTableWidget::item:selected { background-color: #EFF6FF; color: black; }
            QTableWidget::indicator { width: 18px; height: 18px; }
        """)
        
        self.table.cellClicked.connect(self._on_cell_clicked)
        tc_layout.addWidget(self.table)
        
        # Pagination
        pag_bar = QWidget()
        pag_bar.setStyleSheet("background: white; border-top: 1px solid #E5E7EB; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px;")
        pag_layout = QHBoxLayout(pag_bar)
        
        self.lbl_page_info = QLabel("Showing 1 to 10 of X results")
        self.lbl_page_info.setStyleSheet("color: #6B7280; font-size: 9pt;")
        pag_layout.addWidget(self.lbl_page_info)
        pag_layout.addStretch()
        
        self.btn_prev = QPushButton("Previous")
        self.btn_prev.setCursor(Qt.PointingHandCursor)
        self.btn_prev.setStyleSheet("padding: 6px 12px; border: 1px solid #E5E7EB; border-radius: 4px; background: white;")
        self.btn_prev.clicked.connect(self._prev_page)
        
        self.lbl_page_num = QLabel(" 1 ")
        self.lbl_page_num.setStyleSheet("font-weight: bold; color: #111827;")
        
        self.btn_next = QPushButton("Next")
        self.btn_next.setCursor(Qt.PointingHandCursor)
        self.btn_next.setStyleSheet("padding: 6px 12px; border: 1px solid #E5E7EB; border-radius: 4px; background: white;")
        self.btn_next.clicked.connect(self._next_page)
        
        pag_layout.addWidget(self.btn_prev)
        pag_layout.addWidget(self.lbl_page_num)
        pag_layout.addWidget(self.btn_next)
        
        tc_layout.addWidget(pag_bar)
        
        self.splitter.addWidget(table_container)
        
        # RIGHT: DETAIL DRAWER
        self.drawer = QFrame()
        self.drawer.setMaximumWidth(0) # start hidden
        self.drawer.setStyleSheet("background: white; border-radius: 8px;")
        dr_layout = QVBoxLayout(self.drawer)
        dr_layout.setContentsMargins(20, 20, 20, 20)
        dr_layout.setSpacing(12)
        
        dr_top = QHBoxLayout()
        self.dr_title = QLabel("Incident Title")
        self.dr_title.setStyleSheet("font-size: 14pt; font-weight: bold; color: #111827;")
        self.dr_title.setWordWrap(True)
        dr_close = QPushButton()
        dr_close.setIcon(create_svg_icon('x', '#6B7280'))
        dr_close.setFixedSize(24, 24)
        dr_close.setStyleSheet("border: none;")
        dr_close.setCursor(Qt.PointingHandCursor)
        dr_close.clicked.connect(self.close_drawer)
        dr_top.addWidget(self.dr_title)
        dr_top.addWidget(dr_close, alignment=Qt.AlignTop)
        dr_layout.addLayout(dr_top)
        
        self.dr_badges = QHBoxLayout()
        dr_layout.addLayout(self.dr_badges)
        
        self.dr_desc = QLabel("Description goes here...")
        self.dr_desc.setWordWrap(True)
        self.dr_desc.setStyleSheet("color: #4B5563; font-size: 10pt; margin-top: 10px;")
        dr_layout.addWidget(self.dr_desc)
        
        self.dr_map = QWebEngineView()
        self.dr_map.setFixedSize(300, 160)
        dr_layout.addWidget(self.dr_map)
        
        dr_layout.addStretch()
        
        self.dr_dates = QLabel("Created: ...\nUpdated: ...")
        self.dr_dates.setStyleSheet("color: #9CA3AF; font-size: 9pt;")
        dr_layout.addWidget(self.dr_dates)
        
        dr_btns = QHBoxLayout()
        self.dr_btn_edit = QPushButton("Edit")
        self.dr_btn_edit.setStyleSheet("padding: 8px; border: 1px solid #E5E7EB; border-radius: 4px;")
        self.dr_btn_edit.clicked.connect(lambda: self.show_incident_dialog(self.selected_incident))
        self.dr_btn_delete = QPushButton("Delete")
        self.dr_btn_delete.setStyleSheet("padding: 8px; border: none; background: #FEF2F2; color: #DC2626; border-radius: 4px;")
        self.dr_btn_delete.clicked.connect(lambda: self.delete_incident(str(self.selected_incident['_id'])))
        dr_btns.addWidget(self.dr_btn_edit)
        dr_btns.addWidget(self.dr_btn_delete)
        dr_layout.addLayout(dr_btns)
        
        self.splitter.addWidget(self.drawer)
        
    def _build_query(self):
        query = {}
        s = self.search_input.text().strip()
        if s:
            query["title"] = {"$regex": s, "$options": "i"}
        
        sev = self.sev_filter.currentText()
        if sev != "All": query["severity"] = sev
        
        stat = self.status_filter.currentText()
        if stat != "All": query["status"] = stat
        
        typ = self.type_filter.currentText()
        if typ != "All": query["type"] = typ
            
        return query

    def load_data(self):
        query = self._build_query()
        total = self.db.incidents.count_documents(query)
        self.total_pages = max(1, (total + self.items_per_page - 1) // self.items_per_page)
        
        if self.current_page > self.total_pages:
            self.current_page = self.total_pages
            
        cursor = self.db.incidents.find(query)
        if self.current_sort:
            cursor = cursor.sort(self.current_sort[0], self.current_sort[1])
            
        cursor = cursor.skip((self.current_page - 1) * self.items_per_page).limit(self.items_per_page)
        items = list(cursor)
        
        self.table.setRowCount(0)
        for idx, inc in enumerate(items):
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setRowHeight(row, 48)
            
            # 0: ID
            self.table.setItem(row, 0, QTableWidgetItem(str(inc["_id"])))
            
            # 1: Checkbox
            chk_item = QTableWidgetItem()
            chk_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            chk_item.setCheckState(Qt.Unchecked)
            self.table.setItem(row, 1, chk_item)
            
            # 2: #
            num_item = QTableWidgetItem(str((self.current_page - 1) * self.items_per_page + idx + 1))
            num_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, num_item)
            
            # 3: Title
            title_item = QTableWidgetItem(inc.get("title", ""))
            self.table.setItem(row, 3, title_item)
            
            # 4: Type
            self.table.setItem(row, 4, QTableWidgetItem(inc.get("type", "")))
            
            # 5: Severity Badge
            sev = inc.get("severity", "Low")
            self.table.setCellWidget(row, 5, create_pill_badge(sev, get_severity_color(sev)))
            
            # 6: Status Badge
            stat = inc.get("status", "Active")
            self.table.setCellWidget(row, 6, create_pill_badge(stat, get_status_color(stat)))
            
            # 7: Reported
            dt = inc.get("created_at")
            dt_str = dt.strftime("%Y-%m-%d %H:%M") if dt else "Unknown"
            self.table.setItem(row, 7, QTableWidgetItem(dt_str))
            
            # 8: Actions
            action_w = QWidget()
            action_l = QHBoxLayout(action_w)
            action_l.setContentsMargins(4,4,4,4)
            action_l.setSpacing(4)
            
            btn_view = QPushButton()
            btn_view.setIcon(create_svg_icon('eye', '#1F6FEB'))
            btn_view.setStyleSheet("border: none; background: transparent;")
            btn_view.setCursor(Qt.PointingHandCursor)
            btn_view.clicked.connect(lambda _, _id=inc["_id"]: self.open_drawer(_id))
            
            btn_edit = QPushButton()
            btn_edit.setIcon(create_svg_icon('edit-2', '#F39C12'))
            btn_edit.setStyleSheet("border: none; background: transparent;")
            btn_edit.setCursor(Qt.PointingHandCursor)
            btn_edit.clicked.connect(lambda _, i=inc: self.show_incident_dialog(i))
            
            btn_del = QPushButton()
            btn_del.setIcon(create_svg_icon('trash-2', '#E74C3C'))
            btn_del.setStyleSheet("border: none; background: transparent;")
            btn_del.setCursor(Qt.PointingHandCursor)
            btn_del.clicked.connect(lambda _, _id=str(inc["_id"]): self.delete_incident(_id))
            
            action_l.addWidget(btn_view)
            action_l.addWidget(btn_edit)
            action_l.addWidget(btn_del)
            
            self.table.setCellWidget(row, 8, action_w)
            
        # Update pagination controls
        start_item = (self.current_page - 1) * self.items_per_page + 1 if total > 0 else 0
        end_item = min(self.current_page * self.items_per_page, total)
        self.lbl_page_info.setText(f"Showing {start_item} to {end_item} of {total} results")
        self.lbl_page_num.setText(f" {self.current_page} ")
        self.btn_prev.setEnabled(self.current_page > 1)
        self.btn_next.setEnabled(self.current_page < self.total_pages)

    def _on_filter_changed(self):
        self.current_page = 1
        self.load_data()
        
    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_data()
            
    def _next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_data()
            
    def _on_header_clicked(self, logical_index):
        cols_map = {3: "title", 4: "type", 5: "severity", 6: "status", 7: "created_at"}
        if logical_index == 1:
            # Toggle select all
            all_checked = True
            for r in range(self.table.rowCount()):
                if self.table.item(r, 1).checkState() == Qt.Unchecked:
                    all_checked = False
                    break
            new_state = Qt.Unchecked if all_checked else Qt.Checked
            for r in range(self.table.rowCount()):
                self.table.item(r, 1).setCheckState(new_state)
            return

        if logical_index in cols_map:
            field = cols_map[logical_index]
            direction = 1
            if self.current_sort and self.current_sort[0] == field:
                direction = -1 if self.current_sort[1] == 1 else 1
            self.current_sort = (field, direction)
            self.load_data()

    def _on_cell_clicked(self, row, col):
        if col not in (1, 8): # If not actions or checkbox column
            inc_id = self.table.item(row, 0).text()
            self.open_drawer(ObjectId(inc_id))

    def open_drawer(self, incident_id):
        inc = self.db.incidents.find_one({"_id": ObjectId(incident_id)})
        if not inc: return
        self.selected_incident = inc
        
        self.dr_title.setText(inc.get("title", ""))
        
        # Clear old badges
        while self.dr_badges.count():
            item = self.dr_badges.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        self.dr_badges.addWidget(create_pill_badge(inc.get("type", ""), "#6C757D"))
        self.dr_badges.addWidget(create_pill_badge(inc.get("severity", ""), get_severity_color(inc.get("severity"))))
        self.dr_badges.addWidget(create_pill_badge(inc.get("status", ""), get_status_color(inc.get("status"))))
        self.dr_badges.addStretch()
        
        self.dr_desc.setText(inc.get("description", ""))
        
        dt = inc.get("created_at")
        self.dr_dates.setText(f"Reported: {dt.strftime('%Y-%m-%d %H:%M') if dt else 'Unknown'}")
        
        # Draw Mini Folium Map
        lat = inc.get("location", {}).get("lat", 0)
        lng = inc.get("location", {}).get("lng", 0)
        html = generate_incident_location_thumbnail(lat, lng, inc.get("title", "Incident"))
        self.dr_map.setHtml(html, QUrl("about:blank"))
        
        # Animate Open
        if self.drawer.width() == 0:
            self.anim = QPropertyAnimation(self.drawer, b"maximumWidth")
            self.anim.setDuration(250)
            self.anim.setStartValue(0)
            self.anim.setEndValue(340)
            self.anim.setEasingCurve(QEasingCurve.OutCubic)
            self.anim.start()

    def close_drawer(self):
        self.anim = QPropertyAnimation(self.drawer, b"maximumWidth")
        self.anim.setDuration(250)
        self.anim.setStartValue(self.drawer.width())
        self.anim.setEndValue(0)
        self.anim.setEasingCurve(QEasingCurve.InCubic)
        self.anim.start()

    def show_incident_dialog(self, incident_data=None):
        dialog = IncidentDialog(self, incident_data)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_incident_data()
            if not data.get("created_at") and not incident_data:
                data["created_at"] = datetime.now()
            
            if incident_data:
                self.db.incidents.update_one({"_id": incident_data["_id"]}, {"$set": data})
            else:
                self.db.incidents.insert_one(data)
                
            self.load_data()
            if self.selected_incident and incident_data and self.selected_incident["_id"] == incident_data["_id"]:
                self.open_drawer(self.selected_incident["_id"])

    def delete_incident(self, incident_id):
        reply = QMessageBox.question(self, "Confirm Delete", "Are you sure you want to delete this incident?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.incidents.delete_one({"_id": ObjectId(incident_id)})
            if self.selected_incident and str(self.selected_incident["_id"]) == incident_id:
                self.close_drawer()
            self.load_data()

    def export_csv(self):
        self._export_to_csv(list(self.db.incidents.find(self._build_query())))

    def _get_selected_ids(self):
        selected = []
        for r in range(self.table.rowCount()):
            if self.table.item(r, 1).checkState() == Qt.Checked:
                selected.append(ObjectId(self.table.item(r, 0).text()))
        return selected

    def _bulk_delete(self):
        ids = self._get_selected_ids()
        if not ids:
            QMessageBox.warning(self, "No Selection", "Please select at least one incident.")
            return
            
        reply = QMessageBox.question(self, "Confirm Delete", f"Are you sure you want to delete {len(ids)} selected incident(s)?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.incidents.delete_many({"_id": {"$in": ids}})
            if self.selected_incident and self.selected_incident["_id"] in ids:
                self.close_drawer()
            self.load_data()

    def _bulk_update_status(self, new_status):
        ids = self._get_selected_ids()
        if not ids:
            QMessageBox.warning(self, "No Selection", "Please select at least one incident.")
            return
            
        self.db.incidents.update_many({"_id": {"$in": ids}}, {"$set": {"status": new_status}})
        if self.selected_incident and self.selected_incident["_id"] in ids:
            self.selected_incident["status"] = new_status
            self.open_drawer(self.selected_incident["_id"])
        self.load_data()
        
    def _bulk_export_csv(self):
        ids = self._get_selected_ids()
        if not ids:
            QMessageBox.warning(self, "No Selection", "Please select at least one incident.")
            return
            
        cursor = self.db.incidents.find({"_id": {"$in": ids}})
        self._export_to_csv(list(cursor))

    def _export_to_csv(self, records):
        if not records:
            QMessageBox.warning(self, "No Data", "There are no incidents to export.")
            return
            
        path, _ = QFileDialog.getSaveFileName(self, "Export Incidents", "", "CSV Files (*.csv)")
        if not path: return
        
        with open(path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Title", "Type", "Severity", "Status", "Location", "Description", "Reported"])
            for inc in records:
                writer.writerow([
                    str(inc["_id"]),
                    inc.get("title", ""),
                    inc.get("type", ""),
                    inc.get("severity", ""),
                    inc.get("status", ""),
                    inc.get("location", {}).get("area", ""),
                    inc.get("description", ""),
                    inc.get("created_at", "")
                ])
        QMessageBox.information(self, "Export Successful", f"Exported to {path}")
