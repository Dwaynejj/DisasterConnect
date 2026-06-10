"""Main dashboard window for DisasterConnect (Redesigned)."""
import os
from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QStackedWidget, QScrollArea, QSizePolicy, QGridLayout, 
    QLineEdit, QMenu, QAction
)
from PyQt5.QtCore import (
    Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QByteArray, QSize
)
from PyQt5.QtGui import QIcon, QFont, QColor, QPainter, QPixmap
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis

# Keep existing widgets
from src.dashboard.incident_widget import IncidentWidget
from src.dashboard.resource_widget import ResourceWidget
from src.dashboard.alert_widget import AlertWidget


FEATHER_ICONS = {
    'home': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>',
    'alert-triangle': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
    'package': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="16.5" y1="9.4" x2="7.5" y2="4.21"></line><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>',
    'message-square': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>',
    'check-square': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 11 12 14 22 4"></polyline><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path></svg>',
    'bar-chart-2': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>',
    'settings': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>',
    'log-out': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>',
    'chevron-left': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>',
    'chevron-right': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>',
    'bell': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>',
    'search': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>',
    'user': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>',
    'refresh-cw': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>'
}

def create_svg_icon(name, color="#8B9DC3"):
    """Helper to dynamically generate QIcons from SVG strings."""
    svg = FEATHER_ICONS.get(name, FEATHER_ICONS['alert-triangle'])
    svg = svg.replace('currentColor', color)
    renderer = QSvgRenderer(QByteArray(svg.encode('utf-8')))
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)

