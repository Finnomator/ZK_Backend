from datetime import datetime

from sqlmodel import SQLModel, Relationship, Field

from app.models.vehicle import VehicleDB


class _BadLogBase(SQLModel):
    text: str
    upload_timestamp: datetime

class BadLogDB(_BadLogBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    imei: str = Field(foreign_key="vehicledb.imei")
    vehicle: VehicleDB | None = Relationship(back_populates="badlogs")
