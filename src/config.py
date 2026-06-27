from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.local", extra="ignore")

    # App
    app_env: str = "development"
    app_base_url: str = "http://localhost:8000"
    allowed_origins: str = "http://localhost:3000"

    # Database
    database_url: str = "postgresql+asyncpg://health_user:changeme@localhost:5432/health_db"

    # Encryption
    field_encryption_key: str  # Fernet key, required

    # JWT
    jwt_secret_key: str  # required
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # Local LLM
    llm_base_url: str = "http://localhost:8001/v1"
    llm_model: str = "Med42-70B"
    llm_max_tokens: int = 1024
    llm_temperature: float = 0.3

    # Threema
    threema_gateway_id: str = ""
    threema_gateway_secret: str = ""
    threema_private_key: str = ""

    # WhatsApp / Sinch
    sinch_app_id: str = ""
    sinch_app_secret: str = ""
    sinch_whatsapp_number: str = ""

    # FHIR — Denmark
    mitid_client_id: str = ""
    mitid_client_secret: str = ""
    mitid_redirect_uri: str = ""
    sundhedsjournalen_fhir_url: str = "https://api.sundhedsjournalen.dk/fhir/R4"

    # FHIR — Germany
    gematik_idp_url: str = ""
    gematik_client_id: str = ""
    epa_fhir_url: str = ""

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
