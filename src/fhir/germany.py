"""
gematik ePA (elektronische Patientenakte) FHIR client — Germany.
Phase 3 stub — full implementation pending gematik sandbox access.

References:
- https://www.gematik.de/anwendungen/e-patientenakte
- ISiK / KBV FHIR profiles
"""
from src.fhir.client import FHIRClient
from src.health_profile.schemas import HealthProfileData
from src.config import get_settings


class GematikEPAClient(FHIRClient):
    """FHIR client for German ePA via gematik IDP. Phase 3 — stub only."""

    async def get_authorization_url(self, state: str) -> str:
        raise NotImplementedError(
            "gematik ePA integration is Phase 3. "
            "Awaiting gematik test environment access."
        )

    async def exchange_code(self, code: str, state: str) -> dict:
        raise NotImplementedError("gematik ePA integration is Phase 3.")

    async def fetch_patient_profile(self, access_token: str, patient_id: str) -> HealthProfileData:
        raise NotImplementedError("gematik ePA integration is Phase 3.")
