# views/input_capture.py
from pynput import keyboard
from threading import Thread

class InputCapture:
    def __init__(self, callback):
        self.callback = callback
        self.buffer = ""

        self.listener = keyboard.Listener(on_press=self._on_key)
        self.listener.start()

    def _on_key(self, key):
        try:
            if key == keyboard.Key.enter:
                if self.buffer:
                    self.callback(self.buffer)
                self.buffer = ""
            elif hasattr(key, 'char') and key.char:
                self.buffer += key.char
        except Exception:
            pass
