from sqlalchemy import Column, BigInteger
from sqlmodel import SQLModel, Field

from app.models.ints import RFID_UID


class _RfidUidBase(SQLModel):
    rfid_uid: RFID_UID

class RfidUidDB(_RfidUidBase, table=True):
    rfid_uid: RFID_UID = Field(sa_column=Column(BigInteger(), primary_key=True))


class GpsTrackingConsentRfidUidDB(_RfidUidBase, table=True):
    rfid_uid: RFID_UID = Field(sa_column=Column(BigInteger(), primary_key=True))
