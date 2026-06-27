"""FHIR OAuth flows (Denmark Phase 2, Germany Phase 3)."""
import secrets
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database import get_db
from src.auth.jwt_handler import get_current_user_id
from src.health_profile.models import User, ConsentType
from src.health_profile.encryption import encrypt_field
from src.health_profile.crud import merge_fhir_data
from src.auth.consent import has_consent
from src.fhir.denmark import SundhedsjournalClient
from src.cache import cache_set, cache_get, cache_delete

router = APIRouter(prefix="/fhir", tags=["fhir"])

# PKCE verifiers keyed by state token (must survive the round-trip to MitID)
_PKCE_TTL = 600  # 10 minutes


@router.get("/denmark/connect")
async def connect_denmark_fhir(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Initiate MitID OAuth flow for Sundhedsjournalen."""
    if not await has_consent(db, user_id, ConsentType.fhir_pull):
        raise HTTPException(403, "FHIR pull consent required before connecting health records.")

    state = secrets.token_urlsafe(32)
    await cache_set(f"oauth:state:{state}", user_id, ttl_seconds=_PKCE_TTL)

    client = SundhedsjournalClient()
    # Store the PKCE verifier alongside the state so the callback can retrieve it
    await cache_set(f"oauth:pkce:{state}", client._code_verifier, ttl_seconds=_PKCE_TTL)

    auth_url = await client.get_authorization_url(state)
    return {"auth_url": auth_url}


@router.get("/denmark/callback")
async def denmark_fhir_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    """Handle MitID OAuth callback, fetch FHIR data, merge into profile."""
    user_id = await cache_get(f"oauth:state:{state}")
    code_verifier = await cache_get(f"oauth:pkce:{state}")

    await cache_delete(f"oauth:state:{state}")
    await cache_delete(f"oauth:pkce:{state}")

    if not user_id:
        raise HTTPException(400, "Invalid or expired OAuth state.")

    client = SundhedsjournalClient()
    if code_verifier:
        client._code_verifier = code_verifier
    tokens = await client.exchange_code(code, state)
    access_token = tokens.get("access_token")
    patient_id = tokens.get("patient")

    if not access_token or not patient_id:
        raise HTTPException(502, "Failed to obtain access token from MitID.")

    # Store MitID subject (encrypted)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        sub = tokens.get("sub", "")
        user.mitid_sub_enc = encrypt_field(sub, user_id)
        await db.flush()

    # Fetch and merge FHIR profile
    fhir_profile = await client.fetch_patient_profile(access_token, patient_id)
    await merge_fhir_data(db, user_id, fhir_profile)

    return {"status": "synced", "message": "Health records imported from Sundhedsjournalen."}
