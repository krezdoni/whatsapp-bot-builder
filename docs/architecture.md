# Technical Architecture — EU Health AI Companion

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER DEVICES                                 │
│   Threema App          WhatsApp App          Browser (PWA)          │
└───────┬───────────────────────┬─────────────────────┬───────────────┘
        │ E2E encrypted          │ E2E encrypted        │ HTTPS/TLS
        ▼                        ▼                      ▼
┌───────────────┐  ┌─────────────────────┐  ┌────────────────────────┐
│ Threema       │  │ Sinch Conversation   │  │ Next.js PWA            │
│ Gateway       │  │ API (EU region)      │  │ (Hetzner, Germany)     │
│ (EU servers)  │  │                      │  │                        │
└───────┬───────┘  └──────────┬──────────┘  └──────────┬─────────────┘
        │ webhook               │ webhook                 │ REST API
        └───────────────────────┴─────────────────────────┘
                                │
                                ▼
        ┌───────────────────────────────────────────────────┐
        │            FastAPI Backend (Hetzner, DE)           │
        │                                                   │
        │  ┌──────────────┐  ┌──────────────┐              │
        │  │  Messaging   │  │   Auth /     │              │
        │  │  Dispatcher  │  │   Consent    │              │
        │  └──────┬───────┘  └──────────────┘              │
        │         │                                         │
        │  ┌──────▼───────┐  ┌──────────────┐              │
        │  │  LLM Client  │  │ Health Profile│              │
        │  │  (local)     │  │ CRUD + Encrypt│              │
        │  └──────┬───────┘  └──────┬────────┘              │
        │         │                  │                       │
        └─────────┼──────────────────┼───────────────────────┘
                  │                  │
        ┌─────────▼──────┐  ┌────────▼──────────────────────┐
        │ vLLM Server    │  │ PostgreSQL + pgcrypto          │
        │ Med42-70B      │  │ (Hetzner Frankfurt, DE)        │
        │ (Hetzner A100) │  │ Field-level Fernet encryption  │
        └────────────────┘  └───────────────────────────────┘
```

**Data residency guarantee**: All health data is processed and stored within EU. No PHI leaves the EU at any point. The only external calls are to Threema Gateway (EU), Sinch EU-region endpoints, and MitID/Sundhedsjournalen (DK government infrastructure).

---

## Components

### 1. Messaging Abstraction Layer (`src/messaging/`)

Provider-agnostic interface. All adapters implement:

```python
class MessagingAdapter(ABC):
    async def send_message(recipient_id: str, text: str) -> None
    def parse_inbound(payload: dict) -> InboundMessage
    def verify_webhook(payload: bytes, headers: dict) -> bool
