import logging

from fastapi import APIRouter, Depends, HTTPException, Response

from app.auth import auth_admin
from app.database import SessionDep
from app.internal.helper import hash_password
from app.models.admin import AdminCreate, AdminDB
from . import firmware, badgpslog

log = logging.getLogger("app.admin")

router = APIRouter(prefix="/admin", tags=["Admin"],
                   dependencies=[Depends(auth_admin)])

router.include_router(firmware.router)
router.include_router(badgpslog.router)


@router.post("/add-admin")
def add_admin(admin: AdminCreate, session: SessionDep):
    if len(admin.password) < 15:
        log.warning("Refused to create admin %r: password too short", admin.username,
                    extra={"username": admin.username, "reason": "weak_password"})
        raise HTTPException(400, "Password should be at least 15 characters long")

    if session.get(AdminDB, admin.username) is not None:
        log.warning("Refused to create admin %r: already exists", admin.username,
                    extra={"username": admin.username, "reason": "exists"})
        raise HTTPException(400, "User already exists")

    pwd_hash = hash_password(admin.password)

    db_admin = AdminDB(username=admin.username, password_hash=pwd_hash)

    session.add(db_admin)
    session.commit()

    # Who did this is on the "Admin ... authenticated" line sharing this
    # request id.
    log.info("Created admin account %r", admin.username, extra={"username": admin.username})

    return Response(status_code=200)
