from fastapi import APIRouter, Depends, HTTPException, Response

from app.auth import auth_admin
from app.database import SessionDep
from app.internal.helper import hash_password
from app.models.admin import AdminCreate, AdminDB
from . import firmware

router = APIRouter(prefix="/admin", tags=["Admin"],
                   dependencies=[Depends(auth_admin)])

router.include_router(firmware.router)


@router.post("/add-admin")
def add_admin(admin: AdminCreate, session: SessionDep):
    if len(admin.password) < 15:
        raise HTTPException(400, "Password should be at least 15 characters long")

    if session.get(AdminDB, admin.username) is not None:
        raise HTTPException(400, "User already exists")

    pwd_hash = hash_password(admin.password)

    db_admin = AdminDB(username=admin.username, password_hash=pwd_hash)

    session.add(db_admin)
    session.commit()

    return Response(status_code=200)
