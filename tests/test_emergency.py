"""Test emergency keyword pre-filter — safety-critical."""
import os
os.environ["FIELD_ENCRYPTION_KEY"] = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
os.environ["JWT_SECRET_KEY"] = "test-secret"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://x:x@localhost/x"

from src.llm.emergency import check_emergency, EMERGENCY_RESPONSE


# ── Should trigger ─────────────────────────────────────────────────────────────

def test_english_chest_pain():
    assert check_emergency("I have chest pain and can't breathe") is not None

def test_english_suicide():
    assert check_emergency("I want to kill myself") is not None

def test_english_overdose():
    assert check_emergency("I think I took an overdose") is not None

def test_danish_hjerteanfald():
    assert check_emergency("Jeg tror jeg har et hjerteanfald") is not None

def test_danish_selvmord():
    assert check_emergency("Jeg tænker på selvmord") is not None

def test_danish_brystsmerter():
    assert check_emergency("Jeg har brystsmerter og kan ikke trække vejret") is not None

def test_german_herzinfarkt():
    assert check_emergency("Ich glaube ich habe einen Herzinfarkt") is not None

def test_german_suizid():
    assert check_emergency("Ich denke an Suizid") is not None

def test_case_insensitive():
    assert check_emergency("CHEST PAIN radiating to my arm") is not None
    assert check_emergency("BRYSTSMERTER") is not None


# ── Should NOT trigger ────────────────────────────────────────────────────────

def test_normal_health_question():
    assert check_emergency("What does my HbA1c of 6.8 mean?") is None

def test_appointment_question():
    assert check_emergency("Can you help me prepare for my cardiology appointment?") is None

def test_lab_question():
    assert check_emergency("My cholesterol is 5.2 mmol/L, is that normal?") is None

def test_medication_question():
    assert check_emergency("What are the side effects of Metformin?") is None


# ── Response content ──────────────────────────────────────────────────────────

def test_english_response_contains_112():
    resp = check_emergency("chest pain")
    assert "112" in resp

def test_danish_response_contains_1813():
    resp = check_emergency("brystsmerter")
    assert "1813" in resp

def test_german_response_contains_116117():
    resp = check_emergency("herzinfarkt")
    assert "116 117" in resp

def test_response_is_urgent():
    resp = check_emergency("chest pain")
    lower = resp.lower()
    assert "emergency" in lower or "nødsituation" in lower or "notfall" in lower

def test_all_responses_reference_112():
    for resp in EMERGENCY_RESPONSE.values():
        assert "112" in resp
