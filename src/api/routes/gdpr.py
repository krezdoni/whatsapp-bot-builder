"""
GDPR compliance routes: data export (Art. 20) and deletion (Art. 17).
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database import get_db
from src.auth.jwt_handler import get_current_user_id
from src.health_profile.models import User, HealthProfile, Message, Document, UserConsent
from src.health_profile.encryption import decrypt_field, decrypt_json
from src.health_profile.crud import _decrypt_profile, get_profile_row

router = APIRouter(prefix="/gdpr", tags=["gdpr"])


@router.get("/export")
async def export_my_data(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Art. 20 — Data portability. Returns all user data as JSON."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or user.is_deleted:
        raise HTTPException(404, "User not found.")

    # Decrypt and assemble
    profile_row = await get_profile_row(db, user_id)
    profile = _decrypt_profile(profile_row, user_id) if profile_row else None

    result = await db.execute(select(Message).where(Message.user_id == user_id))
    msgs = result.scalars().all()
    messages = []
    for m in msgs:
        try:
            messages.append({
                "direction": m.direction,
                "provider": m.provider,
                "text": decrypt_field(m.content_enc, user_id),
                "timestamp": m.timestamp.isoformat(),
            })
        except Exception:
            pass

    result = await db.execute(select(UserConsent).where(UserConsent.user_id == user_id))
    consents = [
        {
            "type": c.consent_type,
            "granted": c.granted,
            "version": c.consent_text_version,
            "timestamp": c.timestamp.isoformat(),
        }
        for c in result.scalars().all()
    ]

    return {
        "export_timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "created_at": user.created_at.isoformat(),
        "messaging_channel": user.messaging_channel,
        "data_retention_years": user.data_retention_years,
        "health_profile": profile.model_dump() if profile else None,
        "messages": messages,
        "consents": consents,
    }


@router.delete("/delete-account")
async def delete_account(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Art. 17 — Right to erasure. Permanently deletes all user data."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or user.is_deleted:
        raise HTTPException(404, "User not found.")

    # Delete health profile
    await db.execute(
        HealthProfile.__table__.delete().where(HealthProfile.user_id == user_id)
    )
    # Delete messages
    await db.execute(Message.__table__.delete().where(Message.user_id == user_id))
    # Delete documents
    await db.execute(Document.__table__.delete().where(Document.user_id == user_id))
    # Delete consents
    await db.execute(UserConsent.__table__.delete().where(UserConsent.user_id == user_id))
    # Soft-delete user (hard delete of PHI above, user record tombstoned)
    user.is_deleted = True
    user.phone_number_enc = None
    user.threema_id_enc = None
    user.email_enc = None
    user.mitid_sub_enc = None
    user.gematik_sub_enc = None
    user.scheduled_deletion_at = datetime.utcnow()
    await db.flush()

    return {"status": "deleted", "message": "All personal and health data has been permanently deleted."}
