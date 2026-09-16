import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from sqlmodel import select

from app.database import SessionDep
from app.models.badgpslog import BadGpsLogDB

log = logging.getLogger("app.admin.badgpslog")

router = APIRouter(prefix="/badgpslog")

@router.get("/download")
async def download_badgpslog(id: int, session: SessionDep):
    bad_log: BadGpsLogDB = session.exec(select(BadGpsLogDB).where(BadGpsLogDB.id == id)).first()

    if not bad_log:
        log.warning("Download requested for unknown badgpslog #%s", id, extra={"badgpslog_id": id})
        raise HTTPException(status_code=404, detail="Log not found")

    log.info("Admin downloaded badgpslog #%s from %s (%d B)",
             id, bad_log.imei, len(bad_log.raw_data),
             extra={"badgpslog_id": id, "imei": bad_log.imei, "bytes": len(bad_log.raw_data)})

    return Response(
        content=bad_log.raw_data,
        media_type="application/octet-stream"
    )
