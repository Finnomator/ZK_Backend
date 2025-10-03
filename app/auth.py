from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlmodel import Session

from app import database
from app.internal import config
from app.internal.helper import check_password
from app.models.admin import AdminDB
from app.models.vehicle import VehicleDB

security = HTTPBasic()

invalid_username_or_pwd_exception = HTTPException(
    status_code=401,
    detail="Invalid username or password",
    headers={"WWW-Authenticate": "Basic"},
)


def get_car(chip_id: int, session: Session) -> VehicleDB | None:
    return session.get(VehicleDB, chip_id)


def get_admin(username: str, session: Session) -> AdminDB | None:
    return session.get(AdminDB, username)


def ensure_secure_connection(request: Request):
    """
    This does not prevent the client from sending data over http!!!
    """

    proto = request.headers.get("x-forwarded-proto")
    port = request.headers.get("x-forwarded-port")

    if proto != "https":
        raise HTTPException(
            status_code=400,
            detail=f"Insecure connection (proto={proto}, port={port})"
        )


def auth_vehicle(session: database.SessionDep, credentials: HTTPBasicCredentials = Depends(security)) -> VehicleDB:
    try:
        chip_id_int = int(credentials.username, 16)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="Invalid chip ID format",
        )

    car = get_car(chip_id_int, session)

    if car is None:
        raise invalid_username_or_pwd_exception

    if credentials.password != config.VEHICLE_PASSWORD:
        raise invalid_username_or_pwd_exception

    return car


def auth_admin(session: database.SessionDep, credentials: HTTPBasicCredentials = Depends(security)) -> AdminDB:
    admin = get_admin(credentials.username, session)

    if admin is None:
        raise invalid_username_or_pwd_exception

    if not check_password(credentials.password, admin.password_hash):
        raise invalid_username_or_pwd_exception

    return admin
