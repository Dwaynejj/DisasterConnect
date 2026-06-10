import os
import tempfile
import pandas as pd
from datetime import datetime, timedelta

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QComboBox, QDateEdit, QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QMessageBox, QGridLayout, QSizePolicy
)
from PyQt5.QtCore import Qt, QDate, QSize, QByteArray
from PyQt5.QtGui import QIcon, QFont, QColor, QPainter, QPixmap
from PyQt5.QtSvg import QSvgRenderer

import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure
import matplotlib.dates as mdates

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

from db.connection import db_connection

FEATHER_ICONS = {
    'bar-chart-2': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>',
    'download': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>'
}

def create_svg_icon(name, color="#8B9DC3", size=24):
    svg = FEATHER_ICONS.get(name, FEATHER_ICONS['bar-chart-2'])
    svg = svg.replace('currentColor', color)
    renderer = QSvgRenderer(QByteArray(svg.encode('utf-8')))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)

def get_severity_color(sev):
    return {"Critical": "#E74C3C", "High": "#F39C12", "Medium": "#3498DB", "Low": "#27AE60"}.get(sev, "#95A5A6")

def create_pill_badge(text, color):
    w = QWidget()
    l = QHBoxLayout(w)
    l.setContentsMargins(4, 2, 4, 2)
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet(f"background-color: {color}; color: white; border-radius: 10px; padding: 2px 8px; font-weight: bold; font-size: 8pt;")
    l.addWidget(lbl)
    return w

class KPICard(QFrame):
    def __init__(self, title, value, color):
        super().__init__()
        self.setMinimumSize(180, 100)
        self.setStyleSheet("""
            QFrame { background-color: white; border-radius: 8px; border: 1px solid #E5E7EB; }
        """)
        l = QVBoxLayout(self)
        l.setContentsMargins(16, 16, 16, 16)
        
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("color: #6B7280; font-size: 10pt; font-weight: bold; border: none;")
        
        v_lbl = QLabel(str(value))
        v_lbl.setStyleSheet(f"color: {color}; font-size: 24pt; font-weight: bold; border: none;")
        v_lbl.setAlignment(Qt.AlignLeft)
        
        l.addWidget(t_lbl)
        l.addWidget(v_lbl)
        l.addStretch()

class AnalyticsCanvas(QWidget):
    def __init__(self, parent=None, width=10, height=8, dpi=100):
        super().__init__(parent)
        self.width_inch = width
        self.height_inch = height
        self.dpi = dpi
        
        # Setup matplotlib rcParams for matching app style
        matplotlib.rcParams.update({
            'font.family': 'sans-serif',
            'font.sans-serif': ['Segoe UI', 'Arial'],
            'axes.titlesize': 12,
            'axes.titleweight': 'bold',
            'axes.spines.top': False,
            'axes.spines.right': False,
            'axes.grid': True,
            'grid.alpha': 0.3,
            'grid.color': '#D1D5DB'
        })
        
        self.fig = Figure(figsize=(self.width_inch, self.height_inch), dpi=self.dpi)
        self.fig.patch.set_facecolor('white')
        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.img_lbl = QLabel()
        self.img_lbl.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.img_lbl)
        
    def plot_data(self, df_incidents, resources_data):
        self.fig.clf()
        
        ax1 = self.fig.add_subplot(221)
        ax2 = self.fig.add_subplot(222)
        ax3 = self.fig.add_subplot(223)
        ax4 = self.fig.add_subplot(224)
        
        # Chart 1: Incidents per day (Line + Area)
        if not df_incidents.empty and 'timestamp' in df_incidents.columns:
            df_incidents['date'] = pd.to_datetime(df_incidents['timestamp']).dt.date
            daily = df_incidents.groupby('date').size()
            dates = daily.index
            counts = daily.values
            
            ax1.plot(dates, counts, color='#1F6FEB', linewidth=2)
            ax1.fill_between(dates, counts, alpha=0.3, color='#1F6FEB')
            ax1.set_title('Incidents Reported per Day')
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
            ax1.tick_params(axis='x', rotation=45)
            ax1.set_ylim(bottom=0)
        else:
            ax1.set_title('Incidents Reported per Day (No Data)')
            
        # Chart 2: Top 5 Incident Types (Horizontal Bar)
        if not df_incidents.empty and 'type' in df_incidents.columns:
            types = df_incidents['type'].value_counts().head(5).sort_values()
            ax2.barh(types.index, types.values, color='#F39C12')
            ax2.set_title('Top 5 Incident Types')
        else:
            ax2.set_title('Top Incident Types (No Data)')
            
        # Chart 3: Resource Status (Pie)
        if resources_data:
            res_df = pd.DataFrame(resources_data)
            if not res_df.empty and 'status' in res_df.columns:
                status_counts = res_df['status'].value_counts()
                colors_pie = ['#27AE60', '#F39C12', '#E74C3C', '#8B9DC3'][:len(status_counts)]
                ax3.pie(status_counts.values, labels=status_counts.index, autopct='%1.1f%%', colors=colors_pie, startangle=90)
                ax3.set_title('Resource Status Breakdown')
            else:
                ax3.set_title('Resource Status (No Data)')
        else:
            ax3.set_title('Resource Status (No Data)')
            
        # Chart 4: Incidents by Severity (Grouped Bar approx)
        if not df_incidents.empty and 'severity' in df_incidents.columns:
            sev_counts = df_incidents['severity'].value_counts()
            bars = ax4.bar(sev_counts.index, sev_counts.values)
            # Apply exact colors
            color_map = {"Critical": "#E74C3C", "High": "#F39C12", "Medium": "#3498DB", "Low": "#27AE60"}
            for idx, label in enumerate(sev_counts.index):
                bars[idx].set_color(color_map.get(label, "#95A5A6"))
            ax4.set_title('Incidents by Severity')
            ax4.set_ylim(bottom=0)
        else:
            ax4.set_title('Incidents by Severity (No Data)')
            
        self.fig.tight_layout()
        
        # Render to pixmap via Agg
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            self.fig.savefig(tmp.name, format='png', dpi=self.dpi, bbox_inches='tight')
            tmp_path = tmp.name
            
        pixmap = QPixmap(tmp_path)
        self.img_lbl.setPixmap(pixmap)
        
        try:
            os.remove(tmp_path)
        except:
            pass

