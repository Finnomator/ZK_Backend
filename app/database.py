from datetime import datetime, timezone, timedelta
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine, delete
from sqlmodel import SQLModel, Session

from app.internal import config
from app.internal.config import DATABASE_URL
from app.models.admin import AdminDB
from app.models.gps_entry import GpsEntryDB
from app.models.log import LogEntryDB

engine = create_engine(DATABASE_URL)


def get_session():
    with Session(engine) as session:
        yield session


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def insert_default_admin():
    with Session(engine) as session:
        if session.get(AdminDB, config.DEFAULT_ADMIN_NAME) is not None:
            return
        admin = AdminDB(username=config.DEFAULT_ADMIN_NAME, password_hash=config.DEFAULT_ADMIN_HASH)
        session.add(admin)
        session.commit()


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
        else:
            session.commit()

        return UserDataDeletionResult(gps_result.rowcount, log_result.rowcount)


SessionDep = Annotated[Session, Depends(get_session)]
