from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session

from app.internal import config
from app.internal.config import DATABASE_URL
from app.models.admin import AdminDB

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

SessionDep = Annotated[Session, Depends(get_session)]
