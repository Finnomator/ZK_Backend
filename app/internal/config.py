import os
from urllib.parse import quote_plus

from app.internal.helper import hash_password

DB_USER = os.getenv("POSTGRES_USER")
DB_PASS = os.getenv("POSTGRES_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB")

VEHICLE_PASSWORD = os.getenv("VEHICLE_PASSWORD")
DEFAULT_ADMIN_NAME = os.getenv("DEFAULT_ADMIN_NAME")
DEFAULT_ADMIN_HASH = hash_password(os.getenv("DEFAULT_ADMIN_PWD"))

encoded_db_password = quote_plus(DB_PASS)

DATABASE_URL = f"postgresql://{DB_USER}:{encoded_db_password}@db:5432/{DB_NAME}"
