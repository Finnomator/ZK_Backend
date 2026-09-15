from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from sqlmodel import select

from app.database import SessionDep
from app.models.badgpslog import BadGpsLogDB

router = APIRouter(prefix="/badgpslog")

@router.get("/download")
async def download_badgpslog(id: int, session: SessionDep):
    bad_log: BadGpsLogDB = session.exec(select(BadGpsLogDB).where(BadGpsLogDB.id == id)).first()

    if not bad_log:
        raise HTTPException(status_code=404, detail="Log not found")

    return Response(
        content=bad_log.raw_data,
        media_type="application/octet-stream"
    )
