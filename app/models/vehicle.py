from enum import Enum

from sqlmodel import SQLModel, Field, Relationship


class VehicleType(str, Enum):
    Car = "Car"


class _VehicleBase(SQLModel):
    imei: str = Field(primary_key=True)
    name: str
    type: VehicleType


class VehicleDB(_VehicleBase, table=True):
    logs: list["LogEntryDB"] = Relationship(back_populates="vehicle")
    gps_entries: list["GpsEntryDB"] = Relationship(back_populates="vehicle")
