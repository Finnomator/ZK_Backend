from sqlmodel import SQLModel, Field, Relationship


class HardwareFirmwareLink(SQLModel, table=True):
    hw_revision_number: int = Field(foreign_key="hardwarerevisiondb.revision_number", primary_key=True)
    firmware_version: str = Field(foreign_key="firmwaredb.version", primary_key=True)


class HardwareRevisionDB(SQLModel, table=True):
    revision_number: int = Field(primary_key=True)
    compatible_firmwares: list["FirmwareDB"] | None = Relationship(
        back_populates="compatible_hardware", link_model=HardwareFirmwareLink
    )
    devices: list["DeviceDB"] | None = Relationship(back_populates="hw_revision")
