import logging
from datetime import timedelta

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_MISSED
from apscheduler.schedulers.background import BackgroundScheduler
from app import database
from app import vehicle_locations

log = logging.getLogger("app.tasks")

RETENTION = timedelta(days=6 * 30)

scheduler = BackgroundScheduler()


def _on_job_problem(event):
    # A scheduled job that dies takes its traceback with it unless the scheduler
    # is asked to hand it over.
    if event.code == EVENT_JOB_MISSED:
        log.warning("Scheduled job %s missed its run time", event.job_id,
                    extra={"job_id": event.job_id})
    else:
        log.error("Scheduled job %s failed", event.job_id,
                  exc_info=event.exception, extra={"job_id": event.job_id})


scheduler.add_listener(_on_job_problem, EVENT_JOB_ERROR | EVENT_JOB_MISSED)
scheduler.start()


def _delete_old_user_data():
    log.info("Deleting user data older than %s days", RETENTION.days)
    result = database.remove_user_data_older_than(RETENTION, False)
    log.info("Retention sweep removed %d GPS entries and %d log entries",
             result.gps_entries_deleted, result.log_entries_deleted,
             extra={"gps_entries_deleted": result.gps_entries_deleted,
                    "log_entries_deleted": result.log_entries_deleted,
                    "retention_days": RETENTION.days})


def start_background_user_data_cleanup_task():
    scheduler.add_job(_delete_old_user_data, "interval", days=1, id="delete_user_data")
    log.info("Scheduled the daily user-data retention sweep")


def stop_background_user_data_cleanup_task():
    scheduler.remove_job("delete_user_data")
    log.info("Stopped the user-data retention sweep")


def start_vehicle_location_gathering():
    scheduler.add_job(vehicle_locations.fetch_locations_and_place_in_db, "interval", days=1, id="gather_vehicle_locations")
    log.info("Scheduled the daily vehicle location fetch")

def stop_vehicle_location_gathering():
    scheduler.remove_job("gather_vehicle_locations")
    log.info("Stopped the vehicle location fetch")
