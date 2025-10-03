from fastapi import APIRouter, Request, HTTPException, Response

from app.database import SessionDep
from app.models.firmware import FirmwareDB

router = APIRouter(prefix="/firmware")


@router.post("/upload-new")
async def upload_new_firmware(version_major: int, version_minor: int, version_patch: int, request: Request,
                              session: SessionDep):
    request_body = await request.body()

    if len(request_body) == 0:
        raise HTTPException(400, "Firmware is empty")

    if session.get(FirmwareDB, (version_major, version_minor, version_patch)) is not None:
        raise HTTPException(400, "Firmware already exists")

    db_firmware = FirmwareDB(major=version_major, minor=version_minor, patch=version_patch, file=request_body)

    session.add(db_firmware)
    session.commit()

    return Response(status_code=200)
