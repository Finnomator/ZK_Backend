from sqlmodel import SQLModel, Field


class _AdminBase(SQLModel):
    username: str = Field(primary_key=True)

class AdminDB(_AdminBase, table=True):
    password_hash: bytes

class AdminCreate(_AdminBase):
    password: str
