from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QFrame
)
from PySide6.QtWidgets import QGroupBox, QSizePolicy
from PySide6.QtWidgets import QTabWidget, QPushButton, QComboBox, QSpinBox
from services.monthly_report_service import export_monthly_report
from views.student_history_window import StudentHistoryWindow
from services.student_report_service import export_student_report
from controllers.attendance_controller import AttendanceController
from controllers.app_controller import AppController
from PySide6.QtCore import QTimer, Qt, QTime
from utils.id_utils import normalize_id
from PySide6.QtWidgets import QLineEdit
from utils.time_utils import format_duration
from PySide6.QtWidgets import QPushButton, QFileDialog, QMessageBox
from models.student_repo import import_students_from_csv
from models.student_repo import get_student_basic_info
from services.daily_report_service import export_daily_report
from PySide6.QtWidgets import QMessageBox
from datetime import date
from datetime import datetime, timedelta
from PySide6.QtGui import QPixmap
from views.analytics_tab import AnalyticsTab
from models.input_mode import InputMode
from utils.resource_utils import resource_path


class StudentIdLineEdit(QLineEdit):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

    def focusInEvent(self, e):
        self.controller.set_input_mode(InputMode.MANUAL)
        super().focusInEvent(e)

    def focusOutEvent(self, e):
        # Only resume scanner in kiosk (attendance) mode
        parent = self.parent()
        if getattr(parent, "kiosk_mode", False):
            self.controller.set_input_mode(InputMode.SCANNER)
        super().focusOutEvent(e)


