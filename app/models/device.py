from sqlmodel import SQLModel, Field, Relationship

from app.models.firmware import FirmwareDB
from app.models.firmware_update import FirmwareUpdateDB


class _DeviceBase(SQLModel):
    imei: str = Field(primary_key=True)
    name: str | None = Field(default=None, unique=True)

class DeviceDB(_DeviceBase, table=True):
    current_firmware_version: str | None = Field(default=None, foreign_key="firmwaredb.version")

    logs: list["LogEntryDB"] | None = Relationship(back_populates="device")
    gps_entries: list["GpsEntryDB"] | None = Relationship(back_populates="device")
    current_firmware: FirmwareDB | None = Relationship(back_populates="devices")
    pending_update: FirmwareUpdateDB | None = Relationship(back_populates="device")
    badlogs: list["BadLogDB"] | None = Relationship(back_populates="device")
