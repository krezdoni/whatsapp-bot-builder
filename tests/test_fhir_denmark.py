"""Test Sundhedsjournalen FHIR parser functions (no network calls)."""
import os
os.environ["FIELD_ENCRYPTION_KEY"] = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
os.environ["JWT_SECRET_KEY"] = "test-secret"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://x:x@localhost/x"
os.environ["MITID_CLIENT_ID"] = "test"
os.environ["MITID_CLIENT_SECRET"] = "test"
os.environ["MITID_REDIRECT_URI"] = "http://localhost/callback"

from src.fhir.denmark import (
    _parse_conditions, _parse_medications, _parse_allergies,
    _parse_vaccinations, _parse_observations, SundhedsjournalClient
)


CONDITION_BUNDLE = {
    "entry": [{
        "resource": {
            "resourceType": "Condition",
            "code": {
                "coding": [{"system": "http://hl7.org/fhir/sid/icd-10", "code": "I10", "display": "Hypertension"}],
                "text": "Hypertension"
            },
            "clinicalStatus": {"coding": [{"code": "active"}]},
            "onsetDateTime": "2020-01-15T00:00:00Z",
        }
    }]
}

MEDICATION_BUNDLE = {
    "entry": [{
        "resource": {
            "resourceType": "MedicationStatement",
            "medicationCodeableConcept": {
                "coding": [{"display": "Metformin 500mg"}],
                "text": "Metformin 500mg"
            },
            "status": "active",
            "dosage": [{"text": "500mg twice daily"}],
        }
    }]
}

ALLERGY_BUNDLE = {
    "entry": [{
        "resource": {
            "resourceType": "AllergyIntolerance",
            "code": {"text": "Penicillin", "coding": [{"display": "Penicillin"}]},
            "reaction": [{"description": "Rash", "severity": "moderate"}],
        }
    }]
}

LAB_BUNDLE = {
    "entry": [{
        "resource": {
            "resourceType": "Observation",
            "code": {"coding": [{"display": "HbA1c"}], "text": "HbA1c"},
            "valueQuantity": {"value": 6.8, "unit": "%"},
            "effectiveDateTime": "2024-03-01T00:00:00Z",
            "referenceRange": [{"text": "< 5.7%"}],
            "interpretation": [{"coding": [{"code": "H"}]}],
        }
    }]
}


def test_parse_conditions():
    conditions = _parse_conditions(CONDITION_BUNDLE)
    assert len(conditions) == 1
    assert conditions[0].name == "Hypertension"
    assert conditions[0].icd_code == "I10"
    assert conditions[0].status == "active"
    assert conditions[0].onset_date == "2020-01-15"
    assert conditions[0].source == "fhir_dk"


def test_parse_medications():
    meds = _parse_medications(MEDICATION_BUNDLE)
    assert len(meds) == 1
    assert "Metformin" in meds[0].name
    assert meds[0].active is True
    assert meds[0].dose == "500mg twice daily"


def test_parse_allergies():
    allergies = _parse_allergies(ALLERGY_BUNDLE)
    assert len(allergies) == 1
    assert allergies[0].substance == "Penicillin"
    assert allergies[0].reaction == "Rash"
    assert allergies[0].severity == "moderate"


def test_parse_observations():
    labs = _parse_observations(LAB_BUNDLE)
    assert len(labs) == 1
    assert labs[0].test == "HbA1c"
    assert labs[0].value == "6.8"
    assert labs[0].unit == "%"
    assert labs[0].date == "2024-03-01"
    assert labs[0].flag == "H"


def test_parse_empty_bundle():
    assert _parse_conditions({"entry": []}) == []
    assert _parse_medications({}) == []


def test_pkce_challenge_deterministic():
    verifier = "test-verifier-string"
    c1 = SundhedsjournalClient._pkce_challenge(verifier)
    c2 = SundhedsjournalClient._pkce_challenge(verifier)
    assert c1 == c2
    assert len(c1) > 20
