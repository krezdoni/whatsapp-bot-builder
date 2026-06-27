"""Health profile CRUD routes (authenticated, for PWA)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database import get_db
from src.auth.jwt_handler import get_current_user_id
from src.health_profile.crud import get_profile, update_profile, get_profile_row
from src.health_profile.schemas import HealthProfileResponse, HealthProfileUpdate
from src.health_profile.models import HealthProfile

router = APIRouter(prefix="/profile", tags=["health_profile"])


@router.get("", response_model=HealthProfileResponse)
async def read_profile(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    row = await get_profile_row(db, user_id)
    if row is None:
        raise HTTPException(404, "Health profile not found. Complete registration first.")
    from src.health_profile.crud import _decrypt_profile
    profile_data = _decrypt_profile(row, user_id)
    return HealthProfileResponse(
        user_id=user_id,
        profile=profile_data,
        fhir_last_synced_at=row.fhir_last_synced_at,
        updated_at=row.updated_at,
    )


@router.patch("", response_model=HealthProfileResponse)
async def patch_profile(
    body: HealthProfileUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    profile_data = await update_profile(db, user_id, body)
    row = await get_profile_row(db, user_id)
    return HealthProfileResponse(
        user_id=user_id,
        profile=profile_data,
        fhir_last_synced_at=row.fhir_last_synced_at if row else None,
        updated_at=row.updated_at if row else None,
    )
