"""
Auth routes: registration, consent, login.
Consent is granular — separate endpoint per consent type.
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database import get_db
from src.health_profile.models import User, ConsentType, MessagingChannel
from src.health_profile.encryption import encrypt_field
from src.health_profile.crud import create_profile
from src.auth.jwt_handler import create_access_token, get_current_user_id
from src.auth.consent import record_consent, get_all_consents, CONSENT_TEXTS, CONSENT_TEXT_VERSION

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    messaging_channel: str  # "threema" or "whatsapp"
    threema_id: str | None = None
    phone_number: str | None = None
    data_retention_years: int = 2


class RegisterResponse(BaseModel):
    user_id: str
    access_token: str
    consent_texts: dict[str, str]


class ConsentRequest(BaseModel):
    consent_type: str
    granted: bool


class ConsentStatusResponse(BaseModel):
    consents: dict[str, bool]


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, request: Request, db: AsyncSession = Depends(get_db)):
    channel = body.messaging_channel.lower()
    if channel not in ("threema", "whatsapp"):
        raise HTTPException(400, "messaging_channel must be 'threema' or 'whatsapp'")
    if channel == "threema" and not body.threema_id:
        raise HTTPException(400, "threema_id is required for Threema channel")
    if channel == "whatsapp" and not body.phone_number:
        raise HTTPException(400, "phone_number is required for WhatsApp channel")

    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        messaging_channel=channel,
        data_retention_years=body.data_retention_years,
    )
    if body.threema_id:
        user.threema_id_enc = encrypt_field(body.threema_id, user_id)
    if body.phone_number:
        user.phone_number_enc = encrypt_field(body.phone_number, user_id)

    db.add(user)
    await db.flush()

    # Create empty health profile
    await create_profile(db, user_id)

    token = create_access_token(user_id)
    return RegisterResponse(
        user_id=user_id,
        access_token=token,
        consent_texts={k.value: v for k, v in CONSENT_TEXTS.items()},
    )


@router.post("/consent")
async def update_consent(
    body: ConsentRequest,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        consent_type = ConsentType(body.consent_type)
    except ValueError:
        raise HTTPException(400, f"Unknown consent type: {body.consent_type}")

    ip = request.client.host if request.client else None
    consent = await record_consent(db, user_id, consent_type, body.granted, ip)

    # WhatsApp: record consent timestamp on user record
    if consent_type == ConsentType.whatsapp_meta_exposure and body.granted:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.whatsapp_consent_timestamp = datetime.utcnow()
            user.whatsapp_consent_text_version = CONSENT_TEXT_VERSION
            await db.flush()

    return {"status": "recorded", "consent_type": body.consent_type, "granted": body.granted}


@router.get("/consent", response_model=ConsentStatusResponse)
async def get_consent_status(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    consents = await get_all_consents(db, user_id)
    return ConsentStatusResponse(consents=consents)


@router.get("/consent-texts")
async def get_consent_texts():
    return {k.value: v for k, v in CONSENT_TEXTS.items()}
