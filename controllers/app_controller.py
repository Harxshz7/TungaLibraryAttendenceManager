from datetime import datetime, timedelta
from PySide6.QtCore import QTimer
import threading
from services.daily_report_service import export_daily_report
from models.meta_repo import get_meta, set_meta
from services.backup_service import load_backup_config, backup_now

class AppController:
    META_KEY = "last_daily_export"

    def __init__(self):
        self.backup_timer = QTimer()
        self.backup_timer.timeout.connect(self._run_backup_async)
        self._setup_backup()

    def _setup_backup(self):
        config = load_backup_config()
        if config and config.get("backup_interval_minutes"):
            interval_ms = config["backup_interval_minutes"] * 60 * 1000
            self.backup_timer.start(interval_ms)

    def _run_backup_async(self):
        threading.Thread(target=backup_now, daemon=True).start()

    def auto_export_yesterday(self):
        yesterday = (datetime.now() - timedelta(days=1)).date()
        last = get_meta(self.META_KEY)

        if last == yesterday.isoformat():
            return

        try:
            export_daily_report(yesterday)
        except ValueError:
            pass  # no data is valid
        finally:
            set_meta(self.META_KEY, yesterday.isoformat())
