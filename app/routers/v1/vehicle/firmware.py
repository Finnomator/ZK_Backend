from datetime import datetime, timezone

from fastapi import APIRouter, Response, Depends
from fastapi import HTTPException
from sqlmodel import select

from app.auth import auth_vehicle
from app.database import SessionDep
from app.models.firmware import FirmwareDB
from app.models.vehicle import VehicleDB

router = APIRouter(prefix="/firmware", tags=["Firmware"])

no_firmware_available_exception = HTTPException(204, "No firmware available")

@router.get("/is-newer-available")
def is_newer_firmware_available(fm_version: str, session: SessionDep, car: VehicleDB = Depends(auth_vehicle)):
    cur_firmware = session.exec(select(FirmwareDB).where(FirmwareDB.version == fm_version)).first()

    car.current_firmware = cur_firmware  # if cur_firmware is none its unknown
    session.commit()

    pending_update = car.pending_update

    if pending_update is None:
        return False

    newer_version = pending_update.target_firmware.version
    return fm_version != newer_version


@router.get("/latest")
def get_latest_firmware_file(session: SessionDep, fm_version: str | None = None, car: VehicleDB = Depends(auth_vehicle)):

    if fm_version is not None:
        cur_firmware = session.exec(select(FirmwareDB).where(FirmwareDB.version == fm_version)).first()
        car.current_firmware = cur_firmware  # if cur_firmware is none its unknown
        session.commit()

    pending_update = car.pending_update
    if pending_update is None:
        raise no_firmware_available_exception

    if fm_version is not None and pending_update.target_firmware.version == fm_version:
        raise no_firmware_available_exception

    pending_update.update_last_downloaded = datetime.now(tz=timezone.utc)
    session.commit()

    return Response(status_code=200, content=pending_update.target_firmware.firmware, media_type="application/octet-stream")


@router.get("/latest/size")
def get_latest_firmware_size(car: VehicleDB = Depends(auth_vehicle)) -> int:
    pending_update = car.pending_update
    if pending_update is None:
        raise no_firmware_available_exception
    return len(pending_update.target_firmware.firmware)
