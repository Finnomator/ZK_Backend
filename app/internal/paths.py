from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.resolve()

V1_STATIC_DIR = BASE_DIR / "routers/v1/public/static"
UPLOAD_DATA_DIR = BASE_DIR / "uploaded_data"

TEST_FILES_DIR = V1_STATIC_DIR / "test-files"

GPS_UPLOAD_DIR = UPLOAD_DATA_DIR / "gps"
