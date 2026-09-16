import logging

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse, Response

# Before anything else imports a logger, so module-level loggers pick up the
# configured handlers rather than the root default.
from app.internal.logging_config import setup_logging

setup_logging()

from app import tasks
from app.database import create_db_and_tables, insert_default_admin
from app.middleware import RequestLogMiddleware
from app.routers import v1

log = logging.getLogger("app.startup")

app = FastAPI(default_response_class=ORJSONResponse)
app.add_middleware(RequestLogMiddleware)


@app.on_event("startup")
async def startup_event():
    log.info("Starting up")
    try:
        create_db_and_tables()
        insert_default_admin()
        tasks.start_background_user_data_cleanup_task()
        tasks.start_vehicle_location_gathering()
    except Exception:
        log.critical("Startup failed", exc_info=True)
        raise
    log.info("Startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    log.info("Shutting down")
    tasks.stop_background_user_data_cleanup_task()
    tasks.stop_vehicle_location_gathering()
    log.info("Shutdown complete")


@app.get("/ping")
async def ping():
    return Response(status_code=204)

app.include_router(v1.router)
