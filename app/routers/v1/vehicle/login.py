from datetime import datetime
import logging

from fastapi import APIRouter, Depends

from app import database
from app.models.device import DeviceDB
from app.models.rfid import RfidUidDB
from app.auth import auth_device

log = logging.getLogger("app.devicelogin")

router = APIRouter(prefix="/login", tags=["Login"])

@router.get("/check-access")
async def check_access(rfid_uid: str, timestamp: datetime, session: database.SessionDep, device: DeviceDB = Depends(auth_device)):

    # What happens if the timestamp is invalid e.g. 1990 something?

    uid_is_whitelisted = session.get(RfidUidDB, rfid_uid) is not None
    has_valid_booking = True # TODO

    return {
        "whitelist": uid_is_whitelisted,
        "valid booking": has_valid_booking
    }
