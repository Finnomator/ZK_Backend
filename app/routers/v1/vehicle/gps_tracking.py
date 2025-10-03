import io
import os
import struct
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlmodel import select

from app import database
from app.auth import auth_vehicle, VehicleDB
from app.database import SessionDep
from app.internal.helper import rfid_uids_to_little_endian_bytes
from app.internal.uploaded_data import make_uploaded_data_path
from app.models.gps_entry import GpsEntryDB
from app.models.rfid import GpsTrackingConsentRfidUidDB

router = APIRouter(prefix="/gps-tracking", tags=["GPS Tracking"])


def parse_raw_gps(raw_data: io.BytesIO, chip_id: int) -> list[GpsEntryDB]:
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
                       timestamp=dt_utc, chip_id=chip_id))

    return db_entries


def make_gps_path(prefix: str, mac: int, upload_time: datetime):
    return make_uploaded_data_path(prefix, mac, upload_time, ".gpslog")


def save_malformed_gps_file(mac: int, content: bytes, upload_time: datetime) -> Path:
    gps_path = make_gps_path("malformed-gps", mac, upload_time)
    os.makedirs(gps_path.parent, exist_ok=True)

    if os.path.exists(gps_path):
        raise HTTPException(500, "File already exists")

    with open(gps_path, "wb") as f:
        f.write(content)

    return gps_path


@router.post("/log/upload")
async def upload_gps(request: Request, session: SessionDep,
                     car: VehicleDB = Depends(auth_vehicle)):
    upload_time = datetime.now()

    body = await request.body()

    if not body:
        raise HTTPException(400, "Body is empty")

    try:
        parsed_gps_entries = parse_raw_gps(io.BytesIO(body), car.chip_id)
    except:
        print("Failed to parse GPS data")
        saved_to_path = save_malformed_gps_file(car.chip_id, body, upload_time)
        print(f"Saved to {'/'.join(saved_to_path.parts)}")
        raise HTTPException(400, "Malformed log")

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
