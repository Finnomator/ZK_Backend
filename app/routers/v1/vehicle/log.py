import io
import os.path
import struct
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app import database
from app.auth import auth_vehicle
from app.internal.paths import UPLOAD_DATA_DIR
from app.models.log import LogEntryDB, int_to_logging_level, LoggingLevel
from app.models.vehicle import VehicleDB

router = APIRouter(prefix="/log", tags=["Logs"])


def read_bin(fmt: str, stream: io.BytesIO) -> tuple | None:
    size = struct.calcsize(fmt)
    data = stream.read(size)
    return struct.unpack(fmt, data) if data else None


def read_log_entry(stream: io.BytesIO) -> tuple[datetime, LoggingLevel, str] | None:
    packed = read_bin("<QB", stream)

    if packed is None:
        return None

    timestamp_ms, level = packed

    dt_utc = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)

    packed = read_bin("<H", stream)

    if packed is None:
        return None

    msg_length = packed[0]

    msg = stream.read(msg_length).decode("utf-8", errors="replace")

    return dt_utc, int_to_logging_level(level), msg


def parse_log(raw_log: io.BytesIO, chip_id: int) -> list[LogEntryDB]:
    entries: list[LogEntryDB] = []

    try:
        while True:
            parsed_log_entry = read_log_entry(raw_log)

            if parsed_log_entry is None:
                break

            dt_utc, level, msg = parsed_log_entry

            if dt_utc.year >= 2025 and "Time:" in msg:
                calib_millis = int(msg.split("millis: ")[1].split(" ")[0])
                index = len(entries)

                # Set timestamps of entries that have millis timestamp
                for i in range(index - 1, -1, -1):
                    entry = entries[i]
                    if entry.timestamp.year >= 2025:
                        break
                    delta = calib_millis - entry.timestamp.timestamp() * 1000.0
                    entry.timestamp = dt_utc - timedelta(milliseconds=delta)

            entries.append(LogEntryDB(timestamp=dt_utc, level=level, message=msg, chip_id=chip_id))

    except (ValueError, OSError) as ve:
        file_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.badlog"
        file_parent_dir = UPLOAD_DATA_DIR / "malformed-logs"
        file_path = file_parent_dir / file_name
        os.makedirs(file_parent_dir, exist_ok=True)
        raw_log.seek(0)
        with open(file_path, "wb") as f:
            f.write(raw_log.getvalue())
        print(f"Failed to parse log: {ve}. Saved to {file_path}")
        raise HTTPException(400, "Malformed log")

    return entries


@router.post("/upload")
async def upload_log(session: database.SessionDep, request: Request, car: VehicleDB = Depends(auth_vehicle)):
    file = await request.body()  # read raw bytes from body
    stream = io.BytesIO(file)
    parsed_entries = parse_log(stream, car.chip_id)
    session.add_all(parsed_entries)
    session.commit()
    print("Added", len(parsed_entries), "log entries")
    return Response(status_code=200)
