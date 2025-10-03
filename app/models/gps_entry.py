from datetime import datetime

from sqlalchemy import Column, SmallInteger, REAL, BigInteger, ForeignKey
from sqlmodel import SQLModel, Field, Relationship

from app.models.ints import CHIP_ID
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
    chip_id: CHIP_ID = Field(sa_column=Column(BigInteger(), ForeignKey("vehicledb.chip_id")))
    vehicle: VehicleDB = Relationship(back_populates="gps_entries")
