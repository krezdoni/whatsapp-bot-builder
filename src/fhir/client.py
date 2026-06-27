"""
Base FHIR R4 client. Subclassed per country.
Uses fhirclient for resource parsing; raw HTTP for OAuth token exchange.
"""
from abc import ABC, abstractmethod
import httpx

from src.health_profile.schemas import HealthProfileData


class FHIRClient(ABC):
    """Abstract FHIR client. Country-specific subclasses handle auth flows."""

    @abstractmethod
    async def get_authorization_url(self, state: str) -> str:
        """Return the OAuth2 authorization URL to redirect the user to."""

    @abstractmethod
    async def exchange_code(self, code: str, state: str) -> dict:
        """Exchange auth code for tokens. Returns dict with access_token, patient_id, etc."""

    @abstractmethod
    async def fetch_patient_profile(self, access_token: str, patient_id: str) -> HealthProfileData:
        """
        Fetch and normalise all relevant FHIR resources for the patient.
        Returns a HealthProfileData populated from FHIR resources.
        """

    async def _fhir_get(
        self, fhir_base: str, resource_type: str, access_token: str, params: dict | None = None
    ) -> dict:
        url = f"{fhir_base}/{resource_type}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                url,
                headers={"Authorization": f"Bearer {access_token}"},
                params=params or {},
            )
            resp.raise_for_status()
            return resp.json()
