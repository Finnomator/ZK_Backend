from sqlmodel import SQLModel, Field, Relationship

from app.models import DeviceDB


class HardwareRevisionDB(SQLModel, table=True):
    revision_number: int = Field(primary_key=True)
    compatible_firmwares: list["FirmwareDB"] = Relationship(back_populates="compatible_hardware")
    devices: list[DeviceDB] = Relationship(back_populates="hw_revision")
