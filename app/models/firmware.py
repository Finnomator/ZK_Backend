from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

from app.models.hw_revision import HardwareRevisionDB, HardwareFirmwareLink


class _FirmwareBase(SQLModel):
    version: str = Field(primary_key=True)
    added: datetime = Field(default_factory=datetime.utcnow)

class FirmwareDB(_FirmwareBase, table=True):
    firmware: bytes
    bootloader: bytes | None = None
    partitions: bytes | None = None

    devices: list["DeviceDB"] | None = Relationship(back_populates="current_firmware")
    pending_updates: list["FirmwareUpdateDB"] | None = Relationship(back_populates="target_firmware")
    compatible_hardware: list[HardwareRevisionDB] | None = Relationship(
        back_populates="compatible_firmwares", link_model=HardwareFirmwareLink
    )

class FirmwarePublic(_FirmwareBase):
    ...
