import hashlib
import logging
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, Response
from fastapi import HTTPException
from sqlalchemy import func
from sqlmodel import select

from app.auth import auth_device
from app.database import SessionDep
from app.models.device import DeviceDB
from app.models.firmware import FirmwareDB

log = logging.getLogger("app.firmware")

router = APIRouter(prefix="/firmware", tags=["Firmware"])

no_firmware_available_exception = HTTPException(204, "No firmware available")

@router.get("/is-newer-available")
def is_newer_firmware_available(fm_version: str, session: SessionDep, device: DeviceDB = Depends(auth_device)):
    cur_firmware = session.exec(select(FirmwareDB).where(FirmwareDB.version == fm_version)).first()

    device.current_firmware = cur_firmware  # if cur_firmware is none its unknown
    session.commit()

    pending_update = device.pending_update

    if pending_update is None:
        return False

    newer_version = pending_update.target_firmware.version
    available = fm_version != newer_version

    # A device asking repeatedly while already on the target is how the
    # download loop looked; worth seeing without turning on debug.
    log.debug("Device %s on %s: update to %s %s", device.imei, fm_version, newer_version,
              "available" if available else "already applied",
              extra={"imei": device.imei, "current": fm_version,
                     "target": newer_version, "available": available})
    return available


# "bytes=0-32767" or open-ended "bytes=32768-". Multi-range is deliberately
# unsupported: the firmware never asks for one, and a 206 carrying a multipart
# body would be silently written to flash as if it were firmware.
_RANGE_RE = re.compile(r"^bytes=(\d+)-(\d*)$")


def _firmware_meta(session: SessionDep, version: str) -> tuple[int, str]:
    """Total size and MD5 of the whole image, computed in the database.

    Every chunk request needs both, and pulling the blob out of Postgres just to
    measure it would move the entire firmware per chunk.
    """
    # execute() rather than exec(): exec() unwraps single-column selects to
    # scalars and leaves multi-column ones as rows, so indexing explicitly keeps
    # both helpers reading the same way.
    row = session.execute(
        select(func.octet_length(FirmwareDB.firmware), func.md5(FirmwareDB.firmware))
        .where(FirmwareDB.version == version)
    ).first()
    return row[0], row[1]


def _firmware_slice(session: SessionDep, version: str, start: int, length: int) -> bytes:
    # substr() is 1-indexed. func.substr() carries no result processor, so
    # psycopg hands back a memoryview; bytes() keeps callers (and hashlib) on
    # one concrete type.
    return bytes(session.execute(
        select(func.substr(FirmwareDB.firmware, start + 1, length))
        .where(FirmwareDB.version == version)
    ).first()[0])


@router.get("/latest")
def get_latest_firmware_file(
    request: Request,
    session: SessionDep,
    fm_version: str | None = None,
    device: DeviceDB = Depends(auth_device),
):
    """Serves the pending firmware, whole or by byte range.

    A device on a cellular link cannot reliably hold one connection open for the
    ~100s a full image takes, so it asks for ~32 KiB at a time and resumes from
    what it has already committed. Without a Range header the whole image is
    returned as before, so older firmware keeps updating normally.
    """
    range_header = request.headers.get("range")

    if range_header is None:
        rng = None
    else:
        match = _RANGE_RE.match(range_header.strip())
        if match is None:
            log.warning("Device %s sent an unsupported Range %r", device.imei, range_header,
                        extra={"imei": device.imei, "range": range_header})
            raise HTTPException(416, f"Unsupported Range: {range_header}")
        rng = (int(match.group(1)), int(match.group(2)) if match.group(2) else None)

    # Only the opening request reports progress. Committing per chunk would turn
    # one update into a write per chunk per device.
    is_first = rng is None or rng[0] == 0

    if fm_version is not None and is_first:
        cur_firmware = session.exec(
            select(FirmwareDB).where(FirmwareDB.version == fm_version)
        ).first()
        device.current_firmware = cur_firmware  # if cur_firmware is none its unknown
        session.commit()

    pending_update = device.pending_update
    if pending_update is None:
        raise no_firmware_available_exception

    if fm_version is not None and pending_update.target_firmware.version == fm_version:
        raise no_firmware_available_exception

    if not any(device.hw_revision_number == hw.revision_number for hw in pending_update.target_firmware.compatible_hardware):
        # An operator mistake that silently leaves the device un-updatable
        # forever, because the device is told there is nothing for it.
        log.error("Device %s (hw rev %s) has firmware %s issued, which is not compatible with its hardware",
                  device.imei, device.hw_revision, pending_update.target_firmware.version,
                  extra={"imei": device.imei, "hw_revision": str(device.hw_revision),
                         "firmware": pending_update.target_firmware.version})
        raise no_firmware_available_exception

    if is_first:
        pending_update.update_last_downloaded = datetime.now(tz=timezone.utc)
        session.commit()

    version = pending_update.target_firmware.version
    total, full_md5 = _firmware_meta(session, version)

    # The MD5 always covers the whole image, never the chunk: the device feeds
    # every chunk into one running digest and verifies it once at the end.
    headers = {"x-MD5": full_md5, "Accept-Ranges": "bytes"}

    if rng is None:
        # Firmware predating the chunked downloader. One connection has to
        # survive the whole image, which is what the range support exists to avoid.
        log.info("Serving the whole %d B image of %s to %s (no Range requested)",
                 total, version, device.imei,
                 extra={"imei": device.imei, "firmware": version, "bytes": total,
                        "ranged": False})
        return Response(
            status_code=200,
            content=_firmware_slice(session, version, 0, total),
            media_type="application/octet-stream",
            headers=headers,
        )

    start, end = rng
    if start >= total:
        log.warning("Device %s asked for byte %d of a %d B image of %s",
                    device.imei, start, total, version,
                    extra={"imei": device.imei, "firmware": version,
                           "start": start, "total": total})
        raise HTTPException(416, "Range starts past the end of the firmware",
                            headers={"Content-Range": f"bytes */{total}"})

    end = total - 1 if end is None else min(end, total - 1)
    if end < start:
        log.warning("Device %s asked for the empty range %d-%d of %s",
                    device.imei, start, end, version,
                    extra={"imei": device.imei, "firmware": version,
                           "start": start, "end": end})
        raise HTTPException(416, f"Range {start}-{end} is empty",
                            headers={"Content-Range": f"bytes */{total}"})

    chunk = _firmware_slice(session, version, start, end - start + 1)

    headers["Content-Range"] = f"bytes {start}-{end}/{total}"
    # Lets the device check each chunk on arrival and re-fetch just that range,
    # instead of only finding out at the end that the whole image is bad.
    headers["x-Chunk-MD5"] = hashlib.md5(chunk).hexdigest()

    # The opening and closing chunks bracket a download in the log; the ones in
    # between are only interesting when chasing a specific device.
    boundary = start == 0 or end == total - 1
    log.log(logging.INFO if boundary else logging.DEBUG,
            "Served %s bytes %d-%d/%d to %s", version, start, end, total, device.imei,
            extra={"imei": device.imei, "firmware": version, "start": start,
                   "end": end, "total": total, "ranged": True})

    return Response(
        status_code=206,
        content=chunk,
        media_type="application/octet-stream",
        headers=headers,
    )


@router.get("/latest/size")
def get_latest_firmware_size(device: DeviceDB = Depends(auth_device)) -> int:
    pending_update = device.pending_update
    if pending_update is None:
        raise no_firmware_available_exception
    return len(pending_update.target_firmware.firmware)
