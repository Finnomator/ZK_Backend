import os

from app.internal.helper import hash_password

DB_USER = os.getenv("POSTGRES_USER")
DB_PASS = os.getenv("POSTGRES_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB")

VEHICLE_PASSWORD = os.getenv("VEHICLE_PASSWORD")
DEFAULT_ADMIN_NAME = os.getenv("DEFAULT_ADMIN_NAME")
DEFAULT_ADMIN_HASH = hash_password(os.getenv("DEFAULT_ADMIN_PWD"))

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@db:5432/{DB_NAME}"
