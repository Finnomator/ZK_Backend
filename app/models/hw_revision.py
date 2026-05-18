from sqlmodel import SQLModel, Field, Relationship


class HardwareRevisionDB(SQLModel, table=True):
    revision_number: int = Field(primary_key=True)
    devices: list["DeviceDB"] | None = Relationship(back_populates="hw_revision")
