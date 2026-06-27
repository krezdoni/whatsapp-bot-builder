"""Consent management — create, verify, and revoke granular consents."""
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from src.health_profile.models import UserConsent, ConsentType


CONSENT_TEXT_VERSION = "v1.0"

CONSENT_TEXTS = {
    ConsentType.profile_storage: (
        "I consent to my health information being stored on EU servers (Hetzner Frankfurt, Germany) "
        "encrypted at rest, for the purpose of providing personalised health assistance."
    ),
    ConsentType.fhir_pull: (
        "I consent to retrieval of my health records from the national health record system "
        "(Sundhedsjournalen / ePA) via secure OAuth, to populate my health profile."
    ),
    ConsentType.document_processing: (
        "I consent to uploaded health documents being processed via OCR and AI extraction "
        "to populate my health profile. Documents are processed on EU servers only."
    ),
    ConsentType.messaging_channel: (
        "I consent to receiving personalised health information via my chosen messaging channel."
    ),
    ConsentType.whatsapp_meta_exposure: (
        "I acknowledge that using WhatsApp means message metadata (sender, timestamp, message length) "
        "is accessible to Meta Platforms Inc. (US), even though message content is end-to-end encrypted. "
        "Health data content is not shared with Meta. I accept this trade-off."
    ),
}


async def record_consent(
    db: AsyncSession,
    user_id: str,
    consent_type: ConsentType,
    granted: bool,
    ip_address: str | None = None,
) -> UserConsent:
    consent = UserConsent(
        user_id=user_id,
        consent_type=consent_type.value,
        granted=granted,
        consent_text_version=CONSENT_TEXT_VERSION,
        ip_address=ip_address,
    )
    db.add(consent)
    await db.flush()
    return consent


async def has_consent(
    db: AsyncSession, user_id: str, consent_type: ConsentType
) -> bool:
    """Returns True if the user's most recent consent record for this type is granted."""
    result = await db.execute(
        select(UserConsent)
        .where(
            and_(
                UserConsent.user_id == user_id,
                UserConsent.consent_type == consent_type.value,
            )
        )
        .order_by(UserConsent.timestamp.desc())
        .limit(1)
    )
    row = result.scalar_one_or_none()
    return row is not None and row.granted


async def get_all_consents(db: AsyncSession, user_id: str) -> dict[str, bool]:
    """Return the current (most recent) consent status per type."""
    result = await db.execute(
        select(UserConsent)
        .where(UserConsent.user_id == user_id)
        .order_by(UserConsent.timestamp.desc())
    )
    rows = result.scalars().all()

    # Latest per type wins
    seen: dict[str, bool] = {}
    for row in rows:
        if row.consent_type not in seen:
            seen[row.consent_type] = row.granted
    return seen
