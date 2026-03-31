from PySide6.QtWidgets import QWidget, QLineEdit
from PySide6.QtCore import Qt, QTimer


class InputCaptureWindow(QWidget):
    def __init__(self, on_scan_callback):
        super().__init__()

        self.on_scan_callback = on_scan_callback
        self._active = False

        # Invisible always-on-top window that stays out of view
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(1, 1)

        # Hidden input field
        self.input = QLineEdit(self)
        self.input.setFixedSize(1, 1)
        self.input.returnPressed.connect(self._on_enter)

        self.focus_timer = QTimer(self)
        self.focus_timer.timeout.connect(self._force_focus)
        self.focus_timer.setInterval(1500)

        # Start listening immediately
        self.start()

    def start(self):
        """Enable scanner capture and keep the hidden field focused."""
        if self._active:
            return

        self._active = True
        self.show()
        self._force_focus()
        if not self.focus_timer.isActive():
            self.focus_timer.start()

    def stop(self):
        """Pause scanner capture so other inputs can keep focus."""
        if not self._active:
            return

        self._active = False
        if self.focus_timer.isActive():
            self.focus_timer.stop()
        self.hide()

    def _force_focus(self):
        if not self._active:
            return

        self.show()
        self.raise_()
        self.activateWindow()
        self.input.setFocus()

    def _on_enter(self):
        text = self.input.text().strip()
        self.input.clear()

        if text:
            self.on_scan_callback(text)

        self.input.setFocus()
