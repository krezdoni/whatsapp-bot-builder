"""
Sundhedsjournalen FHIR client — Denmark.

Auth: MitID / NemID OAuth 2.0 with PKCE.
FHIR server: Sundhedsdatastyrelsen (Danish Health Data Authority).

References:
- https://sundhedsjournalen.dk/for-udviklere
- FHIR R4 endpoint: configurable via SUNDHEDSJOURNALEN_FHIR_URL env var
"""
import urllib.parse
import secrets
import hashlib
import base64
import httpx

from src.fhir.client import FHIRClient
from src.health_profile.schemas import (
    HealthProfileData, Condition, Medication, Allergy,
    Vaccination, LabResult, Appointment, Provider
)
from src.config import get_settings

# OAuth2 / MitID endpoints
MITID_AUTH_URL = "https://pp.netseidbroker.dk/op/connect/authorize"
MITID_TOKEN_URL = "https://pp.netseidbroker.dk/op/connect/token"

FHIR_SCOPES = [
    "openid",
    "patient/Patient.read",
    "patient/Condition.read",
    "patient/MedicationStatement.read",
    "patient/AllergyIntolerance.read",
    "patient/Immunization.read",
    "patient/Observation.read",
    "patient/Appointment.read",
    "patient/Practitioner.read",
]


class SundhedsjournalClient(FHIRClient):
    """FHIR client for Danish Sundhedsjournalen via MitID OAuth."""

    def __init__(self):
        self._settings = get_settings()
        # code_verifier → code_challenge for PKCE
        self._code_verifier = secrets.token_urlsafe(64)

    async def get_authorization_url(self, state: str) -> str:
        s = self._settings
        challenge = self._pkce_challenge(self._code_verifier)
        params = {
            "response_type": "code",
            "client_id": s.mitid_client_id,
            "redirect_uri": s.mitid_redirect_uri,
            "scope": " ".join(FHIR_SCOPES),
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "acr_values": "https://data.gov.dk/concept/core/nsis/loa/High",
        }
        return f"{MITID_AUTH_URL}?{urllib.parse.urlencode(params)}"

    async def exchange_code(self, code: str, state: str) -> dict:
        s = self._settings
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                MITID_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": s.mitid_redirect_uri,
                    "client_id": s.mitid_client_id,
                    "client_secret": s.mitid_client_secret,
                    "code_verifier": self._code_verifier,
                },
            )
            resp.raise_for_status()
            return resp.json()

    async def fetch_patient_profile(self, access_token: str, patient_id: str) -> HealthProfileData:
        fhir_url = self._settings.sundhedsjournalen_fhir_url
        profile = HealthProfileData()

        # Conditions
        bundle = await self._fhir_get(fhir_url, "Condition", access_token, {"patient": patient_id})
        profile.conditions = _parse_conditions(bundle)

        # Medications
        bundle = await self._fhir_get(fhir_url, "MedicationStatement", access_token, {"patient": patient_id})
        profile.medications = _parse_medications(bundle)

        # Allergies
        bundle = await self._fhir_get(fhir_url, "AllergyIntolerance", access_token, {"patient": patient_id})
        profile.allergies = _parse_allergies(bundle)

        # Vaccinations
        bundle = await self._fhir_get(fhir_url, "Immunization", access_token, {"patient": patient_id})
        profile.vaccinations = _parse_vaccinations(bundle)

        # Lab results
        bundle = await self._fhir_get(
            fhir_url, "Observation", access_token,
            {"patient": patient_id, "category": "laboratory"}
        )
        profile.lab_history = _parse_observations(bundle)

        return profile

    @staticmethod
    def _pkce_challenge(verifier: str) -> str:
        digest = hashlib.sha256(verifier.encode()).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


# ── FHIR resource parsers ──────────────────────────────────────────────────────

def _parse_conditions(bundle: dict) -> list[Condition]:
    out = []
    for entry in bundle.get("entry", []):
        res = entry.get("resource", {})
        code = res.get("code", {})
        codings = code.get("coding", [{}])
        name = codings[0].get("display", code.get("text", "Unknown"))
        icd = next((c.get("code") for c in codings if "icd" in c.get("system", "").lower()), None)
        onset = res.get("onsetDateTime", "")[:10] if res.get("onsetDateTime") else None
        status = "active" if res.get("clinicalStatus", {}).get("coding", [{}])[0].get("code") == "active" else "inactive"
        out.append(Condition(name=name, icd_code=icd, onset_date=onset, status=status, source="fhir_dk"))
    return out


def _parse_medications(bundle: dict) -> list[Medication]:
    out = []
    for entry in bundle.get("entry", []):
        res = entry.get("resource", {})
        med_ref = res.get("medicationCodeableConcept", {})
        name = med_ref.get("text") or med_ref.get("coding", [{}])[0].get("display", "Unknown")
        dosage = res.get("dosage", [{}])
        dose_text = dosage[0].get("text") if dosage else None
        status = res.get("status", "active")
        out.append(Medication(name=name, dose=dose_text, active=(status == "active")))
    return out


def _parse_allergies(bundle: dict) -> list[Allergy]:
    out = []
    for entry in bundle.get("entry", []):
        res = entry.get("resource", {})
        code = res.get("code", {})
        substance = code.get("text") or code.get("coding", [{}])[0].get("display", "Unknown")
        reactions = res.get("reaction", [{}])
        reaction_text = reactions[0].get("description") if reactions else None
        severity = reactions[0].get("severity") if reactions else None
        out.append(Allergy(substance=substance, reaction=reaction_text, severity=severity))
    return out


def _parse_vaccinations(bundle: dict) -> list[Vaccination]:
    out = []
    for entry in bundle.get("entry", []):
        res = entry.get("resource", {})
        code = res.get("vaccineCode", {})
        name = code.get("text") or code.get("coding", [{}])[0].get("display", "Unknown")
        date = res.get("occurrenceDateTime", "")[:10] if res.get("occurrenceDateTime") else None
        lot = res.get("lotNumber")
        out.append(Vaccination(vaccine=name, date=date, lot=lot))
    return out


def _parse_observations(bundle: dict) -> list[LabResult]:
    out = []
    for entry in bundle.get("entry", []):
        res = entry.get("resource", {})
        code = res.get("code", {})
        test = code.get("text") or code.get("coding", [{}])[0].get("display", "Unknown")
        value_qty = res.get("valueQuantity", {})
        value = str(value_qty.get("value", "")) if value_qty else res.get("valueString", "")
        unit = value_qty.get("unit")
        ref = res.get("referenceRange", [{}])
        ref_text = ref[0].get("text") if ref else None
        date = res.get("effectiveDateTime", "")[:10] if res.get("effectiveDateTime") else ""
        flag = None
        for interp in res.get("interpretation", []):
            flag = interp.get("coding", [{}])[0].get("code")
            break
        out.append(LabResult(test=test, value=value, unit=unit, reference_range=ref_text, date=date, flag=flag))
    return out