```

**Threema adapter** (`threema.py`): Calls Threema Gateway REST API. Threema provides end-to-end encryption and stores messages only on EU servers. No user PII touches Threema's servers without E2E encryption.

**WhatsApp adapter** (`whatsapp.py`): Calls Sinch Conversation API (EU region endpoint: `eu.conversation.api.sinch.com`). Requires prior `whatsapp_meta_exposure` consent. Message content is E2E encrypted via WhatsApp protocol; metadata (sender, timestamp, length) is accessible to Meta.

**Message dispatcher** (`dispatcher.py`): Receives normalised `InboundMessage`, loads conversation history (last 10 turns), injects health profile context into LLM prompt, stores both messages encrypted, sends reply.

### 2. FastAPI Backend (`src/api/`)

Python 3.11, FastAPI 0.115, asyncpg for async PostgreSQL.

Routes:
| Prefix | Purpose |
|--------|---------|
| `/auth` | Registration, JWT issuance, consent management |
| `/messaging` | Webhooks (Threema, WhatsApp), PWA chat endpoint |
| `/profile` | Health profile read/write |
| `/documents` | File upload, OCR (Phase 2) |
| `/fhir` | FHIR OAuth flows (Denmark Phase 2, Germany Phase 3) |
| `/gdpr` | Data export (Art. 20), account deletion (Art. 17) |

### 3. Health Profile (`src/health_profile/`)

Schema includes: conditions, medications, allergies, providers, vaccinations, lab_history, appointments, notes.

All PHI fields are stored encrypted:
- **Encryption**: Fernet (AES-128-CBC + HMAC-SHA256) from `cryptography` library
- **Key derivation**: HKDF-SHA256 per user — compromising one user's key does not expose others
- **Master key**: 32-byte Fernet key stored as environment variable (production: HSM or Vault)
- Plain-text columns: only non-PHI (UUIDs, timestamps, enum flags)

### 4. LLM Layer (`src/llm/`)

**Model**: Med42-70B (M42 Health, Llama 3 base, medical fine-tune) or Meditron-70B (EPFL/Yale)
**Serving**: vLLM on Hetzner dedicated GPU instance (A100 or H100)
**API**: OpenAI-compatible `/v1/chat/completions` endpoint — no code changes needed to swap models

Health profile is injected into the system prompt as a compact summary (conditions, medications, allergies). Full history is not injected to avoid hitting context limits.

**Medical boundary enforcement** (in `prompts.py`):
1. System prompt explicitly states the assistant provides information, not advice
2. Post-processing keyword scan — if response touches clinical topics, appends a disclaimer
3. System prompt enforces Fernbehandlungsverbot (no treatment recommendations)

### 5. FHIR Integration (`src/fhir/`)

**Denmark** (Phase 2): `SundhedsjournalClient` — MitID OAuth 2.0 + PKCE → Sundhedsjournalen FHIR R4. Fetches: Condition, MedicationStatement, AllergyIntolerance, Immunization, Observation (lab).

**Germany** (Phase 3): `GematikEPAClient` — gematik IDP → ePA FHIR endpoint. Stub pending gematik sandbox access.

### 6. Auth & Consent (`src/auth/`)

**JWT**: HS256, 60-minute expiry, issued at registration.

**Consent**: Granular per-purpose records in `user_consents` table. Separate consent required for:
- `profile_storage`: health data stored on EU servers
- `fhir_pull`: pulling records from national health system
- `document_processing`: OCR + LLM extraction on uploaded documents
- `messaging_channel`: receiving messages via chosen channel
- `whatsapp_meta_exposure`: acknowledgment of WhatsApp metadata exposure to Meta

Each consent record includes: type, granted/revoked, consent text version, timestamp, IP.

---

## Database Schema

```
users
  id (UUID PK)
  phone_number_enc (TEXT encrypted)
  threema_id_enc   (TEXT encrypted)
  messaging_channel (TEXT)
  mitid_sub_enc    (TEXT encrypted)
  gematik_sub_enc  (TEXT encrypted)
  whatsapp_consent_timestamp (TIMESTAMP)
  data_retention_years (INT default 2)
  is_deleted (BOOL)

user_consents
  id, user_id, consent_type, granted, consent_text_version, ip_address, timestamp

health_profiles
  id, user_id
  conditions_enc, medications_enc, allergies_enc, providers_enc,
  vaccinations_enc, lab_history_enc, appointments_enc, notes_enc
  fhir_last_synced_at, updated_at

messages
  id, user_id, direction, provider, content_enc, timestamp

documents
  id, user_id, filename_enc, document_type,
  ocr_text_enc, extracted_data_enc, uploaded_at
```

---

## Infrastructure (Production Target)

| Component | Provider | Location |
|-----------|----------|----------|
| Backend + DB | Hetzner Dedicated | Frankfurt, DE |
| LLM GPU server | Hetzner Dedicated (A100/H100) | Frankfurt, DE |
| Object storage (docs) | Hetzner Object Storage | Frankfurt, DE |
| CDN / TLS termination | Hetzner LB + Let's Encrypt | EU |

**No AWS, GCP, Azure, or any US-based infrastructure for health data.**

---

## Open Decisions

1. **Model**: Med42-70B vs Meditron-70B — benchmark on 50 health Q&A samples before Phase 2 launch.
2. **OCR**: Tesseract (free, on-server, good for Danish/German) vs Cloud Vision EU region (higher accuracy, ~0.001 EUR/page). Recommend Tesseract first, add Cloud Vision as fallback.
3. **Denmark vs Germany first**: Denmark recommended — Sundhedsjournalen has cleaner developer documentation and test environment.
4. **State store for OAuth**: Currently in-memory dict (dev only). Replace with Redis before Phase 2.
