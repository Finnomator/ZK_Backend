from enum import Enum
from sqlmodel import SQLModel, Field, Relationship

from app.models.firmware import FirmwareDB
from app.models.firmware_update import FirmwareUpdateDB


class VehicleType(str, Enum):
    Car = "Car"


class _VehicleBase(SQLModel):
    imei: str = Field(primary_key=True)
    name: str
    type: VehicleType


class VehicleDB(_VehicleBase, table=True):
    current_firmware_id: int | None = Field(default=None, foreign_key="firmwaredb.id")

    logs: list["LogEntryDB"] = Relationship(back_populates="vehicle")
    gps_entries: list["GpsEntryDB"] = Relationship(back_populates="vehicle")
    current_firmware: FirmwareDB | None = Relationship(back_populates="vehicles")
    pending_update: FirmwareUpdateDB | None = Relationship(back_populates="vehicle")
