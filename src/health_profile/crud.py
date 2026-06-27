"""CRUD operations for health profiles. All reads/writes go through encryption layer."""
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.health_profile.models import HealthProfile
from src.health_profile.schemas import HealthProfileData, HealthProfileUpdate
from src.health_profile.encryption import encrypt_json, decrypt_json


async def get_profile(db: AsyncSession, user_id: str) -> HealthProfileData | None:
    result = await db.execute(select(HealthProfile).where(HealthProfile.user_id == user_id))
    row = result.scalar_one_or_none()
    if row is None:
        return None
    return _decrypt_profile(row, user_id)


async def get_profile_row(db: AsyncSession, user_id: str) -> HealthProfile | None:
    result = await db.execute(select(HealthProfile).where(HealthProfile.user_id == user_id))
    return result.scalar_one_or_none()


async def create_profile(db: AsyncSession, user_id: str) -> HealthProfile:
    profile = HealthProfile(user_id=user_id)
    db.add(profile)
    await db.flush()
    return profile


async def update_profile(
    db: AsyncSession, user_id: str, update: HealthProfileUpdate
) -> HealthProfileData:
    result = await db.execute(select(HealthProfile).where(HealthProfile.user_id == user_id))
    row = result.scalar_one_or_none()

    if row is None:
        row = await create_profile(db, user_id)

    existing = _decrypt_profile(row, user_id)

    if update.conditions is not None:
        row.conditions_enc = encrypt_json([c.model_dump() for c in update.conditions], user_id)
    if update.medications is not None:
        row.medications_enc = encrypt_json([m.model_dump() for m in update.medications], user_id)
    if update.allergies is not None:
        row.allergies_enc = encrypt_json([a.model_dump() for a in update.allergies], user_id)
    if update.providers is not None:
        row.providers_enc = encrypt_json([p.model_dump() for p in update.providers], user_id)
    if update.vaccinations is not None:
        row.vaccinations_enc = encrypt_json([v.model_dump() for v in update.vaccinations], user_id)
    if update.lab_history is not None:
        row.lab_history_enc = encrypt_json([l.model_dump() for l in update.lab_history], user_id)
    if update.appointments is not None:
        row.appointments_enc = encrypt_json([a.model_dump() for a in update.appointments], user_id)
    if update.notes is not None:
        row.notes_enc = encrypt_json(update.notes, user_id)

    await db.flush()
    return _decrypt_profile(row, user_id)


async def merge_fhir_data(
    db: AsyncSession, user_id: str, fhir_profile: HealthProfileData
) -> HealthProfileData:
    """Merge FHIR-sourced data into the user's profile (additive, FHIR data marked by source)."""
    update = HealthProfileUpdate(
        conditions=fhir_profile.conditions,
        medications=fhir_profile.medications,
        allergies=fhir_profile.allergies,
        providers=fhir_profile.providers,
        vaccinations=fhir_profile.vaccinations,
        lab_history=fhir_profile.lab_history,
        appointments=fhir_profile.appointments,
    )
    result = await update_profile(db, user_id, update)

    # Mark fhir sync timestamp
    profile_row = await get_profile_row(db, user_id)
    if profile_row:
        profile_row.fhir_last_synced_at = datetime.utcnow()
        await db.flush()

    return result


def _decrypt_profile(row: HealthProfile, user_id: str) -> HealthProfileData:
    def safe_decrypt_list(token: str | None, model_cls):
        if not token:
            return []
        raw = decrypt_json(token, user_id)
        return [model_cls(**item) for item in raw]

    from src.health_profile.schemas import (
        Condition, Medication, Allergy, Provider,
        Vaccination, LabResult, Appointment
    )

    return HealthProfileData(
        conditions=safe_decrypt_list(row.conditions_enc, Condition),
        medications=safe_decrypt_list(row.medications_enc, Medication),
        allergies=safe_decrypt_list(row.allergies_enc, Allergy),
        providers=safe_decrypt_list(row.providers_enc, Provider),
        vaccinations=safe_decrypt_list(row.vaccinations_enc, Vaccination),
        lab_history=safe_decrypt_list(row.lab_history_enc, LabResult),
        appointments=safe_decrypt_list(row.appointments_enc, Appointment),
        notes=decrypt_json(row.notes_enc, user_id) if row.notes_enc else [],
    )
