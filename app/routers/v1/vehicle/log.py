import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, Response, HTTPException

from app import database
from app.auth import auth_vehicle
from app.helpers.log_parser import parse_log
from app.internal.paths import UPLOAD_DATA_DIR
from app.models.vehicle import VehicleDB

router = APIRouter(prefix="/log", tags=["Logs"])


@router.post("/upload")
async def upload_log(session: database.SessionDep, request: Request, car: VehicleDB = Depends(auth_vehicle)):
    upload_time = datetime.now(timezone.utc)
    file = await request.body()  # read raw bytes from body
    try:
        parsed_entries = parse_log(file.decode(), car.imei, upload_time)
    except (ValueError, OSError) as ve:
        file_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.badlog"
        file_parent_dir = UPLOAD_DATA_DIR / "malformed-logs"
        file_path = file_parent_dir / file_name
        os.makedirs(file_parent_dir, exist_ok=True)
        with open(file_path, "w") as f:
            f.write(file)
        print(f"Failed to parse log: {ve}. Saved to {file_path}")
        raise HTTPException(400, "Malformed log")

    session.add_all(parsed_entries)
    session.commit()
    print("Added", len(parsed_entries), "log entries")
    return Response(status_code=200)
