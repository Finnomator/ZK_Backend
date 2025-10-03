import os
import pathlib
from datetime import datetime

from app.internal.paths import UPLOAD_DATA_DIR


def make_uploaded_data_path(prefix: str, mac: int, upload_time: datetime, file_extension: str) -> pathlib.Path:
    year = upload_time.strftime("%Y")
    month = upload_time.strftime("%m")
    timestamp = upload_time.strftime("%Y%m%d_%H%M%S")

    # start with counter = 1, increment if folder already exists
    counter = 1
    while True:
        file_path = UPLOAD_DATA_DIR / prefix / hex(mac)[2:] / year / month / f"{timestamp}_{counter}{file_extension}"
        if not os.path.exists(file_path):
            break
        counter += 1

    return file_path
