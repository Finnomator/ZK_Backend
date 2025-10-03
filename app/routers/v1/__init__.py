from fastapi import APIRouter

from . import vehicle, admin

router = APIRouter(prefix="/v1")
router.include_router(vehicle.router)
router.include_router(admin.router)