class NavButton(QPushButton):
    """Custom sidebar navigation button with active/inactive states."""
    def __init__(self, text, icon_name):
        super().__init__()
        self.btn_text = text
        self.icon_name = icon_name
        
        self.icon_inactive = create_svg_icon(icon_name, "#8B9DC3")
        self.icon_active = create_svg_icon(icon_name, "#FFFFFF")
        
        self.setIcon(self.icon_inactive)
        self.setText(f"  {text}")
        self.setIconSize(QSize(20, 20))
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(44)
        
        self.set_active(False)
        
    def set_active(self, active: bool):
        if active:
            self.setIcon(self.icon_active)
            self.setStyleSheet("""
                QPushButton {
                    background-color: #1F2937;
                    color: #FFFFFF;
                    border: none;
                    border-left: 3px solid #1F6FEB;
                    text-align: left;
                    padding-left: 12px;
                    font-size: 14px;
                    font-weight: bold;
                }
            """)
        else:
            self.setIcon(self.icon_inactive)
            self.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #8B9DC3;
                    border: none;
                    border-left: 3px solid transparent;
                    text-align: left;
                    padding-left: 12px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    color: #E5E7EB;
                    background-color: #1F2937;
                }
            """)

class DashboardWindow(QMainWindow):
    def __init__(self, auth_manager=None):
        super().__init__()
        self.auth_manager = auth_manager
        
        # 1. Maximised, Min 1100x700, dark theme base
        self.setWindowTitle("DisasterConnect")
        self.setMinimumSize(1100, 700)
        
        self.setStyleSheet("""
            QMainWindow { background-color: #F3F4F6; }
            /* Reset global QFrame styles inside the dashboard */
            QFrame, QLabel { border: none; margin: 0; }
        """)
        
        self.nav_buttons = []
        self._is_collapsed = False
        
        # Initialize UI components
        self._init_ui()
        
        # Simulated Alerts logic
        self.alerts = ["New incident in Accra", "Resource shortage: Medical kits", "Team Alpha dispatched"]
        self.badge_count = len(self.alerts)
        self.update_bell_badge()
        
    def _init_ui(self):
        # 2. Global layout: QHBoxLayout -> SIDEBAR + CONTENT AREA
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self._build_sidebar()
        
        # Right side content area
        self.content_container = QWidget()
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        
        self._build_topbar()
        
        # Content Stack
        self.content_stack = QStackedWidget()
        self.content_layout.addWidget(self.content_stack)
        
        self.main_layout.addWidget(self.content_container)
        
        # Instantiate pages
        self._init_pages()

    def _build_sidebar(self):
        # 3. SIDEBAR
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(220)
        self.sidebar.setStyleSheet("QFrame#Sidebar { background-color: #161B22; border-right: 1px solid #1F2937; }")
        
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(0, 16, 0, 16)
        self.sidebar_layout.setSpacing(4)
        
        # Header (Logo + Title + Toggle)
        self.sidebar_header = QWidget()
        header_layout = QHBoxLayout(self.sidebar_header)
        header_layout.setContentsMargins(12, 0, 8, 0)
        header_layout.setSpacing(8)
        
        logo = QLabel()
        logo.setPixmap(create_svg_icon('alert-triangle', '#1F6FEB').pixmap(24, 24))
        
        self.app_title = QLabel("DisasterConnect")
        self.app_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.app_title.setStyleSheet("color: white;")
        
        self.toggle_btn = QPushButton()
        self.toggle_btn.setIcon(create_svg_icon('chevron-left', '#8B9DC3'))
        self.toggle_btn.setFixedSize(28, 28)
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.setStyleSheet("border: none; background: transparent;")
        self.toggle_btn.clicked.connect(self._toggle_sidebar)
        
        header_layout.addWidget(logo)
        header_layout.addWidget(self.app_title)
        header_layout.addStretch()
        header_layout.addWidget(self.toggle_btn)
        
        self.sidebar_layout.addWidget(self.sidebar_header)
        self.sidebar_layout.addSpacing(24)
        
        # Navigation Items
        nav_items = [
            ("Dashboard", "home"),
            ("Incidents", "alert-triangle"),
            ("Resources", "package"),
            ("Messages", "message-square"),
            ("Tasks", "check-square"),
            ("Reports", "bar-chart-2"),
            ("Settings", "settings")
        ]
        
        for idx, (text, icon) in enumerate(nav_items):
            btn = NavButton(text, icon)
            btn.clicked.connect(lambda checked, i=idx: self._switch_page(i))
            self.sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)
            
        self.sidebar_layout.addStretch()
        
        # Bottom User Area
        self.user_area = QWidget()
        user_layout = QHBoxLayout(self.user_area)
        user_layout.setContentsMargins(16, 12, 16, 12)
        
        # Avatar circle
        self.avatar = QLabel("A")
        self.avatar.setFixedSize(32, 32)
        self.avatar.setAlignment(Qt.AlignCenter)
        self.avatar.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.avatar.setStyleSheet("background-color: #1F6FEB; color: white; border-radius: 16px;")
        
        # User details
        self.user_details = QWidget()
        details_layout = QVBoxLayout(self.user_details)
        details_layout.setContentsMargins(8, 0, 0, 0)
        details_layout.setSpacing(0)
        
        username = "Admin User"
        role = "System Admin"
        if self.auth_manager and hasattr(self.auth_manager, 'get_current_user'):
            u = self.auth_manager.get_current_user()
            if u:
                username = f"{u.get('username', 'Admin')}"
                role = u.get('role', 'User').capitalize()
                self.avatar.setText(username[0].upper() if username else "U")
            
        self.username_lbl = QLabel(username)
        self.username_lbl.setStyleSheet("color: white; font-weight: bold; font-size: 13px;")
        
        self.role_lbl = QLabel(role)
        self.role_lbl.setStyleSheet("color: #8B9DC3; font-size: 11px;")
        
        details_layout.addWidget(self.username_lbl)
        details_layout.addWidget(self.role_lbl)
        
        self.logout_btn = QPushButton()
        self.logout_btn.setIcon(create_svg_icon('log-out', '#8B9DC3'))
        self.logout_btn.setFixedSize(28, 28)
        self.logout_btn.setCursor(Qt.PointingHandCursor)
        self.logout_btn.setStyleSheet("border: none; background: transparent;")
        
        # Connect logout
        self.logout_btn.clicked.connect(self._handle_logout)
        
        user_layout.addWidget(self.avatar)
        user_layout.addWidget(self.user_details)
        user_layout.addWidget(self.logout_btn)
        
        self.sidebar_layout.addWidget(self.user_area)
        self.main_layout.addWidget(self.sidebar)

    def _build_topbar(self):
        # 4. TOPBAR
        self.topbar = QFrame()
        self.topbar.setFixedHeight(52)
        self.topbar.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-bottom: 1px solid #E5E7EB;
            }
        """)
        
        top_layout = QHBoxLayout(self.topbar)
        top_layout.setContentsMargins(24, 0, 24, 0)
        
        self.page_title = QLabel("Dashboard")
        self.page_title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.page_title.setStyleSheet("color: #111827; border: none;")
        
        # Right side tools
        tools_widget = QWidget()
        tools_widget.setStyleSheet("border: none;")
        tools_layout = QHBoxLayout(tools_widget)
        tools_layout.setContentsMargins(0, 0, 0, 0)
        tools_layout.setSpacing(16)
        
        # Refresh Button
        self.refresh_btn = QPushButton()
        self.refresh_btn.setIcon(create_svg_icon('refresh-cw', '#4B5563'))
        self.refresh_btn.setFixedSize(36, 36)
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.setStyleSheet("QPushButton { border: none; border-radius: 18px; background: transparent; } QPushButton:hover { background-color: #F3F4F6; }")
        self.refresh_btn.clicked.connect(self._on_refresh_clicked)
        
        # Search
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.setFixedWidth(200)
        self.search_bar.setFixedHeight(32)
        self.search_bar.setStyleSheet("""
            QLineEdit {
                background-color: #F3F4F6;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
                padding: 0 16px;
                color: #374151;
            }
            QLineEdit:focus {
                border: 1px solid #1F6FEB;
                background-color: #FFFFFF;
            }
        """)
        
        # Notification Bell
        self.bell_btn = QPushButton()
        self.bell_btn.setIcon(create_svg_icon('bell', '#4B5563'))
        self.bell_btn.setFixedSize(36, 36)
        self.bell_btn.setCursor(Qt.PointingHandCursor)
        self.bell_btn.setStyleSheet("QPushButton { border: none; border-radius: 18px; background: transparent; } QPushButton:hover { background-color: #F3F4F6; }")
        self.bell_btn.clicked.connect(self._show_notifications)
        
        # Badge
        self.badge = QLabel(self.bell_btn)
        self.badge.setFixedSize(16, 16)
        self.badge.move(18, 4)
        self.badge.setAlignment(Qt.AlignCenter)
        self.badge.setStyleSheet("""
            QLabel {
                background-color: #EF4444;
                color: white;
                border-radius: 8px;
                font-size: 9px;
                font-weight: bold;
            }
        """)
        self.badge.hide()
        
        # Topbar avatar
        self.top_avatar = QLabel("A")
        self.top_avatar.setFixedSize(32, 32)
        self.top_avatar.setAlignment(Qt.AlignCenter)
        self.top_avatar.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.top_avatar.setStyleSheet("background-color: #1F6FEB; color: white; border-radius: 16px;")
        if self.auth_manager and getattr(self.auth_manager, 'current_user', None):
            u = self.auth_manager.current_user.get('username', 'Admin')
            self.top_avatar.setText(u[0].upper() if u else "U")
            
        tools_layout.addWidget(self.refresh_btn)
        tools_layout.addWidget(self.search_bar)
        tools_layout.addWidget(self.bell_btn)
        tools_layout.addWidget(self.top_avatar)
        
        top_layout.addWidget(self.page_title)
        top_layout.addStretch()
        top_layout.addWidget(tools_widget)
        
        self.content_layout.addWidget(self.topbar)

    def _init_pages(self):
        from src.dashboard.overview_page import OverviewPage
        from src.dashboard.messages_widget import MessagesWidget
        from src.dashboard.tasks_widget import TasksWidget
        from src.dashboard.reports_widget import ReportsWidget
        from src.dashboard.settings_widget import SettingsWidget
        self.overview_page = OverviewPage(self)
        
        # Create pages
        self.pages = [
            self.overview_page,
            IncidentWidget(self.auth_manager),
            ResourceWidget(self.auth_manager),
            MessagesWidget(self.auth_manager),
            TasksWidget(self.auth_manager),
            ReportsWidget(self.auth_manager),
            SettingsWidget(self.auth_manager)
        ]
        
        for p in self.pages:
            self.content_stack.addWidget(p)
            
        # Select first page
        self._switch_page(0)
        
    def _create_placeholder_page(self, title):
        page = QWidget()
        page.setStyleSheet("background-color: #F3F4F6;")
        layout = QVBoxLayout(page)
        lbl = QLabel(f"<b>{title}</b><br>Content coming soon...")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("color: #6B7280; font-size: 16px;")
        layout.addWidget(lbl)
        return page

    def _on_refresh_clicked(self):
        if hasattr(self, 'overview_page'):
            self.overview_page.reload_data()
            
    def _switch_page(self, index):
        self.content_stack.setCurrentIndex(index)
        self.page_title.setText(self.nav_buttons[index].btn_text.strip())
        
        for i, btn in enumerate(self.nav_buttons):
            btn.set_active(i == index)

    def _toggle_sidebar(self):
        start_width = self.sidebar.width()
        end_width = 52 if not self._is_collapsed else 220
        
        self.anim = QPropertyAnimation(self.sidebar, b"minimumWidth")
        self.anim.setDuration(200)
        self.anim.setStartValue(start_width)
        self.anim.setEndValue(end_width)
        self.anim.setEasingCurve(QEasingCurve.InOutQuad)
        
        # Also animate maximum width so it stays fixed
        self.anim2 = QPropertyAnimation(self.sidebar, b"maximumWidth")
        self.anim2.setDuration(200)
        self.anim2.setStartValue(start_width)
        self.anim2.setEndValue(end_width)
        self.anim2.setEasingCurve(QEasingCurve.InOutQuad)
        
        # Handle label visibility
        if not self._is_collapsed:
            self.app_title.hide()
            self.user_details.hide()
            for btn in self.nav_buttons:
                btn.setText("")
            self.toggle_btn.setIcon(create_svg_icon('chevron-right', '#8B9DC3'))
        else:
            self.app_title.show()
            self.user_details.show()
            for btn in self.nav_buttons:
                btn.setText(f"  {btn.btn_text}")
            self.toggle_btn.setIcon(create_svg_icon('chevron-left', '#8B9DC3'))
            
        self.anim.start()
        self.anim2.start()
        self._is_collapsed = not self._is_collapsed

    def _show_notifications(self):
        # 5. QMenu-style dropdown
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 4px 0px;
            }
            QMenu::item {
                padding: 8px 24px;
                color: #374151;
            }
            QMenu::item:selected {
                background-color: #F3F4F6;
            }
        """)
        
        if not self.alerts:
            act = QAction("No new notifications", self)
            act.setEnabled(False)
            menu.addAction(act)
        else:
            for alert in reversed(self.alerts[-5:]):
                act = QAction(alert, self)
                menu.addAction(act)
                
            menu.addSeparator()
            clear_act = QAction("Clear All", self)
            clear_act.triggered.connect(self._clear_alerts)
            menu.addAction(clear_act)
            
        # Show below the bell button
        pos = self.bell_btn.mapToGlobal(self.bell_btn.rect().bottomRight())
        # Offset to align right
        pos.setX(pos.x() - menu.sizeHint().width())
        menu.exec_(pos)
        
    def update_bell_badge(self):
        if self.badge_count > 0:
            self.badge.setText(str(self.badge_count))
            self.badge.show()
        else:
            self.badge.hide()

    def _clear_alerts(self):
        self.alerts.clear()
        self.badge_count = 0
        self.update_bell_badge()

    def update_user_info(self):
        """Update the sidebar and topbar with the authenticated user's details."""
        if self.auth_manager and hasattr(self.auth_manager, 'get_current_user'):
            user = self.auth_manager.get_current_user()
            if user:
                username = user.get('username', 'Admin')
                role = user.get('role', 'user').capitalize()
                initials = user.get('avatar_initials', username[0].upper() if username else 'U')
                
                self.username_lbl.setText(username)
                self.role_lbl.setText(role)
                self.avatar.setText(initials)
                self.top_avatar.setText(initials)

    def _handle_logout(self):
        if self.auth_manager and hasattr(self.auth_manager, 'logout'):
            self.auth_manager.logout()
        
        # We need to signal the parent main window to switch back to login.
        # As a simple approach without circular imports, we can close the parent window if it's the main app,
        # or we can emit a signal. For now, since DashboardWindow is inside a QStackedWidget,
        # we can traverse up.
        parent = self.parentWidget()
        while parent and not hasattr(parent, 'stacked_widget'):
            parent = parent.parentWidget()
        if parent:
            parent.stacked_widget.setCurrentWidget(parent.login_window)
            parent.login_window._password_input.clear()
