from datetime import timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from app import database

scheduler = BackgroundScheduler()
scheduler.start()


def _delete_old_user_data():
    result = database.remove_user_data_older_than(timedelta(days=6 * 30), False)
    print(f"Deleted {result.gps_entries_deleted} GPS entries and {result.log_entries_deleted} log entries")


def start_background_user_data_cleanup_task():
    scheduler.add_job(_delete_old_user_data, "interval", days=1, id="delete_user_data")


def stop_background_user_data_cleanup_task():
    scheduler.remove_job("delete_user_data")
