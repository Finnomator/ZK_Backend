from enum import Enum

from sqlalchemy import Column, BigInteger
from sqlmodel import SQLModel, Field, Relationship

class VehicleType(str, Enum):
    Car = "Car"


class _VehicleBase(SQLModel):
    chip_id: int = Field(sa_column=Column(BigInteger(), primary_key=True))
    name: str
    type: VehicleType


class VehicleDB(_VehicleBase, table=True):
    logs: list["LogEntryDB"] = Relationship(back_populates="vehicle")
    gps_entries: list["GpsEntryDB"] = Relationship(back_populates="vehicle")
