import re
from enum import Enum

from pydantic import field_validator
from sqlmodel import SQLModel, Field, Relationship

from app.models.firmware import FirmwareDB
from app.models.firmware_update import FirmwareUpdateDB

license_plate_re = re.compile(r"^[A-ZÄÖÜ]{1,3}-[A-Z]{1,2}\d{1,4}$")  # For germany


class VehicleType(str, Enum):
    Car = "Car"


class _VehicleBase(SQLModel):
    imei: str = Field(primary_key=True)
    name: str
    type: VehicleType
    license_plate: str | None = None

    @field_validator("license_plate")
    def check_license_place(cls, v):

        if v is None:
            return v

        v = v.replace(" ", "").upper()

        if not license_plate_re.match(v):
            raise ValueError(f"Invalid license plate: {v}")

        return v


class VehicleDB(_VehicleBase, table=True):
    current_firmware_version: str | None = Field(default=None, foreign_key="firmwaredb.version")

    logs: list["LogEntryDB"] = Relationship(back_populates="vehicle")
    gps_entries: list["GpsEntryDB"] = Relationship(back_populates="vehicle")
    current_firmware: FirmwareDB | None = Relationship(back_populates="vehicles")
    pending_update: FirmwareUpdateDB | None = Relationship(back_populates="vehicle")
