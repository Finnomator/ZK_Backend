from datetime import datetime
from enum import Enum

from sqlalchemy import Column, ForeignKey
from sqlmodel import SQLModel, Field, Relationship

from app.models.vehicle import VehicleDB


class LoggingLevel(str, Enum):
    debug = "DEBUG"
    info = "INFO"
    warning = "WARNING"
    error = "ERROR"
    critical = "CRITICAL"


class _LogEntryBase(SQLModel):
    timestamp: datetime
    level: LoggingLevel
    message: str
    imei: str
    timestamp_is_valid: bool # in case the Modem failed to sync time with network
    upload_timestamp: datetime

    def __str__(self):
        return f"[{self.timestamp.isoformat()}][{self.level.value}] {self.message}"


class LogEntryDB(_LogEntryBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    imei: str = Field(sa_column=Column(ForeignKey("vehicledb.imei")))
    vehicle: VehicleDB = Relationship(back_populates="logs")


def char_to_logging_level(char: str) -> LoggingLevel:
    match char:
        case "D":
            return LoggingLevel.debug
        case "I":
            return LoggingLevel.info
        case "W":
            return LoggingLevel.warning
        case "E":
            return LoggingLevel.error
        case "C":
            return LoggingLevel.critical

    raise ValueError()
