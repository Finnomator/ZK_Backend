from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field, Relationship


class _FirmwareUpdateBase(SQLModel):
    id: int | None = Field(default=None, primary_key=True)
    update_issued_at: datetime = Field(default_factory=datetime.utcnow)
    update_last_downloaded: datetime | None = None
    target_vehicle_imei: str = Field(foreign_key="vehicledb.imei", unique=True)
    target_firmware_version: str = Field(foreign_key="firmwaredb.version")


class FirmwareUpdateDB(_FirmwareUpdateBase, table=True):
    vehicle: Optional["VehicleDB"] = Relationship(back_populates="pending_update")
    target_firmware: Optional["FirmwareDB"] = Relationship(back_populates="pending_updates")


class FirmwareUpdatePublic(_FirmwareUpdateBase):
    ...
