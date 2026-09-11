from unittest.mock import MagicMock
from PySide6.QtWidgets import QApplication
import sys
import pytest
from controllers.app_controller import AppController

# Ensure QApplication exists for QObject/QTimer
app = QApplication.instance() or QApplication(sys.argv)

def test_app_controller_unconfigured(monkeypatch):
    monkeypatch.setattr("controllers.app_controller.load_backup_config", lambda: None)
    controller = AppController()
    assert not controller.backup_timer.isActive()

def test_app_controller_configured(monkeypatch):
    mock_config = {
        "bucket_name": "test-bucket",
        "backup_interval_minutes": 30
    }
    monkeypatch.setattr("controllers.app_controller.load_backup_config", lambda: mock_config)
    controller = AppController()
    assert controller.backup_timer.isActive()
    assert controller.backup_timer.interval() == 30 * 60 * 1000

def test_app_controller_overlapping_prevention(monkeypatch):
    monkeypatch.setattr("controllers.app_controller.load_backup_config", lambda: None)
    controller = AppController()
    controller._backup_in_progress = True
    
    cb = MagicMock()
    result = controller.run_backup_async(callback=cb)
    assert result is False
    cb.assert_called_once_with(False, "A backup is already in progress.")