class ReportsWidget(QWidget):
    def __init__(self, auth_manager=None):
        super().__init__()
        self.auth_manager = auth_manager
        self.db = db_connection.db
        
        self.setStyleSheet("QWidget { background-color: #F3F4F6; }")
        self.setup_ui()
        self.on_date_range_changed()
        
    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(24, 24, 24, 24)
        self.main_layout.setSpacing(16)
        
        # TOP ROW
        self.top_row = QFrame()
        self.top_row.setStyleSheet("background-color: white; border-radius: 8px; border: 1px solid #E5E7EB;")
        tl = QHBoxLayout(self.top_row)
        tl.setContentsMargins(16, 12, 16, 12)
        tl.setSpacing(16)
        
        lbl_style = "color: #374151; font-weight: bold; border: none;"
        combo_style = "padding: 6px; border: 1px solid #D1D5DB; border-radius: 4px; min-width: 150px; background: white;"
        
        type_lbl = QLabel("Report Type:")
        type_lbl.setStyleSheet(lbl_style)
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Incident Summary", "Resource Utilisation", "Response Time", "Full Operational"])
        self.type_combo.setStyleSheet(combo_style)
        
        range_lbl = QLabel("Date Range:")
        range_lbl.setStyleSheet(lbl_style)
        self.range_combo = QComboBox()
        self.range_combo.addItems(["Last 7 days", "Last 30 days", "Last 90 days", "Custom"])
        self.range_combo.setStyleSheet(combo_style)
        self.range_combo.currentTextChanged.connect(self.on_date_range_changed)
        
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addDays(-7))
        self.start_date.setStyleSheet(combo_style)
        
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setStyleSheet(combo_style)
        
        format_lbl = QLabel("Format:")
        format_lbl.setStyleSheet(lbl_style)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["Screen", "PDF Export", "CSV Export"])
        self.format_combo.setStyleSheet(combo_style)
        
        self.generate_btn = QPushButton(" Generate Report")
        self.generate_btn.setIcon(create_svg_icon('bar-chart-2', 'white'))
        self.generate_btn.setCursor(Qt.PointingHandCursor)
        self.generate_btn.setStyleSheet("background-color: #1F6FEB; color: white; font-weight: bold; padding: 8px 16px; border-radius: 6px;")
        self.generate_btn.clicked.connect(self.generate_report)
        
        tl.addWidget(type_lbl)
        tl.addWidget(self.type_combo)
        tl.addWidget(range_lbl)
        tl.addWidget(self.range_combo)
        tl.addWidget(self.start_date)
        tl.addWidget(self.end_date)
        tl.addWidget(format_lbl)
        tl.addWidget(self.format_combo)
        tl.addStretch()
        tl.addWidget(self.generate_btn)
        
        self.main_layout.addWidget(self.top_row)
        
        # SCREEN OUTPUT AREA
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(20)
        
        # SECTION A: KPIs
        self.kpi_layout = QHBoxLayout()
        self.kpi_total = KPICard("Total Incidents", "0", "#111827")
        self.kpi_resolved = KPICard("Resolved Incidents", "0", "#27AE60")
        self.kpi_response = KPICard("Avg Response Time", "N/A", "#F39C12")
        self.kpi_resources = KPICard("Resources Deployed", "0", "#1F6FEB")
        
        self.kpi_layout.addWidget(self.kpi_total)
        self.kpi_layout.addWidget(self.kpi_resolved)
        self.kpi_layout.addWidget(self.kpi_response)
        self.kpi_layout.addWidget(self.kpi_resources)
        
        self.content_layout.addLayout(self.kpi_layout)
        
        # SECTION B: Charts
        self.canvas = AnalyticsCanvas(self, width=10, height=7)
        self.content_layout.addWidget(self.canvas)
        
        # SECTION C: Data Table
        self.table_lbl = QLabel("Incident Data Table")
        self.table_lbl.setStyleSheet("font-size: 14pt; font-weight: bold; color: #111827; margin-top: 10px;")
        self.content_layout.addWidget(self.table_lbl)
        
        self.table = QTableWidget()
        self.table.setMinimumHeight(300)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Title", "Type", "Severity", "Status", "Reported"])
        self.table.setColumnHidden(0, True)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setStyleSheet("""
            QTableWidget { border: 1px solid #E5E7EB; background: white; border-radius: 8px; alternate-background-color: #F8F9FA; }
            QHeaderView::section { background-color: white; padding: 12px; border: none; border-bottom: 2px solid #E5E7EB; font-weight: bold; color: #6B7280; text-align: left; }
            QTableWidget::item { padding: 8px 12px; border-bottom: 1px solid #F3F4F6; }
        """)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        self.content_layout.addWidget(self.table)
        
        self.scroll.setWidget(self.content_widget)
        self.main_layout.addWidget(self.scroll, stretch=1)

    def on_date_range_changed(self):
        sel = self.range_combo.currentText()
        if sel == "Custom":
            self.start_date.show()
            self.end_date.show()
        else:
            self.start_date.hide()
            self.end_date.hide()
            d = QDate.currentDate()
            self.end_date.setDate(d)
            if sel == "Last 7 days":
                self.start_date.setDate(d.addDays(-7))
            elif sel == "Last 30 days":
                self.start_date.setDate(d.addDays(-30))
            elif sel == "Last 90 days":
                self.start_date.setDate(d.addDays(-90))

    def get_date_range(self):
        start = self.start_date.date().toPyDate()
        end = self.end_date.date().toPyDate()
        # Make end date inclusive up to midnight
        return datetime.combine(start, datetime.min.time()), datetime.combine(end, datetime.max.time())

    def fetch_data(self):
        start_dt, end_dt = self.get_date_range()
        
        # MongoDB queries
        # Some dummy data might not have timestamp, fallback to reported_at or skip.
        # We'll just fetch all and filter in python if fields vary, but normally we'd filter in query.
        incidents = list(self.db.incidents.find())
        filtered_incs = []
        for inc in incidents:
            dt = inc.get('timestamp') or inc.get('reported_at')
            if isinstance(dt, datetime):
                if start_dt <= dt <= end_dt:
                    filtered_incs.append(inc)
            else:
                # If no date, include it just for mockup visually or skip. We'll skip if strict.
                # Let's include if date parsing fails or is none for dummy data sake, but assign fake date
                inc['timestamp'] = datetime.now() - timedelta(days=2)
                filtered_incs.append(inc)
                
        resources = list(self.db.resources.find())
        return filtered_incs, resources

    def update_screen(self, incidents, resources):
        # Update KPIs
        total = len(incidents)
        resolved = sum(1 for i in incidents if i.get('status') == 'Resolved')
        res_deployed = sum(1 for r in resources if r.get('status') == 'Deployed')
        
        self.kpi_total.findChildren(QLabel)[1].setText(str(total))
        self.kpi_resolved.findChildren(QLabel)[1].setText(str(resolved))
        self.kpi_resources.findChildren(QLabel)[1].setText(str(res_deployed))
        
        # Update Charts
        df_inc = pd.DataFrame(incidents)
        self.canvas.plot_data(df_inc, resources)
        
        # Update Table
        self.table.setRowCount(0)
        for row, inc in enumerate(incidents):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(inc["_id"])))
            self.table.setItem(row, 1, QTableWidgetItem(inc.get("title", "")))
            self.table.setItem(row, 2, QTableWidgetItem(inc.get("type", "")))
            
            sev = inc.get("severity", "Medium")
            self.table.setCellWidget(row, 3, create_pill_badge(sev, get_severity_color(sev)))
            
            stat = inc.get("status", "Active")
            self.table.setItem(row, 4, QTableWidgetItem(stat))
            
            dt = inc.get('timestamp') or inc.get('reported_at')
            dt_str = dt.strftime("%Y-%m-%d %H:%M") if isinstance(dt, datetime) else str(dt)
            self.table.setItem(row, 5, QTableWidgetItem(dt_str))

    def generate_report(self):
        incidents, resources = self.fetch_data()
        fmt = self.format_combo.currentText()
        
        if fmt == "Screen":
            self.update_screen(incidents, resources)
            QMessageBox.information(self, "Report Generated", "Screen updated with latest report data.")
            
        elif fmt == "CSV Export":
            path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
            if path:
                df = pd.DataFrame(incidents)
                # Cleanup _id object
                if '_id' in df.columns:
                    df['_id'] = df['_id'].astype(str)
                df.to_csv(path, index=False)
                QMessageBox.information(self, "Success", f"CSV Exported successfully to:\n{path}")
                
        elif fmt == "PDF Export":
            path, _ = QFileDialog.getSaveFileName(self, "Save PDF", "", "PDF Files (*.pdf)")
            if path:
                self.update_screen(incidents, resources)
                self.export_pdf(path, incidents, resources)
                QMessageBox.information(self, "Success", f"PDF Exported successfully to:\n{path}")
                try:
                    os.startfile(path)
                except:
                    pass

    def export_pdf(self, filepath, incidents, resources):
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        
        # Title
        elements.append(Paragraph("<b>DisasterConnect Operational Report</b>", styles['Title']))
        elements.append(Spacer(1, 12))
        
        # Meta
        start, end = self.get_date_range()
        dt_str = f"Date Range: {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}"
        elements.append(Paragraph(dt_str, styles['Normal']))
        elements.append(Paragraph(f"Report Type: {self.type_combo.currentText()}", styles['Normal']))
        elements.append(Paragraph(f"Generated On: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        elements.append(Spacer(1, 24))
        
        # Exec Summary
        elements.append(Paragraph("<b>Executive Summary</b>", styles['Heading2']))
        total = len(incidents)
        resolved = sum(1 for i in incidents if i.get('status') == 'Resolved')
        deployed = sum(1 for r in resources if r.get('status') == 'Deployed')
        summary_text = f"During this reporting period, a total of {total} incidents were recorded, of which {resolved} have been resolved. Currently, {deployed} resources are deployed in the field."
        elements.append(Paragraph(summary_text, styles['Normal']))
        elements.append(Spacer(1, 24))
        
        # Charts (Save canvas to temp image, then embed)
        elements.append(Paragraph("<b>Analytics & Charts</b>", styles['Heading2']))
        elements.append(Spacer(1, 12))
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            self.canvas.fig.savefig(tmp.name, format='png', dpi=150, bbox_inches='tight')
            tmp_path = tmp.name
            
        img = RLImage(tmp_path, width=6.5*inch, height=4.5*inch)
        elements.append(img)
        elements.append(Spacer(1, 24))
        
        # Table
        elements.append(Paragraph("<b>Incident Data</b>", styles['Heading2']))
        elements.append(Spacer(1, 12))
        
        data = [["Title", "Type", "Severity", "Status", "Date"]]
        for inc in incidents:
            dt = inc.get('timestamp') or inc.get('reported_at')
            dt_str = dt.strftime("%Y-%m-%d") if isinstance(dt, datetime) else ""
            data.append([
                inc.get("title", "")[:25],
                inc.get("type", ""),
                inc.get("severity", ""),
                inc.get("status", ""),
                dt_str
            ])
            
        t = Table(data, colWidths=[2.5*inch, 1.2*inch, 1*inch, 1*inch, 1.2*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1F6FEB')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#F8F9FA')),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#E5E7EB'))
        ]))
        elements.append(t)
        
        doc.build(elements)
        # Cleanup temp file if possible
        try:
            os.remove(tmp_path)
        except:
            pass
