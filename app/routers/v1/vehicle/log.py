import logging
from collections import Counter
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, Response, HTTPException

from app import database
from app.auth import auth_device
from app.helpers.log_parser import parse_log
from app.models.badlog import BadLogDB
from app.models.device import DeviceDB
from app.models.log import LogEntryDB

log = logging.getLogger("app.devicelog")

router = APIRouter(prefix="/log", tags=["Logs"])


@router.post("/upload")
async def upload_log(session: database.SessionDep, request: Request, device: DeviceDB = Depends(auth_device)):
    upload_time = datetime.now(timezone.utc)
    file = await request.body()  # read raw bytes from body
    raw_log = file.decode()
    try:
        parsed_entries = parse_log(raw_log)
    except Exception as ve:
        bad = BadLogDB(text=raw_log, upload_timestamp=upload_time, imei=device.imei)
        session.add(bad)
        session.commit()
        # The device gets a 200 and deletes its copy, so this is the only notice
        # that the parser could not handle what it sent.
        log.error("Could not parse the %d B log from %s (%s). Stored as badlogdb #%s",
                  len(file), device.imei, ve, bad.id,
                  extra={"imei": device.imei, "bytes": len(file),
                         "badlog_id": bad.id, "error": str(ve)})
        # Return success because we saved the log and the device can delete its log
        raise HTTPException(200, "Malformed log")

    log_db: list[LogEntryDB] = [LogEntryDB.from_dataclass(pe, device.imei, upload_time) for pe in parsed_entries]

    # Counted before committing: commit expires every instance, so reading
    # e.level afterwards would issue a SELECT per entry.
    levels = Counter(getattr(e.level, "value", str(e.level)) for e in log_db)

    session.add_all(log_db)
    session.commit()

    log.info("Stored %d log entries from %s (%d B) %s",
             len(log_db), device.imei, len(file), dict(levels),
             extra={"imei": device.imei, "entries": len(log_db), "bytes": len(file),
                    "levels": {k: v for k, v in levels.items()}})

    # A device reporting its own errors is worth surfacing without having to
    # query the log table.
    serious = levels.get("ERROR", 0) + levels.get("CRITICAL", 0)
    if serious:
        log.warning("Device %s reported %d error/critical line(s) in this batch",
                    device.imei, serious,
                    extra={"imei": device.imei, "serious_lines": serious})

    return Response(status_code=200)
