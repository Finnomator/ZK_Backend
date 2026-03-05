from datetime import datetime

from sqlmodel import SQLModel, Field

class _DeviceVehicleAssignmentBase(SQLModel):
    start_time: datetime
    end_time: datetime

class DeviceVehicleAssignmentDB(_DeviceVehicleAssignmentBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    device_imei: str | None = Field(default=None, foreign_key="devicedb.imei")
    vehicle_id: int | None = Field(default=None, foreign_key="vehicledb.id")