class MainWindow(QMainWindow):

    def _enable_manual_mode(self):
        self.attendance_controller.set_input_mode(InputMode.MANUAL)

    def _enable_scanner_mode(self):
        self.attendance_controller.set_input_mode(InputMode.SCANNER)


    def __init__(self):
        self.attendance_controller = AttendanceController()
        self.kiosk_mode = True

        super().__init__()
        self.setWindowTitle("Tunga Library Attendance")
        self.resize(1100, 650)

        # -------- CENTRAL WIDGET --------
        central = QWidget()
        self.setCentralWidget(central)

        tabs = QTabWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(12, 12, 12, 12)
        central_layout.setSpacing(12)
        # -------- HEADER --------
        header = QWidget()
        header.setObjectName("AppHeader")
        header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        header.setFixedHeight(120)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(14)

        logo = QLabel()
        logo.setObjectName("LogoLabel")
        logo_pix = QPixmap(resource_path("assets/logo.png"))
        if not logo_pix.isNull():
            logo.setPixmap(logo_pix.scaled(96, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo.setFixedSize(96, 96)
        logo.setAlignment(Qt.AlignCenter)

        titles_layout = QVBoxLayout()
        titles_layout.setContentsMargins(0, 0, 0, 0)
        titles_layout.setSpacing(4)

        self.lbl_college = QLabel("Tunga Mahavidyalaya")
        self.lbl_college.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.lbl_college.setObjectName("CollegeTitle")

        self.lbl_app = QLabel("Library Attendance Management System")
        self.lbl_app.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.lbl_app.setObjectName("AppTitle")

        titles_layout.addWidget(self.lbl_college)
        titles_layout.addWidget(self.lbl_app)

        header_layout.addWidget(logo, 0, Qt.AlignVCenter)
        header_layout.addLayout(titles_layout)
        header_layout.addStretch()

        central_layout.addWidget(header)

        central_layout.addWidget(tabs)

        attendance_tab = QWidget()
        tabs.addTab(attendance_tab, "Attendance")
        tabs.currentChanged.connect(self.on_tab_changed)

        main_layout = QHBoxLayout(attendance_tab)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(10, 4, 10, 10)

        # LEFT SIDE (Dashboard)
        left_layout = QVBoxLayout()
        left_layout.setSpacing(12)
        main_layout.addLayout(left_layout, 3)

        # -------- TOP BAR --------
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)
        top_bar.setContentsMargins(0, 0, 0, 0)
        left_layout.addLayout(top_bar)

        self.lbl_present = QLabel("Present: 0")
        self.lbl_present.setStyleSheet("font-size: 18px; font-weight: bold;")

        self.lbl_clock = QLabel()
        self.lbl_clock.setAlignment(Qt.AlignRight)
        self.lbl_clock.setStyleSheet("font-size: 16px;")

        top_bar.addWidget(self.lbl_present)
        top_bar.addStretch()
        top_bar.addWidget(self.lbl_clock)

        # -------- LIVE TABLE --------
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Name", "Class", "Start", "Duration"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)

        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.viewport().setFocusPolicy(Qt.NoFocus)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        left_layout.addWidget(self.table)

        self.table.setFocusPolicy(Qt.NoFocus)
        self.lbl_present.setFocusPolicy(Qt.NoFocus)
        self.lbl_clock.setFocusPolicy(Qt.NoFocus)

        self.attendance_controller.data_updated.connect(self.update_table)

        # self.scan_input = QLineEdit(attendance_tab)
        # self.scan_input.setFocusPolicy(Qt.StrongFocus)
        # self.scan_input.setAttribute(Qt.WA_InputMethodEnabled, True)
        # self.scan_input.setFixedSize(1, 1)
        # self.scan_input.setStyleSheet("border: none; background: transparent;")
        # self.scan_input.returnPressed.connect(self.on_scan_entered)
        # tabs.currentChanged.connect(self.on_tab_changed)
        #
        #
        # left_layout.addWidget(self.scan_input)
        #
        # # Force focus always
        # self.scan_input.setFocus()

        # -------- TIMERS --------
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)

        self.update_clock()

        self.btn_import = QPushButton("Import Students CSV")
        self.btn_import.clicked.connect(self.import_csv)
        top_bar.addWidget(self.btn_import)
        self.btn_import.setFocusPolicy(Qt.NoFocus)

        self.btn_export_daily = QPushButton("Export Daily Report")
        self.btn_export_daily.clicked.connect(self.export_today)

        self.btn_export_daily.setFocusPolicy(Qt.NoFocus)
        top_bar.addWidget(self.btn_export_daily)


        # -------- REPORTS TAB --------
        reports_tab = QWidget()
        tabs.addTab(reports_tab, "Reports")

        reports_layout = QVBoxLayout(reports_tab)
        reports_layout.setContentsMargins(40, 30, 40, 30)
        reports_layout.setSpacing(25)

        # ================= MONTHLY REPORT =================
        monthly_group = QGroupBox("Monthly Report")
        monthly_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        reports_layout.addWidget(monthly_group)

        monthly_layout = QHBoxLayout(monthly_group)
        monthly_layout.setSpacing(12)
        monthly_layout.setContentsMargins(14, 12, 14, 12)

        lbl_month = QLabel("Select Month:")
        monthly_layout.addWidget(lbl_month)

        self.month_combo = QComboBox()
        self.month_combo.addItems([
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ])
        self.month_combo.setCurrentIndex(datetime.now().month - 1)
        self.month_combo.setFocusPolicy(Qt.NoFocus)
        self.month_combo.setFixedWidth(140)
        monthly_layout.addWidget(self.month_combo)

        self.year_spin = QSpinBox()
        self.year_spin.setRange(2020, datetime.now().year + 5)
        self.year_spin.setValue(datetime.now().year)
        self.year_spin.setSuffix("")
        self.year_spin.setFocusPolicy(Qt.NoFocus)
        self.year_spin.setFixedWidth(90)
        monthly_layout.addWidget(self.year_spin)

        monthly_layout.addStretch()

        self.btn_monthly = QPushButton("Export Monthly Report")
        self.btn_monthly.setFixedWidth(200)
        self.btn_monthly.setFocusPolicy(Qt.NoFocus)
        self.btn_monthly.clicked.connect(self.export_monthly_clicked)
        monthly_layout.addWidget(self.btn_monthly)

        # ================= STUDENT REPORT =================
        student_group = QGroupBox("Student-Specific Report")
        student_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        reports_layout.addWidget(student_group)

        student_layout = QHBoxLayout(student_group)
        student_layout.setSpacing(15)

        lbl_sid = QLabel("Student ID:")
        student_layout.addWidget(lbl_sid)

        self.student_id_input = StudentIdLineEdit(self, self.attendance_controller)
        self.student_id_input.setPlaceholderText("S-1023")
        

        self.student_id_input.setFixedWidth(200)
        self.student_id_input.setFocusPolicy(Qt.StrongFocus)
        student_layout.addWidget(self.student_id_input)

        student_layout.addStretch()

        self.btn_student = QPushButton("Export Student Report")
        self.btn_student.setFixedWidth(200)
        self.btn_student.setFocusPolicy(Qt.NoFocus)
        self.btn_student.clicked.connect(self.export_student_clicked)
        student_layout.addWidget(self.btn_student)

        reports_layout.addStretch()

        #Analytics dashbord
        analytics_tab = AnalyticsTab()
        tabs.addTab(analytics_tab, "Analytics")

        self.app_controller = AppController()
        self.app_controller.auto_export_yesterday()
        self.attendance_controller.refresh()


    # def handle_background_scan(self, raw):
    #     sid = normalize_id(raw)
    #
    #     student = get_student_basic_info(sid)
    #     if not student:
    #         return  # silently ignore invalid scans
    #
    #     # Business logic only
    #     self.attendance_controller.process_scan(sid)
    #
    #     # 🔔 SHOW POPUP HERE (login / logout)
    #     self.app_controller.show_student_popup(
    #         sid=sid,
    #         name=student["name"]
    #     )

    def on_tab_changed(self, index):
        tab_name = self.sender().tabText(index)

        if tab_name == "Attendance":
            self.kiosk_mode = True
            self.attendance_controller.set_input_mode(InputMode.SCANNER)
        else:
            self.kiosk_mode = False
            self.attendance_controller.set_input_mode(InputMode.MANUAL)
            if tab_name == "Reports":
                self.student_id_input.setFocus()



    def export_monthly_clicked(self):
        self.attendance_controller.set_input_mode(InputMode.MANUAL)

        month = self.month_combo.currentIndex() + 1
        year = self.year_spin.value()

        try:
            path = export_monthly_report(year, month)
            QMessageBox.information(
                self,
                "Monthly Report",
                f"Monthly report exported successfully:\n{path}"
            )
        except Exception as e:
            QMessageBox.warning(self, "Monthly Report", str(e))

        self.attendance_controller.set_input_mode(InputMode.SCANNER)

    def export_student_clicked(self):
        # Pause scanner while admin works
        self.attendance_controller.set_input_mode(InputMode.MANUAL)

        sid = normalize_id(self.student_id_input.text())

        if not sid:
            QMessageBox.warning(self, "Student Report", "Enter a valid ID")
            self.attendance_controller.set_input_mode(InputMode.SCANNER)
            return

        student = get_student_basic_info(sid)
        if not student:
            QMessageBox.warning(self, "Student Report", "Student not found")
            self.attendance_controller.set_input_mode(InputMode.SCANNER)
            return

        dlg = StudentHistoryWindow(sid, student["name"])
        dlg.exec()  # blocks UI, scanner paused

        reply = QMessageBox.question(
            self,
            "Export Student Report",
            "Export this student's report?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            export_student_report(sid)

        self.student_id_input.clear()
        self.attendance_controller.set_input_mode(InputMode.SCANNER)

    # def on_scan_entered(self):
    #     raw = self.scan_input.text()
    #     self.scan_input.clear()
    #
    #     if not raw.strip():
    #         self.scan_input.setFocus()
    #         return
    #
    #     sid = normalize_id(raw)
    #
    #     student = get_student_basic_info(sid)
    #     if student is None:
    #         QMessageBox.warning(
    #             self,
    #             "Invalid ID",
    #             "Student not found.\nPlease scan again."
    #         )
    #         self.scan_input.setFocus()
    #         return
    #
    #     # 🔥 ONLY business logic now
    #     self.attendance_controller.process_scan(sid)
    #
    #     # ❌ No student info update here
    #     self.scan_input.setFocus()

    def update_clock(self):
        self.lbl_clock.setText(QTime.currentTime().toString("HH:mm:ss"))

    def update_table(self, rows, present):
        self.table.setRowCount(len(rows))

        for r, (sid, name, cls, start, end, dur) in enumerate(rows):
            self.table.setItem(r, 0, QTableWidgetItem(sid))
            self.table.setItem(r, 1, QTableWidgetItem(name))
            self.table.setItem(r, 2, QTableWidgetItem(cls))
            self.table.setItem(r, 3, QTableWidgetItem(start))
            self.table.setItem(r, 4, QTableWidgetItem(format_duration(int(dur))))

        self.lbl_present.setText(f"Present: {present}")

    def showEvent(self, event):
        super().showEvent(event)
        self.activateWindow()
        self.raise_()


    def import_csv(self):
        self.attendance_controller.set_input_mode(InputMode.MANUAL)

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Students CSV",
            "",
            "CSV Files (*.csv)"
        )

        if not file_path:
            self.attendance_controller.set_input_mode(InputMode.SCANNER)
            return

        try:
            count = import_students_from_csv(file_path)

            QMessageBox.information(
                self,
                "CSV Import",
                f"Imported / updated {count} students successfully."
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "CSV Import Failed",
                str(e)
            )

        # Return focus to scanner regardless of outcome
        self.attendance_controller.set_input_mode(InputMode.SCANNER)

    def export_today(self):
        self.attendance_controller.set_input_mode(InputMode.MANUAL)

        try:
            path = export_daily_report(date.today())

            QMessageBox.information(
                self,
                "Daily Report",
                f"Daily report exported successfully:\n{path}"
            )

        except Exception as e:
            QMessageBox.warning(
                self,
                "Daily Report",
                str(e)
            )

        self.attendance_controller.set_input_mode(InputMode.SCANNER)

    def closeEvent(self, event):
        if self.kiosk_mode:
            event.ignore()
        else:
            event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F12:
            self.kiosk_mode = False



