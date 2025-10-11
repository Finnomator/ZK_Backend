from datetime import datetime

from packaging.version import Version
from sqlmodel import SQLModel, Field, Relationship

class _FirmwareBase(SQLModel):
    major: int
    minor: int
    patch: int
    added: datetime = Field(default_factory=datetime.utcnow)

class FirmwareDB(_FirmwareBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    file: bytes
    vehicles: list["VehicleDB"] = Relationship(back_populates="current_firmware")
    pending_updates: list["FirmwareUpdateDB"] = Relationship(back_populates="target_firmware")

    def get_version(self) -> Version:
        return Version(f"{self.major}.{self.minor}.{self.patch}")

class FirmwarePublic(_FirmwareBase):
    id: int | None
