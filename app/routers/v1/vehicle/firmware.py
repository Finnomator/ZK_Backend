import hashlib
from datetime import datetime, timezone

from fastapi import APIRouter, Response, Depends
from fastapi import HTTPException
from sqlmodel import select

from app.auth import auth_device
from app.database import SessionDep
from app.models.device import DeviceDB
from app.models.firmware import FirmwareDB

router = APIRouter(prefix="/firmware", tags=["Firmware"])

no_firmware_available_exception = HTTPException(204, "No firmware available")

@router.get("/is-newer-available")
def is_newer_firmware_available(fm_version: str, session: SessionDep, device: DeviceDB = Depends(auth_device)):
    cur_firmware = session.exec(select(FirmwareDB).where(FirmwareDB.version == fm_version)).first()

    device.current_firmware = cur_firmware  # if cur_firmware is none its unknown
    session.commit()

    pending_update = device.pending_update

    if pending_update is None:
        return False

    newer_version = pending_update.target_firmware.version
    return fm_version != newer_version


@router.get("/latest")
def get_latest_firmware_file(
    session: SessionDep,
    fm_version: str | None = None,
    device: DeviceDB = Depends(auth_device),
):

    if fm_version is not None:
        cur_firmware = session.exec(
            select(FirmwareDB).where(FirmwareDB.version == fm_version)
        ).first()
        device.current_firmware = cur_firmware  # if cur_firmware is none its unknown
        session.commit()

    pending_update = device.pending_update
    if pending_update is None:
        raise no_firmware_available_exception

    if fm_version is not None and pending_update.target_firmware.version == fm_version:
        raise no_firmware_available_exception

    pending_update.update_last_downloaded = datetime.now(tz=timezone.utc)
    session.commit()

    new_firmware: bytes = pending_update.target_firmware.firmware

    return Response(
        status_code=200,
        content=new_firmware,
        media_type="application/octet-stream",
        headers={"x-MD5": hashlib.md5(new_firmware).hexdigest()},
    )


@router.get("/latest/size")
def get_latest_firmware_size(device: DeviceDB = Depends(auth_device)) -> int:
    pending_update = device.pending_update
    if pending_update is None:
        raise no_firmware_available_exception
    return len(pending_update.target_firmware.firmware)
