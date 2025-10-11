from sqlalchemy import Column, BigInteger
from sqlmodel import SQLModel, Field


class _RfidUidBase(SQLModel):
    rfid_uid: int


class RfidUidDB(_RfidUidBase, table=True):
    rfid_uid: int = Field(sa_column=Column(BigInteger(), primary_key=True))


class GpsTrackingConsentRfidUidDB(_RfidUidBase, table=True):
    rfid_uid: int = Field(sa_column=Column(BigInteger(), primary_key=True))
