from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from app import tasks
from app.database import create_db_and_tables, insert_default_admin
from app.routers import v1

app = FastAPI(default_response_class=ORJSONResponse)


@app.on_event("startup")
async def startup_event():
    create_db_and_tables()
    insert_default_admin()
    tasks.start_background_user_data_cleanup_task()

@app.on_event("shutdown")
async def shutdown_event():
    tasks.stop_background_user_data_cleanup_task()

app.include_router(v1.router)
