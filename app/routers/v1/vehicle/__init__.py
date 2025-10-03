from fastapi import APIRouter, Depends

from app.auth import auth_vehicle
from . import gps_tracking, log, rfids, other, firmware

router = APIRouter(prefix="/vehicle", tags=["Vehicle"], dependencies=[Depends(auth_vehicle)])

router.include_router(rfids.router)
router.include_router(log.router)
router.include_router(gps_tracking.router)
router.include_router(other.router)
router.include_router(firmware.router)
