import logging

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlmodel import Session

from app import database
from app.internal import config
from app.internal.helper import check_password
from app.models.admin import AdminDB
from app.models.device import DeviceDB

log = logging.getLogger("app.auth")

security = HTTPBasic()

invalid_username_or_pwd_exception = HTTPException(
    status_code=401,
    detail="Invalid username or password",
    headers={"WWW-Authenticate": "Basic"},
)


def get_device(imei: str, session: Session) -> DeviceDB | None:
    return session.get(DeviceDB, imei)


def get_admin(username: str, session: Session) -> AdminDB | None:
    return session.get(AdminDB, username)


def ensure_secure_connection(request: Request):
    """
    This does not prevent the client from sending data over http!!!
    """

    proto = request.headers.get("x-forwarded-proto")
    port = request.headers.get("x-forwarded-port")

    if proto != "https":
        log.warning("Rejected an insecure request to %s (proto=%s, port=%s)",
                    request.url.path, proto, port,
                    extra={"proto": proto, "port": port, "path": request.url.path})
        raise HTTPException(
            status_code=400,
            detail=f"Insecure connection (proto={proto}, port={port})"
        )


def auth_device(session: database.SessionDep, credentials: HTTPBasicCredentials = Depends(security)) -> DeviceDB:
    device = get_device(credentials.username, session)

    # Unknown IMEI and wrong shared password are different problems: the first
    # is usually a device that was never registered, the second means a device
    # is running a build with a stale password, or someone is guessing.
    if device is None:
        log.warning("Rejected unknown device %r", credentials.username,
                    extra={"imei": credentials.username, "reason": "unknown_device"})
        raise invalid_username_or_pwd_exception

    if credentials.password != config.DEVICE_PASSWORD:
        log.warning("Rejected device %s: wrong password", credentials.username,
                    extra={"imei": credentials.username, "reason": "bad_password"})
        raise invalid_username_or_pwd_exception

    log.debug("Device %s authenticated", device.imei, extra={"imei": device.imei})
    return device


def auth_admin(session: database.SessionDep, credentials: HTTPBasicCredentials = Depends(security)) -> AdminDB:
    admin = get_admin(credentials.username, session)

    if admin is None:
        log.warning("Rejected unknown admin %r", credentials.username,
                    extra={"username": credentials.username, "reason": "unknown_admin"})
        raise invalid_username_or_pwd_exception

    if not check_password(credentials.password, admin.password_hash):
        log.warning("Rejected admin %s: wrong password", credentials.username,
                    extra={"username": credentials.username, "reason": "bad_password"})
        raise invalid_username_or_pwd_exception

    log.info("Admin %s authenticated", admin.username, extra={"username": admin.username})
    return admin
