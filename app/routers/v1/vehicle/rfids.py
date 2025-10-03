import hashlib

from fastapi import APIRouter, Response
from sqlmodel import select, Session

from app import database
from app.internal.helper import rfid_uids_to_little_endian_bytes
from app.models.rfid import RfidUidDB

router = APIRouter(prefix="/rfids", tags=["RFIDs"])


# TODO: Caching

def get_rfid_uids_bin(session: Session):
    rfid_uids: list[int] = session.exec(select(RfidUidDB.rfid_uid)).all()
    bin_rfid_uids = rfid_uids_to_little_endian_bytes(rfid_uids)
    return bin_rfid_uids

@router.get("/")
def get_rfids(session: database.SessionDep) -> list[int]:
    rfid_uids: list[int] = session.exec(select(RfidUidDB.rfid_uid)).all()
    return rfid_uids

# https://github.com/swagger-api/swagger-ui/issues/4791

@router.get("/md5-checksum")
async def get_rfids_md5_checksum(session: database.SessionDep):
    md5_hash = hashlib.md5(get_rfid_uids_bin(session)).digest()
    return Response(content=md5_hash, media_type="application/octet-stream")
