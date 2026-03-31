from PySide6.QtCore import QObject, Signal

class ScannerService(QObject):
    scan_completed = Signal(str)

    def __init__(self):
        super().__init__()
        self.buffer = ""

    def process_key(self, text, is_enter):
        if is_enter:
            if len(self.buffer) >= 4:
                self.scan_completed.emit(self.buffer)
            self.buffer = ""
        else:
            self.buffer += text
