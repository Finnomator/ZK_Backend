from fastapi import APIRouter, Response
from fastapi import HTTPException
from packaging.version import Version
from sqlmodel import Session, select, desc

from app import database
from app.models.firmware import FirmwareDB

router = APIRouter(prefix="/firmware", tags=["Firmware"])

no_firmware_available_exception = HTTPException(500, "No firmware available")


def get_latest_firmware() -> FirmwareDB | None:
    stmt = select(FirmwareDB).order_by(
        desc(FirmwareDB.major),
        desc(FirmwareDB.minor),
        desc(FirmwareDB.patch)
    ).limit(1)

    with Session(database.engine) as session:
        return session.exec(stmt).first()


def get_latest_firmware_version() -> Version | None:
    return Version(get_latest_firmware_version_str())


def get_latest_firmware_version_str() -> str | None:
    latest_firmware = get_latest_firmware()
    if latest_firmware is None:
        raise no_firmware_available_exception
    return f"{latest_firmware.major}.{latest_firmware.minor}.{latest_firmware.patch}"


@router.get("/is-newer-available")
def is_newer_firmware_available(fm_version: str):
    try:
        parsed_fm_ver = Version(fm_version)
    except ValueError:
        raise HTTPException(422, "Invalid version format")

    return get_latest_firmware_version() > parsed_fm_ver


@router.get("/latest")
def get_latest_firmware_file():
    print("HERE 1")
    latest_firmware = get_latest_firmware()
    if latest_firmware is None:
        raise no_firmware_available_exception
    return Response(status_code=200, content=latest_firmware.file, media_type="application/octet-stream")


@router.get("/latest/size")
def get_latest_firmware_size() -> int:
    latest_firmware = get_latest_firmware()
    if latest_firmware is None:
        raise no_firmware_available_exception
    return len(latest_firmware.file)
