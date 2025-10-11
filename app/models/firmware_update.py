from datetime import datetime

from sqlmodel import SQLModel, Field, Relationship

from app.models.firmware import FirmwareDB


class FirmwareUpdateDB(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    update_issued_at: datetime = Field(default_factory=datetime.utcnow)
    update_last_downloaded: datetime | None = None
    target_vehicle_imei: str = Field(foreign_key="vehicledb.imei")
    target_firmware_id: int = Field(foreign_key="firmwaredb.id")

    vehicle: "VehicleDB" = Relationship(back_populates="pending_update")
    target_firmware: "FirmwareDB" = Relationship(back_populates="pending_updates")
