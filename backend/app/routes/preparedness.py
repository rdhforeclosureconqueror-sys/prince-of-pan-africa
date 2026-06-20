from __future__ import annotations

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user, require_auth
from app.models import PreparednessInventoryItem, PreparednessVolunteer
from app.services.participation import submit_activity
from app.services.preparedness import VOLUNTEER_ROLES, preparedness_summary, serialize_inventory, serialize_profile, serialize_volunteer, upsert_profile

router = APIRouter(prefix="/preparedness", tags=["Preparedness"])


class HouseholdProfilePayload(BaseModel):
    household_size: int = Field(default=1, ge=1, le=50)
    neighborhood: str = Field(default="", max_length=255)
    water_days: int = Field(default=0, ge=0, le=365)
    food_days: int = Field(default=0, ge=0, le=365)
    medical_status: str = Field(default="getting_started", max_length=64)
    power_status: str = Field(default="getting_started", max_length=64)
    communication_status: str = Field(default="getting_started", max_length=64)
    skills: list[str] = Field(default_factory=list)
    notes: str = Field(default="", max_length=1000)


class InventoryPayload(BaseModel):
    item_name: str = Field(min_length=1, max_length=255)
    category: str = Field(default="general", max_length=64)
    quantity: int = Field(default=1, ge=0, le=1_000_000)
    unit: str = Field(default="units", max_length=64)
    target_quantity: int = Field(default=0, ge=0, le=1_000_000)
    storage_location: str = Field(default="", max_length=255)
    notes: str = Field(default="", max_length=1000)


class VolunteerPayload(BaseModel):
    role: str = Field(default="neighbor_support", max_length=64)
    availability: str = Field(default="as_available", max_length=64)
    neighborhood: str = Field(default="", max_length=255)
    skills: list[str] = Field(default_factory=list)
    notes: str = Field(default="", max_length=1000)
    active: bool = True


@router.get("/summary")
def get_preparedness_summary(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return {"ok": True, "preparedness": preparedness_summary(db, user=current_user), "volunteer_roles": VOLUNTEER_ROLES}


@router.put("/household-profile")
def save_household_profile(payload: HouseholdProfilePayload, db: Session = Depends(get_db), current_user=Depends(require_auth)):
    profile = upsert_profile(db, user=current_user, payload=payload.model_dump())
    db.commit()
    return {"ok": True, "profile": serialize_profile(profile), "preparedness": preparedness_summary(db, user=current_user)}


@router.post("/inventory", status_code=status.HTTP_201_CREATED)
def create_inventory_item(payload: InventoryPayload, db: Session = Depends(get_db), current_user=Depends(require_auth)):
    item = PreparednessInventoryItem(user_id=current_user.id, **payload.model_dump())
    db.add(item)
    db.flush()
    submit_activity(db, user=current_user, guest_session_id=None, activity_type_name="preparedness_supplies_logged", source_module="preparedness", metadata={"item_name": item.item_name, "quantity": item.quantity, "unit": item.unit})
    db.commit()
    return {"ok": True, "item": serialize_inventory(item), "preparedness": preparedness_summary(db, user=current_user)}


@router.get("/inventory")
def list_inventory(db: Session = Depends(get_db)):
    items = db.query(PreparednessInventoryItem).order_by(PreparednessInventoryItem.updated_at.desc(), PreparednessInventoryItem.id.desc()).limit(100).all()
    return {"ok": True, "items": [serialize_inventory(item) for item in items]}


@router.put("/volunteer")
def save_volunteer(payload: VolunteerPayload, db: Session = Depends(get_db), current_user=Depends(require_auth)):
    role = payload.role if payload.role in VOLUNTEER_ROLES else "neighbor_support"
    volunteer = db.query(PreparednessVolunteer).filter(PreparednessVolunteer.user_id == current_user.id).first()
    created = volunteer is None
    if not volunteer:
        volunteer = PreparednessVolunteer(user_id=current_user.id)
        db.add(volunteer)
    data = payload.model_dump()
    data["role"] = role
    for key, value in data.items():
        setattr(volunteer, key, value)
    db.flush()
    submit_activity(db, user=current_user, guest_session_id=None, activity_type_name="preparedness_volunteer_joined", source_module="preparedness", metadata={"role": role, "created": created})
    db.commit()
    return {"ok": True, "volunteer": serialize_volunteer(volunteer), "preparedness": preparedness_summary(db, user=current_user)}
