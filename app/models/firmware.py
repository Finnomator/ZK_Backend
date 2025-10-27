from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class _FirmwareBase(SQLModel):
    version: str = Field(primary_key=True)
    added: datetime = Field(default_factory=datetime.utcnow)

class FirmwareDB(_FirmwareBase, table=True):
    file: bytes
    vehicles: list["VehicleDB"] | None = Relationship(back_populates="current_firmware")
    pending_updates: list["FirmwareUpdateDB"] | None = Relationship(back_populates="target_firmware")


class FirmwarePublic(_FirmwareBase):
    ...
