import logging
import threading
from datetime import datetime, timedelta
from PySide6.QtCore import QObject, QTimer, Signal

from models.meta_repo import get_meta, set_meta
from services.backup_service import backup_now, load_backup_config
from services.daily_report_service import export_daily_report

logger = logging.getLogger(__name__)


class AppController(QObject):
    META_KEY = "last_daily_export"
    backup_status_changed = Signal(bool, str)  # (success, status_message)

    def __init__(self):
        super().__init__()
        self._backup_in_progress = False
        self.backup_timer = QTimer(self)
        self.backup_timer.timeout.connect(self._run_scheduled_backup)
        self._setup_backup()

    def _setup_backup(self):
        config = load_backup_config()
        if not config:
            logger.info("Cloud backup not configured — skipping automatic backups")
            print("Cloud backup not configured — skipping automatic backups")
            return

        interval_min = config.get("backup_interval_minutes")
        if interval_min and isinstance(interval_min, (int, float)) and interval_min > 0:
            interval_ms = int(interval_min * 60 * 1000)
            self.backup_timer.start(interval_ms)
            logger.info(f"Automatic cloud backup scheduled every {interval_min} minutes.")
        else:
            logger.info("Cloud backup configured without interval — automatic backups disabled.")

    def _run_scheduled_backup(self):
        if self._backup_in_progress:
            logger.warning("Scheduled backup skipped — backup already in progress.")
            return

        self.run_backup_async()

    def run_backup_async(self, callback=None):
        if self._backup_in_progress:
            if callback:
                callback(False, "A backup is already in progress.")
            return False

        self._backup_in_progress = True

        def _worker():
            try:
                success, msg = backup_now()
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if success:
                    status_text = f"Last backup: {ts}"
                else:
                    status_text = f"Last backup failed: {msg}"
                self.backup_status_changed.emit(success, status_text)
                if callback:
                    callback(success, msg)
            except Exception as e:
                err_msg = str(e)
                self.backup_status_changed.emit(False, f"Last backup failed: {err_msg}")
                if callback:
                    callback(False, err_msg)
            finally:
                self._backup_in_progress = False

        threading.Thread(target=_worker, daemon=True).start()
        return True

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

