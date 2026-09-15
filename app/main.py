from fastapi import FastAPI
from fastapi.responses import ORJSONResponse, Response

from app import tasks
from app.database import create_db_and_tables, insert_default_admin
from app.routers import v1

app = FastAPI(default_response_class=ORJSONResponse)


@app.on_event("startup")
async def startup_event():
    create_db_and_tables()
    insert_default_admin()
    tasks.start_background_user_data_cleanup_task()
    tasks.start_vehicle_location_gathering()

@app.on_event("shutdown")
async def shutdown_event():
    tasks.stop_background_user_data_cleanup_task()
    tasks.stop_vehicle_location_gathering()

@app.get("/ping")
async def ping():
    return Response(status_code=204)

app.include_router(v1.router)
