from sqlmodel import SQLModel, Field

class FirmwareBase(SQLModel):
    file: bytes
    major: int = Field(primary_key=True)
    minor: int = Field(primary_key=True)
    patch: int = Field(primary_key=True)


class FirmwareDB(FirmwareBase, table=True):
    ...
