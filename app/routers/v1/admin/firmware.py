from datetime import datetime, timezone

from fastapi import APIRouter, Request, HTTPException, Response
from sqlmodel import select

from app.database import SessionDep
from app.models.firmware import FirmwareDB, FirmwarePublic
from app.models.firmware_update import FirmwareUpdateDB, FirmwareUpdatePublic
from app.models.vehicle import VehicleDB

router = APIRouter(prefix="/firmware")


@router.get("/download")
async def download_fw(version: str, session: SessionDep):
    fw_db = session.exec(select(FirmwareDB).where(FirmwareDB.version == version)).first()

    if not fw_db:
        raise HTTPException(status_code=404, detail="Firmware not found")

    return Response(
        content=fw_db.file,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{fw_db.version}.bin"'}
    )


@router.post("/upload-new", response_model=FirmwarePublic)
async def upload_new_firmware(version: str, request: Request, session: SessionDep):
    request_body = await request.body()

    if len(request_body) == 0:
        raise HTTPException(400, "Firmware is empty")

    if session.exec(select(FirmwareDB).where(FirmwareDB.version == version)).first() is not None:
        raise HTTPException(400, "Firmware already exists")

    db_firmware = FirmwareDB(version=version, file=request_body)

    session.add(db_firmware)
    session.commit()

    return db_firmware


@router.post("/issue-new", response_model=FirmwareUpdatePublic)
async def issue_new_firmware_to_vehicle(vehicle_imei: str, firmware_version: str, session: SessionDep):
    # check vehicle exists
    vehicle = session.get(VehicleDB, vehicle_imei)
    if not vehicle:
        raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_imei} not found")

    # check firmware exists
    firmware = session.get(FirmwareDB, firmware_version)
    if not firmware:
        raise HTTPException(status_code=404, detail=f"Firmware {firmware_version} not found")

    # check for existing pending update
    existing_update = session.exec(
        select(FirmwareUpdateDB).where(FirmwareUpdateDB.target_vehicle_imei == vehicle_imei)
    ).first()

    if existing_update is not None:

        if existing_update.target_firmware_version == firmware.version:
            raise HTTPException(status_code=200,
                                detail="Update has already been issued at " + existing_update.update_issued_at.isoformat())

        # just override the existing record
        existing_update.target_firmware_version = firmware.version
        existing_update.update_issued_at = datetime.now(tz=timezone.utc)
        existing_update.update_last_downloaded = None
        fw_update = existing_update
    else:
        # create a new one if none exists
        fw_update = FirmwareUpdateDB(
            target_vehicle_imei=vehicle.imei,
            target_firmware_version=firmware.version
        )
        session.add(fw_update)

    session.commit()
    session.refresh(fw_update)

    return fw_update


@router.get("/all", response_model=list[FirmwarePublic])
async def get_all_available_firmwares(session: SessionDep):
    return session.exec(select(FirmwareDB)).all()
