# EU Health AI Companion

A personal health AI assistant for the European market. Users interact via Threema (EU-native) or WhatsApp. The AI maintains a persistent, encrypted health profile per user, answers health questions, helps interpret lab results, and drafts communications for doctor visits.

Built GDPR-first with no US data touchpoints for health data.

**Target markets:** Denmark and Germany.

---

## Architecture Overview

```
User (Threema / WhatsApp)
        │
        ▼
Messaging Abstraction Layer
        │
        ▼
FastAPI Backend (EU server, Hetzner Frankfurt)
    ├── Health Profile (PostgreSQL + field-level encryption)
    ├── LLM Client (vLLM → Med42-70B, local GPU)
    ├── FHIR Client (Sundhedsjournalen DK / gematik ePA DE)
    └── Consent & Auth (JWT + granular consent store)
        │
        ▼
Next.js PWA (onboarding, consent flows, profile review)
```

See [`docs/architecture.md`](docs/architecture.md) for full detail.

---

## Quick Start (Development)

### Prerequisites
- Docker & Docker Compose
- Python 3.11+

### Setup

```bash
cp .env.example .env.local
# Fill in values in .env.local

docker compose up -d         # starts PostgreSQL + backend
# OR run backend locally:
pip install -r requirements.txt
alembic upgrade head
uvicorn src.api.main:app --reload --port 8000
```

### Run tests

```bash
pytest tests/ -v
```

---

## Project Structure

```
src/
├── api/             FastAPI app + routes
├── auth/            JWT auth + granular consent management
├── fhir/            FHIR clients (Sundhedsjournalen DK, gematik ePA DE)
├── health_profile/  Profile schema, CRUD, field-level encryption
├── llm/             Local LLM client (vLLM OpenAI-compatible endpoint)
└── messaging/       Abstraction layer + Threema + WhatsApp adapters

docs/
├── architecture.md        Full technical architecture
├── dpia.md                GDPR Data Protection Impact Assessment
└── medical-boundary.md    What the system will and won't do

app/          Next.js PWA (onboarding, consent, profile review)
migrations/   Alembic database migrations
tests/        Test suite
```

---

## Regulatory Compliance

- **GDPR Art. 9**: Health data is special category. Granular consent per processing purpose.
- **Germany Fernbehandlungsverbot**: Information only — no treatment recommendations.
- **EU MDR**: Stays on information side; no clinical decision support.
- **Data residency**: All health data processed and stored in EU (Hetzner Frankfurt).

See [`docs/medical-boundary.md`](docs/medical-boundary.md) and [`docs/dpia.md`](docs/dpia.md).

---

## MVP Phases

- **Phase 1** (weeks 1–3): Messaging layer, FastAPI, consent, local LLM, health profile
- **Phase 2** (weeks 4–6): MitID OAuth, Sundhedsjournalen FHIR, document upload + OCR
- **Phase 3** (weeks 7–10): WhatsApp via Sinch, gematik ePA
- **Phase 4**: GDPR deletion, audit logging, medical guardrails audit
