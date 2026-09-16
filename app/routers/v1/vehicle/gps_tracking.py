import io
import logging
import struct
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlmodel import select

from app import database
from app.auth import auth_device, DeviceDB
from app.database import SessionDep
from app.internal.helper import rfid_uids_to_little_endian_bytes
from app.models.badgpslog import BadGpsLogDB
from app.models.gps_entry import GpsEntryDB
from app.models.rfid import GpsTrackingConsentRfidUidDB

log = logging.getLogger("app.gps")

router = APIRouter(prefix="/gps-tracking", tags=["GPS Tracking"])


def parse_raw_gps(raw_data: io.BytesIO, imei: str) -> list[GpsEntryDB]:
    fmt = '<ffffBBfQ'

    struct_size = struct.calcsize(fmt)

    db_entries: list[GpsEntryDB] = []

    while True:
        chunk = raw_data.read(struct_size)

        if not chunk:
            break

        (lat, lon, speed, alt, vsat, usat, accuracy, unix_timestamp) = struct.unpack(fmt, chunk)

        dt_utc = datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)

        db_entries.append(
            GpsEntryDB(latitude=lat, longitude=lon, speed=speed, altitude=alt, vsat=vsat, usat=usat, accuracy=accuracy,
                       timestamp=dt_utc, imei=imei))

    return db_entries


@router.post("/log/upload")
async def upload_gps(request: Request, session: SessionDep, device: DeviceDB = Depends(auth_device)):
    upload_time = datetime.now()

    body = await request.body()

    if not body:
        log.warning("Device %s uploaded an empty GPS log", device.imei,
                    extra={"imei": device.imei})
        raise HTTPException(400, "Body is empty")

    if len(body) % struct.calcsize('<ffffBBfQ'):
        # Not fatal on its own, but it means the body is not a whole number of
        # records, which is the signature of a damaged upload.
        log.warning("GPS log from %s is %d B, not a multiple of the %d B record size",
                    device.imei, len(body), struct.calcsize('<ffffBBfQ'),
                    extra={"imei": device.imei, "bytes": len(body)})

    try:
        parsed_gps_entries = parse_raw_gps(io.BytesIO(body), device.imei)
    except Exception as e:
        bad = BadGpsLogDB(raw_data=body, imei=device.imei, upload_timestamp=upload_time)
        session.add(bad)
        session.commit()
        # The device is told 200 so it stops retrying, so this line is the only
        # signal that a device just lost a log. See repair_bad_gps_logs.py.
        log.error("Could not parse the %d B GPS log from %s (%s). Stored as badgpslogdb #%s",
                  len(body), device.imei, e, bad.id,
                  extra={"imei": device.imei, "bytes": len(body),
                         "badgpslog_id": bad.id, "error": str(e)})
        raise HTTPException(200, "Malformed log") # Prevent device from uploading logs unnecessarily

    # Read before committing: commit expires every instance, so touching them
    # afterwards would issue a SELECT per row.
    span = ((parsed_gps_entries[0].timestamp, parsed_gps_entries[-1].timestamp)
            if parsed_gps_entries else None)

    session.add_all(parsed_gps_entries)
    session.commit()

    if span:
        log.info("Stored %d GPS entries from %s (%d B, %s to %s)",
                 len(parsed_gps_entries), device.imei, len(body),
                 span[0].isoformat(), span[1].isoformat(),
                 extra={"imei": device.imei, "entries": len(parsed_gps_entries),
                        "bytes": len(body)})
    else:
        log.info("GPS upload from %s contained no entries", device.imei,
                 extra={"imei": device.imei, "bytes": len(body)})

    return {
        "Added": len(parsed_gps_entries)
    }


@router.get("/rfids/download", tags=["RFIDs"])
def download_gprs_tracking_consented_rfids(session: database.SessionDep):
    gps_rfid_uids: list[int] = session.exec(select(GpsTrackingConsentRfidUidDB.rfid_uid)).all()
    bin_rfid_uids = rfid_uids_to_little_endian_bytes(gps_rfid_uids)
    return Response(status_code=200, content=bin_rfid_uids, media_type="application/octet-stream")
