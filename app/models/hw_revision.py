from sqlmodel import SQLModel, Field, Relationship


class HardwareRevisionDB(SQLModel, table=True):
    revision_number: int = Field(primary_key=True)
    compatible_firmwares: list["FirmwareDB"] | None = Relationship(back_populates="compatible_hardware")
    devices: list["DeviceDB"] | None = Relationship(back_populates="hw_revision")
