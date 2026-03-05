from fastapi import APIRouter

from . import device, admin

router = APIRouter(prefix="/v1")
router.include_router(device.router)
router.include_router(admin.router)
