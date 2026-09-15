import io
import struct
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlmodel import select, Session

from app import database
from app.auth import auth_device, DeviceDB
from app.database import SessionDep
from app.internal.helper import rfid_uids_to_little_endian_bytes
from app.models.badgpslog import BadGpsLogDB
from app.models.gps_entry import GpsEntryDB
from app.models.rfid import GpsTrackingConsentRfidUidDB
from app.models.badgpslog import BadGpsLogDB

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
        raise HTTPException(400, "Body is empty")

    try:
        parsed_gps_entries = parse_raw_gps(io.BytesIO(body), device.imei)
    except Exception as e:
        session.add(BadGpsLogDB(raw_data=body, imei=device.imei, upload_timestamp=upload_time))
        session.commit()
        print(f'Failed to prase GPS log: {e}. Saved to db')
        raise HTTPException(200, "Malformed log") # Prevent device from uploading logs unnecessarily

    session.add_all(parsed_gps_entries)
    session.commit()

    return {
        "Added": len(parsed_gps_entries)
    }


@router.get("/rfids/download", tags=["RFIDs"])
def download_gprs_tracking_consented_rfids(session: database.SessionDep):
    gps_rfid_uids: list[int] = session.exec(select(GpsTrackingConsentRfidUidDB.rfid_uid)).all()
    bin_rfid_uids = rfid_uids_to_little_endian_bytes(gps_rfid_uids)
    return Response(status_code=200, content=bin_rfid_uids, media_type="application/octet-stream")
