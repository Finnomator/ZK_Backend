from datetime import datetime

from sqlalchemy import Column, SmallInteger, REAL, ForeignKey
from sqlmodel import SQLModel, Field, Relationship

from app.models.vehicle import VehicleDB


class _GpsEntryBase(SQLModel):
    latitude: float = Field(sa_column=Column(REAL()))
    longitude: float = Field(sa_column=Column(REAL()))
    speed: float = Field(sa_column=Column(REAL()))
    altitude: float = Field(sa_column=Column(REAL()))
    vsat: int = Field(sa_column=Column(SmallInteger()))
    usat: int = Field(sa_column=Column(SmallInteger()))
    accuracy: float = Field(sa_column=Column(REAL()))
    timestamp: datetime


class GpsEntryDB(_GpsEntryBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    imei: str = Field(sa_column=Column(ForeignKey("vehicledb.imei")))
    vehicle: VehicleDB = Relationship(back_populates="gps_entries")
