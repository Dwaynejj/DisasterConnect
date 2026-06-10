import os
import folium
from datetime import datetime, timedelta
from src.utils.map_generator import generate_dashboard_map
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSplitter,
    QListWidget, QListWidgetItem, QPushButton, QCheckBox, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QUrl, QSize
from PyQt5.QtGui import QFont, QColor, QPainter, QIcon
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtChart import (
    QChart, QChartView, QPieSeries, QPieSlice,
    QHorizontalBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
)

from db.connection import db_connection

def time_ago(dt):
    if not dt:
        return "Unknown"
    diff = datetime.now() - dt
    if diff.days > 0:
        return f"{diff.days}d ago"
    hours = diff.seconds // 3600
    if hours > 0:
        return f"{hours}h ago"
    minutes = (diff.seconds % 3600) // 60
    return f"{minutes}m ago"

def get_severity_color(severity):
    colors = {
        'Critical': '#E74C3C',
        'High': '#F39C12',
        'Medium': '#3498DB',
        'Low': '#27AE60'
    }
    return colors.get(severity, '#95A5A6')

class KPICard(QFrame):
    def __init__(self, title, value, icon_name, accent_color, trend_val="+0%"):
        super().__init__()
        self.setFixedHeight(120)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 8px;
                border-left: 4px solid {accent_color};
                margin: 0px;
            }}
        """)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        
        top_layout = QHBoxLayout()
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: #6C757D; font-size: 11pt; font-weight: bold; border: none;")
        top_layout.addWidget(title_lbl)
        top_layout.addStretch()
        layout.addLayout(top_layout)
        
        val_lbl = QLabel(str(value))
        val_lbl.setStyleSheet(f"color: {accent_color}; font-size: 32pt; font-weight: bold; border: none;")
        layout.addWidget(val_lbl)
        
        trend_lbl = QLabel(f"⬈ {trend_val} vs yesterday")
        trend_lbl.setStyleSheet("color: #27AE60; font-size: 9pt; border: none;")
        layout.addWidget(trend_lbl)

class ActivityItemWidget(QWidget):
    def __init__(self, title, location, severity, dt):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {get_severity_color(severity)}; font-size: 14pt; border: none;")
        dot.setFixedWidth(24)
        dot.setAlignment(Qt.AlignCenter)
        layout.addWidget(dot)
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setAlignment(Qt.AlignVCenter)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-weight: bold; color: #111827; border: none; font-size: 10pt;")
        loc_lbl = QLabel(location)
        loc_lbl.setStyleSheet("color: #6B7280; font-size: 9pt; border: none;")
        text_layout.addWidget(title_lbl)
        text_layout.addWidget(loc_lbl)
        layout.addLayout(text_layout)
        
        layout.addStretch()
        
        time_lbl = QLabel(time_ago(dt))
        time_lbl.setStyleSheet("color: #9CA3AF; font-size: 9pt; border: none;")
        time_lbl.setFixedWidth(60)
        time_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(time_lbl)
        
        view_btn = QPushButton("View All")
        view_btn.setCursor(Qt.PointingHandCursor)
        view_btn.setStyleSheet("color: #1F6FEB; background: transparent; border: none; font-weight: bold;")
        view_btn.setFixedWidth(60)
        layout.addWidget(view_btn)

class OverviewPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = db_connection.db
        
        # UI State
        self.show_incidents = True
        self.show_resources = True
        
        self.setStyleSheet("QWidget { background-color: #F3F4F6; } QFrame { border: none; }")
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(24, 24, 24, 24)
        self.main_layout.setSpacing(20)
        
        self._init_ui()
        self.reload_data()
        
    def _init_ui(self):
        # ROW 1: KPI Cards
        self.row1 = QHBoxLayout()
        self.main_layout.addLayout(self.row1)
        
        # ROW 2: Splitter
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Left Side (Map)
        self.map_container = QFrame()
        self.map_container.setStyleSheet("background-color: white; border-radius: 8px;")
        map_layout = QVBoxLayout(self.map_container)
        map_layout.setContentsMargins(12, 12, 12, 12)
        
        # Map toggles
        toggles_layout = QHBoxLayout()
        self.chk_incidents = QCheckBox("Incidents")
        self.chk_incidents.setChecked(True)
        self.chk_incidents.toggled.connect(self._on_layer_toggled)
        self.chk_resources = QCheckBox("Resources")
        self.chk_resources.setChecked(True)
        self.chk_resources.toggled.connect(self._on_layer_toggled)
        toggles_layout.addWidget(self.chk_incidents)
        toggles_layout.addWidget(self.chk_resources)
        toggles_layout.addStretch()
        map_layout.addLayout(toggles_layout)
        
        self.web_view = QWebEngineView()
        map_layout.addWidget(self.web_view)
        
        # Right Side (Charts)
        self.charts_container = QFrame()
        self.charts_layout = QVBoxLayout(self.charts_container)
        self.charts_layout.setContentsMargins(0, 0, 0, 0)
        self.charts_layout.setSpacing(16)
        
        self.donut_chart_view = QChartView()
        self.donut_chart_view.setRenderHint(QPainter.Antialiasing)
        self.donut_chart_view.setStyleSheet("background: white; border-radius: 8px;")
        
        self.bar_chart_view = QChartView()
        self.bar_chart_view.setRenderHint(QPainter.Antialiasing)
        self.bar_chart_view.setStyleSheet("background: white; border-radius: 8px;")
        
        self.charts_layout.addWidget(self.donut_chart_view)
        self.charts_layout.addWidget(self.bar_chart_view)
        
        self.splitter.addWidget(self.map_container)
        self.splitter.addWidget(self.charts_container)
        self.splitter.setSizes([600, 400]) # 60/40 split approximation
        
        self.main_layout.addWidget(self.splitter, stretch=1)
        
        # ROW 3: Recent Activity
        activity_lbl = QLabel("Recent Activity")
        activity_lbl.setStyleSheet("font-size: 14pt; font-weight: bold; color: #111827; border: none;")
        self.main_layout.addWidget(activity_lbl)
        
        self.activity_list = QListWidget()
        self.activity_list.setFixedHeight(180)
        self.activity_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border-radius: 8px;
                border: none;
            }
            QListWidget::item {
                border-bottom: 1px solid #F3F4F6;
            }
        """)
        self.main_layout.addWidget(self.activity_list)
        
    def _on_layer_toggled(self):
        self.show_incidents = self.chk_incidents.isChecked()
        self.show_resources = self.chk_resources.isChecked()
        self._update_map()

    def reload_data(self):
        # Fetch data
        self.incidents = list(self.db.incidents.find().sort("created_at", -1))
        self.resources = list(self.db.resources.find())
        
        self._update_kpis()
        self._update_map()
        self._update_charts()
        self._update_activity()
        
    def _update_kpis(self):
        # Clear existing
        while self.row1.count():
            item = self.row1.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        total_incidents = len(self.incidents)
        active_incidents = sum(1 for i in self.incidents if i.get("status") in ["Active", "In Progress", "Under Review"])
        total_resources = len(self.resources)
        available_resources = sum(1 for r in self.resources if r.get("status") == "Available")
        
        c1 = KPICard("Total Incidents", total_incidents, "alert-circle", "#E74C3C")
        c2 = KPICard("Active Incidents", active_incidents, "zap", "#F39C12")
        c3 = KPICard("Total Resources", total_resources, "package", "#1F6FEB")
        c4 = KPICard("Available Resources", available_resources, "check-circle", "#27AE60")
        
        self.row1.addWidget(c1)
        self.row1.addWidget(c2)
        self.row1.addWidget(c3)
        self.row1.addWidget(c4)

    def _update_map(self):
        html = generate_dashboard_map(
            incidents=self.incidents,
            resources=self.resources,
            show_heatmap=True,
            show_resources=self.show_resources,
            show_incidents=self.show_incidents
        )
        self.web_view.setHtml(html, QUrl("about:blank"))

    def _update_charts(self):
        # Donut Chart
        donut = QChart()
        donut.setTitle("Incidents by Severity")
        donut.setAnimationOptions(QChart.SeriesAnimations)
        
        pie_series = QPieSeries()
        pie_series.setHoleSize(0.4)
        
        sev_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        for inc in self.incidents:
            s = inc.get("severity")
            if s in sev_counts:
                sev_counts[s] += 1
                
        for sev, count in sev_counts.items():
            if count > 0:
                slice_ = pie_series.append(f"{sev} ({count})", count)
                slice_.setColor(QColor(get_severity_color(sev)))
                
        donut.addSeries(pie_series)
        donut.legend().setAlignment(Qt.AlignBottom)
        self.donut_chart_view.setChart(donut)
        
        # Bar Chart
        bar = QChart()
        bar.setTitle("Incidents by Type (Top 6)")
        bar.setAnimationOptions(QChart.SeriesAnimations)
        
        type_counts = {}
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        for inc in self.incidents:
            dt = inc.get("created_at")
            if dt and dt > thirty_days_ago:
                t = inc.get("type", "Unknown")
                type_counts[t] = type_counts.get(t, 0) + 1
                
        top_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:6]
        
        bar_series = QHorizontalBarSeries()
        set0 = QBarSet("Incidents")
        set0.setColor(QColor("#1F6FEB"))
        
        categories = []
        for t, count in reversed(top_types):  # Reverse so largest is at top
            set0.append(count)
            categories.append(t)
            
        bar_series.append(set0)
        bar.addSeries(bar_series)
        
        axis_y = QBarCategoryAxis()
        axis_y.append(categories)
        bar.addAxis(axis_y, Qt.AlignLeft)
        bar_series.attachAxis(axis_y)
        
        axis_x = QValueAxis()
        axis_x.applyNiceNumbers()
        bar.addAxis(axis_x, Qt.AlignBottom)
        bar_series.attachAxis(axis_x)
        
        bar.legend().hide()
        self.bar_chart_view.setChart(bar)

    def _update_activity(self):
        self.activity_list.clear()
        
        for inc in self.incidents[:5]:
            item = QListWidgetItem(self.activity_list)
            
            loc = inc.get("location", {}).get("area", "Unknown location")
            widget = ActivityItemWidget(
                title=inc.get("title", "Unknown Incident"),
                location=loc,
                severity=inc.get("severity", "Medium"),
                dt=inc.get("created_at")
            )
            
            item.setSizeHint(widget.sizeHint())
            self.activity_list.setItemWidget(item, widget)
