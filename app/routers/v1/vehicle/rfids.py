import hashlib
import base64
import logging
from typing import Annotated

from fastapi import APIRouter, Response, Header
from sqlmodel import select, Session
from starlette.status import HTTP_304_NOT_MODIFIED

from app import database
from app.internal.helper import rfid_uids_to_little_endian_bytes
from app.models.rfid import RfidUidDB

log = logging.getLogger("app.rfids")

router = APIRouter(prefix="/rfids", tags=["RFIDs"])


# TODO: Caching


def get_rfid_uids_bin(session: Session):
    rfid_uids: list[int] = session.exec(select(RfidUidDB.rfid_uid)).all()
    bin_rfid_uids = rfid_uids_to_little_endian_bytes(rfid_uids)
    return bin_rfid_uids


@router.get(
    "/",
    response_model=list[int] | None,
    responses={304: {"description": "Not Modified"}},
)
def get_rfids(
    session: database.SessionDep,
    if_none_match: Annotated[str | None, Header()] = None,
) -> list[int] | Response:
    if if_none_match is not None:
        md5_raw = hashlib.md5(get_rfid_uids_bin(session)).digest()
        md5_b64 = base64.b64encode(md5_raw).decode()

        if if_none_match == md5_b64:
            log.debug("RFID list unchanged", extra={"checksum": md5_b64})
            return Response(status_code=HTTP_304_NOT_MODIFIED)

    rfid_uids: list[int] = session.exec(select(RfidUidDB.rfid_uid)).all()
    # Sending the list means a device is about to replace the UIDs it grants
    # access with, so it is worth a line even though it is not an error.
    log.info("Serving %d RFID UIDs (device list was stale or unknown)", len(rfid_uids),
             extra={"uids": len(rfid_uids), "had_checksum": if_none_match is not None})
    return rfid_uids


# https://github.com/swagger-api/swagger-ui/issues/4791


@router.get("/md5-checksum")
async def get_rfids_md5_checksum(session: database.SessionDep):
    md5_hash = hashlib.md5(get_rfid_uids_bin(session)).digest()
    return Response(content=md5_hash, media_type="application/octet-stream")
