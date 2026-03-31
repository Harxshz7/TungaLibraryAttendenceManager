import sys
from PySide6.QtWidgets import QApplication
from views.main_window import MainWindow
from models.database import init_db

def run_app():
    init_db()
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
