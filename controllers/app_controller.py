from datetime import datetime, timedelta
from services.daily_report_service import export_daily_report
from models.meta_repo import get_meta, set_meta


class AppController:
    META_KEY = "last_daily_export"

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
