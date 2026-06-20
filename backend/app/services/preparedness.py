from __future__ import annotations

from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Activity, PreparednessHouseholdProfile, PreparednessInventoryItem, PreparednessVolunteer, User
from app.services.participation import submit_activity

READINESS_STATUSES = {"getting_started": 0, "in_progress": 50, "ready": 100}
VOLUNTEER_ROLES = {
    "neighbor_support": "Neighbor Support",
    "supply_steward": "Supply Steward",
    "communications": "Communications",
    "wellness_check": "Wellness Check",
    "training_support": "Training Support",
}

INVENTORY_TARGETS = {
    "water": {"label": "Water", "target": 300, "unit": "gallons"},
    "food": {"label": "Food", "target": 300, "unit": "days"},
    "medical": {"label": "Medical", "target": 100, "unit": "kits"},
    "power": {"label": "Power", "target": 50, "unit": "units"},
    "communication": {"label": "Communication", "target": 50, "unit": "units"},
}


def _status_points(value: str) -> int:
    return READINESS_STATUSES.get((value or "getting_started").strip().lower(), 0)


def household_score(profile: PreparednessHouseholdProfile | None) -> int:
    if not profile:
        return 0
    parts = [
        min(100, round((profile.water_days / 14) * 100)),
        min(100, round((profile.food_days / 14) * 100)),
        _status_points(profile.medical_status),
        _status_points(profile.power_status),
        _status_points(profile.communication_status),
        100 if profile.skills else 0,
    ]
    return round(sum(parts) / len(parts))


def inventory_overview(db: Session) -> list[dict]:
    rows = db.query(
        PreparednessInventoryItem.category,
        func.coalesce(func.sum(PreparednessInventoryItem.quantity), 0),
        func.coalesce(func.max(PreparednessInventoryItem.target_quantity), 0),
    ).group_by(PreparednessInventoryItem.category).all()
    totals = {category: {"quantity": int(quantity or 0), "target": int(target or 0)} for category, quantity, target in rows}
    overview = []
    for category, defaults in INVENTORY_TARGETS.items():
        current = totals.get(category, {})
        target = current.get("target") or defaults["target"]
        quantity = current.get("quantity", 0)
        overview.append({
            "category": category,
            "label": defaults["label"],
            "quantity": quantity,
            "target_quantity": target,
            "unit": defaults["unit"],
            "percent": min(100, round((quantity / max(target, 1)) * 100)),
            "critical": quantity < target * 0.35,
        })
    return overview


def preparedness_summary(db: Session, *, user: User | None = None) -> dict:
    profiles = db.query(PreparednessHouseholdProfile).count()
    volunteers = db.query(PreparednessVolunteer).filter(PreparednessVolunteer.active.is_(True)).count()
    members = max(db.query(User).count(), 1)
    inventory = inventory_overview(db)
    avg_household = int(db.query(func.coalesce(func.avg(PreparednessHouseholdProfile.household_size), 0)).scalar() or 0)
    critical = [item for item in inventory if item["critical"]]
    inventory_score = round(sum(item["percent"] for item in inventory) / max(len(inventory), 1))
    household_participation = min(100, round((profiles / members) * 100))
    volunteer_participation = min(100, round((volunteers / members) * 100))
    preparedness_score = round((inventory_score * 0.4) + (household_participation * 0.3) + (volunteer_participation * 0.3))
    profile = db.query(PreparednessHouseholdProfile).filter(PreparednessHouseholdProfile.user_id == user.id).first() if user else None
    activity = db.query(Activity).filter(Activity.source_module == "preparedness").order_by(Activity.timestamp.desc(), Activity.id.desc()).limit(10).all()
    return {
        "preparedness_score": preparedness_score,
        "community_readiness": "Building Together" if preparedness_score < 50 else "Coordinating" if preparedness_score < 80 else "Resilient Network",
        "household_participation": household_participation,
        "volunteer_participation": volunteer_participation,
        "household_profiles": profiles,
        "average_household_size": avg_household,
        "active_volunteers": volunteers,
        "inventory": inventory,
        "critical_shortages": critical,
        "profile": serialize_profile(profile) if profile else None,
        "profile_score": household_score(profile),
        "activity": [serialize_activity(item) for item in activity],
    }


def serialize_profile(profile: PreparednessHouseholdProfile) -> dict:
    return {key: getattr(profile, key) for key in ["id", "household_size", "neighborhood", "water_days", "food_days", "medical_status", "power_status", "communication_status", "skills", "notes"]} | {"score": household_score(profile)}


def serialize_inventory(item: PreparednessInventoryItem) -> dict:
    return {key: getattr(item, key) for key in ["id", "item_name", "category", "quantity", "unit", "target_quantity", "storage_location", "notes"]}


def serialize_volunteer(item: PreparednessVolunteer) -> dict:
    return {key: getattr(item, key) for key in ["id", "role", "availability", "neighborhood", "skills", "notes", "active"]} | {"role_label": VOLUNTEER_ROLES.get(item.role, item.role)}


def serialize_activity(activity: Activity) -> dict:
    labels = {
        "preparedness_profile_completed": "Preparedness profile completed",
        "preparedness_volunteer_joined": "Volunteer joined",
        "preparedness_supplies_logged": "Community supplies logged",
        "preparedness_training_attended": "Training attended",
        "preparedness_household_supported": "Household readiness supported",
    }
    return {"id": activity.id, "title": labels.get(activity.activity_type, activity.activity_type.replace("_", " ").title()), "timestamp": activity.timestamp.isoformat() if activity.timestamp else None, "metadata": activity.metadata_ or {}}


def upsert_profile(db: Session, *, user: User, payload: dict) -> PreparednessHouseholdProfile:
    profile = db.query(PreparednessHouseholdProfile).filter(PreparednessHouseholdProfile.user_id == user.id).first()
    if not profile:
        profile = PreparednessHouseholdProfile(user_id=user.id)
        db.add(profile)
    for key in ["household_size", "neighborhood", "water_days", "food_days", "medical_status", "power_status", "communication_status", "skills", "notes"]:
        if key in payload:
            setattr(profile, key, payload[key])
    db.flush()
    submit_activity(db, user=user, guest_session_id=None, activity_type_name="preparedness_profile_completed", source_module="preparedness", metadata={"neighborhood": profile.neighborhood})
    return profile
