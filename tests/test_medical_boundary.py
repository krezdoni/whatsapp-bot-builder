"""Test medical boundary enforcement in LLM prompts layer."""
import os
os.environ["FIELD_ENCRYPTION_KEY"] = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
os.environ["JWT_SECRET_KEY"] = "test-secret"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://x:x@localhost/x"

from src.llm.prompts import (
    needs_disclaimer, ensure_disclaimer, summarise_profile_for_context
)


def test_needs_disclaimer_clinical_keywords():
    assert needs_disclaimer("Your blood pressure reading looks elevated")
    assert needs_disclaimer("This symptom could be related to your medication")
    assert needs_disclaimer("Your lab results show an HbA1c of 7.2")


def test_needs_disclaimer_clean_response():
    assert not needs_disclaimer("Here is a summary of your appointments this month.")


def test_ensure_disclaimer_not_doubled():
    text_with_doctor = "Please speak with your doctor about this."
    result = ensure_disclaimer(text_with_doctor)
    assert result == text_with_doctor  # no duplicate disclaimer


def test_ensure_disclaimer_added():
    text = "Your HbA1c is 7.2%, which is slightly above the normal range."
    result = ensure_disclaimer(text)
    assert "doctor" in result.lower() or "healthcare" in result.lower()


def test_summarise_profile_active_conditions_only():
    profile = {
        "conditions": [
            {"name": "Hypertension", "status": "active"},
            {"name": "Appendicitis", "status": "inactive"},
        ],
        "medications": [
            {"name": "Metformin", "active": True},
            {"name": "Aspirin", "active": False},
        ],
        "allergies": [{"substance": "Penicillin"}],
    }
    summary = summarise_profile_for_context(profile)
    assert "Hypertension" in summary
    assert "Appendicitis" not in summary  # inactive
    assert "Metformin" in summary
    assert "Aspirin" not in summary  # inactive
    assert "Penicillin" in summary


def test_summarise_empty_profile():
    summary = summarise_profile_for_context({})
    assert "No profile" in summary


def test_disclaimer_variants_cycle():
    from src.llm.prompts import DISCLAIMER_VARIANTS, ensure_disclaimer
    base = "Your cholesterol levels are discussed here."
    for i in range(len(DISCLAIMER_VARIANTS) * 2):
        result = ensure_disclaimer(base, variant_index=i)
        # should always contain some disclaimer
        lower = result.lower()
        assert any(m in lower for m in ["doctor", "healthcare", "provider", "gp", "specialist"])
