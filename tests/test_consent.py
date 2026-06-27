"""Test consent management — granular consent per purpose."""
import os
os.environ["FIELD_ENCRYPTION_KEY"] = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
os.environ["JWT_SECRET_KEY"] = "test-secret"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://x:x@localhost/x"

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.consent import (
    record_consent, has_consent, get_all_consents, CONSENT_TEXTS, CONSENT_TEXT_VERSION
)
from src.health_profile.models import ConsentType, UserConsent


@pytest.mark.asyncio
async def test_consent_texts_all_types_covered():
    """All ConsentType values must have a consent text."""
    for ct in ConsentType:
        assert ct in CONSENT_TEXTS, f"Missing consent text for {ct}"


@pytest.mark.asyncio
async def test_consent_texts_not_empty():
    for ct, text in CONSENT_TEXTS.items():
        assert len(text) > 20, f"Consent text for {ct} is too short"


def test_consent_text_version_format():
    assert CONSENT_TEXT_VERSION.startswith("v")


@pytest.mark.asyncio
async def test_whatsapp_consent_mentions_meta():
    text = CONSENT_TEXTS[ConsentType.whatsapp_meta_exposure]
    assert "Meta" in text or "metadata" in text.lower()


@pytest.mark.asyncio
async def test_whatsapp_consent_explains_what_is_not_shared():
    text = CONSENT_TEXTS[ConsentType.whatsapp_meta_exposure]
    lower = text.lower()
    assert "content" in lower or "health" in lower
