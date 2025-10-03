from datetime import datetime
from enum import Enum

from sqlalchemy import Column, ForeignKey, BigInteger
from sqlmodel import SQLModel, Field, Relationship

from app.models.ints import CHIP_ID
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
    chip_id: CHIP_ID

    def __str__(self):
        return f"[{self.timestamp.isoformat()}][{self.level.value}] {self.message}"


class LogEntryDB(_LogEntryBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    chip_id: CHIP_ID = Field(sa_column=Column(BigInteger(), ForeignKey("vehicledb.chip_id")))
    vehicle: VehicleDB = Relationship(back_populates="logs")



def int_to_logging_level(level: int) -> LoggingLevel:
    match level:
        case 0:
            return LoggingLevel.debug
        case 1:
            return LoggingLevel.info
        case 2:
            return LoggingLevel.warning
        case 3:
            return LoggingLevel.error
        case 4:
            return LoggingLevel.critical

    raise ValueError()
