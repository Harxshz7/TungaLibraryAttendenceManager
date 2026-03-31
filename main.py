import os
import sys
from PySide6.QtCore import QTimer
from PySide6.QtGui import QAction, QFontDatabase, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon
from utils.resource_utils import resource_path
from views.main_window import MainWindow


def load_fonts():
    QFontDatabase.addApplicationFont(
        resource_path("assets/fonts/Inter/Inter-Regular.ttf")
    )


def load_stylesheet(app, path):
    full_path = resource_path(path)
    with open(full_path, "r", encoding="utf-8") as f:
        app.setStyleSheet(f.read())

def build_tray_icon():
    icon = QIcon()
    ico_path = resource_path("assets/logo.ico")
    png_path = resource_path("assets/logo.png")

    if sys.platform.startswith("win"):
        if os.path.exists(ico_path):
            icon.addFile(ico_path)
        if os.path.exists(png_path):
            icon.addFile(png_path)
    else:
        if os.path.exists(png_path):
            icon.addFile(png_path)
        if os.path.exists(ico_path):
            icon.addFile(ico_path)

    return icon


app = QApplication(sys.argv)
load_fonts()
# LOAD THEME HERE
load_stylesheet(app, "themes/light.qss")
 # switch anytime

window = MainWindow()

tray_icon = build_tray_icon()
if not tray_icon.isNull():
    app.setWindowIcon(tray_icon)

tray = QSystemTrayIcon(app)
tray.setIcon(tray_icon)
tray.setToolTip("Library Attendance System")

menu = QMenu()

open_action = QAction("Open Dashboard")
exit_action = QAction("Exit (Admin)")

menu.addAction(open_action)
menu.addSeparator()
menu.addAction(exit_action)

tray.setContextMenu(menu)
app.setQuitOnLastWindowClosed(False)

def show_dashboard():
    window.show()
    window.raise_()
    window.activateWindow()
    window.showMaximized()  # or showFullScreen()
    window.raise_()

def exit_app():
    tray.hide()
    window.kiosk_mode = False
    window.close()
    app.quit()

open_action.triggered.connect(show_dashboard)
exit_action.triggered.connect(exit_app)

tray.activated.connect(
    lambda reason: show_dashboard()
    if reason == QSystemTrayIcon.Trigger else None
)

def init_tray():
    if QSystemTrayIcon.isSystemTrayAvailable() and not tray.icon().isNull():
        window.hide()
        tray.show()
    else:
        window.kiosk_mode = False
        window.showMaximized()

QTimer.singleShot(0, init_tray)

sys.exit(app.exec())
