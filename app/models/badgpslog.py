from datetime import datetime

from sqlmodel import SQLModel, Field, Relationship

from app.models import DeviceDB


class _BadGpsLog(SQLModel):
    raw_data: bytes
    upload_timestamp: datetime
    was_reintegrated: bool = False

class BadGpsLogDB(_BadGpsLog, table=True):
    id: int | None = Field(default=None, primary_key=True)
    imei: str = Field(foreign_key="devicedb.imei")
    device: DeviceDB | None = Relationship(back_populates="badgpslogs")
