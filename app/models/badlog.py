from datetime import datetime

from sqlmodel import SQLModel, Relationship, Field

from app.models.device import DeviceDB


class _BadLogBase(SQLModel):
    text: str
    upload_timestamp: datetime
    was_reintegrated: bool = False

class BadLogDB(_BadLogBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    imei: str = Field(foreign_key="devicedb.imei")
    device: DeviceDB | None = Relationship(back_populates="badlogs")
