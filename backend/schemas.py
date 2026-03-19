from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


# --- Vehicle ---
class VehicleCreate(BaseModel):
    plate: str
    hgs_tag: Optional[str] = None
    owner_name: Optional[str] = None
    balance: Optional[float] = 0.0


class VehicleUpdate(BaseModel):
    hgs_tag: Optional[str] = None
    owner_name: Optional[str] = None
    balance: Optional[float] = None


class VehicleOut(BaseModel):
    id: int
    plate: str
    hgs_tag: Optional[str]
    owner_name: Optional[str]
    balance: float
    created_at: datetime

    class Config:
        from_attributes = True


# --- Passage ---
class PassageCreate(BaseModel):
    plate: str
    location: str
    amount: float
    passed_at: Optional[datetime] = None
    note: Optional[str] = None


class PassageOut(BaseModel):
    id: int
    vehicle_id: int
    location: str
    amount: float
    passed_at: datetime
    note: Optional[str]

    class Config:
        from_attributes = True


# --- Report ---
class VehicleReport(BaseModel):
    plate: str
    owner_name: Optional[str]
    hgs_tag: Optional[str]
    balance: float
    total_passages: int
    total_spent: float
    passages: List[PassageOut]
