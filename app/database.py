import logging
from datetime import datetime, timezone, timedelta
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine, delete
from sqlmodel import SQLModel, Session

from app.internal import config
from app.internal.config import DATABASE_URL
from app.models import AdminDB, GpsEntryDB, LogEntryDB

log = logging.getLogger("app.db")

engine = create_engine(DATABASE_URL)


def get_session():
    with Session(engine) as session:
        yield session


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    log.info("Database schema is up to date")


def insert_default_admin():
    with Session(engine) as session:
        if session.get(AdminDB, config.DEFAULT_ADMIN_NAME) is not None:
            return
        admin = AdminDB(username=config.DEFAULT_ADMIN_NAME, password_hash=config.DEFAULT_ADMIN_HASH)
        session.add(admin)
        session.commit()
        # Only ever on a fresh database, and it means an account exists whose
        # password came from the environment.
        log.warning("Created the default admin account %r", config.DEFAULT_ADMIN_NAME,
                    extra={"username": config.DEFAULT_ADMIN_NAME})


class UserDataDeletionResult:
    gps_entries_deleted: int
    log_entries_deleted: int

    def __init__(self, gps_entries_deleted: int, log_entries_deleted: int):
        self.gps_entries_deleted = gps_entries_deleted
        self.log_entries_deleted = log_entries_deleted


def remove_user_data_older_than(td: timedelta, dry_run: bool):
    now = datetime.now(tz=timezone.utc)
    delete_timestamp = now - td

    with Session(engine) as session:
        gps_result = session.exec(delete(GpsEntryDB).where(GpsEntryDB.timestamp < delete_timestamp))
        log_result = session.exec(delete(LogEntryDB).where(LogEntryDB.timestamp < delete_timestamp))

        if dry_run:
            session.rollback()
            log.info("Retention dry run: would delete %d GPS and %d log entries older than %s",
                     gps_result.rowcount, log_result.rowcount, delete_timestamp.isoformat())
        else:
            session.commit()

        return UserDataDeletionResult(gps_result.rowcount, log_result.rowcount)


SessionDep = Annotated[Session, Depends(get_session)]
