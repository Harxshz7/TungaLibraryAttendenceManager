from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PySide6.QtCore import Qt
from models.settings_repo import verify_pin

class PinDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Admin PIN Required")
        self.setFixedSize(300, 150)
        self.setModal(True)
        
        self.attempts = 0
        self.max_attempts = 3
        
        layout = QVBoxLayout(self)
        
        self.lbl_instruction = QLabel("Enter Admin PIN:")
        layout.addWidget(self.lbl_instruction)
        
        self.pin_input = QLineEdit()
        self.pin_input.setEchoMode(QLineEdit.Password)
        self.pin_input.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.pin_input)
        
        self.lbl_forgot = QLabel("<a href='#'>Forgot PIN?</a>")
        self.lbl_forgot.setOpenExternalLinks(False)
        self.lbl_forgot.setAlignment(Qt.AlignRight)
        layout.addWidget(self.lbl_forgot)
        
        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton("OK")
        self.btn_cancel = QPushButton("Cancel")
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_ok)
        layout.addLayout(btn_layout)
        
        self.btn_ok.clicked.connect(self.check_pin)
        self.btn_cancel.clicked.connect(self.reject)
        self.pin_input.returnPressed.connect(self.check_pin)
        
    def check_pin(self):
        candidate = self.pin_input.text()
        if verify_pin(candidate):
            self.accept()
        else:
            self.attempts += 1
            if self.attempts >= self.max_attempts:
                QMessageBox.critical(self, "Locked", "Too many failed attempts.")
                self.reject()
            else:
                QMessageBox.warning(self, "Incorrect PIN", f"Incorrect PIN. {self.max_attempts - self.attempts} attempts remaining.")
                self.pin_input.clear()
                self.pin_input.setFocus()
                
    @staticmethod
    def verify(parent=None) -> bool:
        dialog = PinDialog(parent)
        result = dialog.exec()
        return result == QDialog.Accepted
