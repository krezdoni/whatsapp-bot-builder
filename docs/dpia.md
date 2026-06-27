# Data Protection Impact Assessment (DPIA)
## EU Health AI Companion

**Document version**: 0.1 (draft — requires DPO review before launch)  
**GDPR basis**: Article 35 — Processing likely to result in high risk (health data + systematic profiling)  
**Last updated**: 2026-06-27  
**Owner**: Data Controller (company TBD)

---

## 1. Description of Processing

### 1.1 Nature of Processing
- Collection, storage, and processing of health data (special category, Art. 9 GDPR)
- AI-assisted interpretation of health records and documents
- Integration with national health record systems (Sundhedsjournalen DK, ePA DE)
- Messaging via Threema (EU-native) or WhatsApp (metadata accessible to Meta/US)
- OCR and LLM extraction from uploaded health documents

### 1.2 Scope
- Individual users (natural persons, patients)
- Health data: conditions, medications, allergies, vaccinations, lab results, appointments
- Communication metadata: message timestamps, channel type (not message content, which is encrypted)
- Identity data: phone number or Threema ID (encrypted at rest)

### 1.3 Context
A practicing surgeon in Denmark (clinical founder) operates this service. The product provides health information, not medical advice. Target markets: Denmark and Germany.

### 1.4 Purposes
| Purpose | Legal Basis | Data Used |
|---------|-------------|-----------|
| Health profile storage | Art. 9(2)(a) — explicit consent | All health data |
| FHIR pull from national records | Art. 9(2)(a) — explicit consent | MitID/gematik OAuth token, FHIR resources |
| Document OCR + extraction | Art. 9(2)(a) — explicit consent | Uploaded document content |
| AI-assisted health Q&A | Art. 9(2)(a) — explicit consent | Health profile, conversation history |
| Messaging via chosen channel | Art. 6(1)(b) — contract performance | Phone / Threema ID, message content |
| GDPR compliance (Art. 17, 20) | Art. 6(1)(c) — legal obligation | All data |

---

## 2. Necessity and Proportionality

### 2.1 Necessity
Each processing activity is necessary to deliver the service: health context injection requires storing health data; FHIR pull requires OAuth identity; messaging requires a channel identifier.

### 2.2 Proportionality
- Minimum data collected: no diagnoses generated (user-provided or FHIR-sourced conditions stored, not inferred)
- Retention: user-defined (default 2 years), full deletion on request
- Encryption: all PHI encrypted at rest with per-user derived keys
- No profiling for advertising or third-party sharing

### 2.3 Data Minimisation Measures
- Conversation history limited to last 10 messages for LLM context
- FHIR pull is opt-in; profile can be populated manually instead
- Document originals not stored after extraction (Phase 2 design decision — TBD)

---

## 3. Risks Identified

| Risk | Severity | Likelihood | Mitigation |
|------|----------|------------|------------|
| Unauthorized access to health data | High | Low | Field-level encryption, JWT auth, EU data residency |
| Data breach via LLM API | High | Low | LLM runs locally on EU server; no PHI sent to external LLM |
| Metadata exposure via WhatsApp | Medium | High (if user chooses WA) | Explicit consent with detailed disclosure; Threema offered as alternative |
| Inaccurate health information leading to harm | High | Low | Medical boundary enforcement; disclaimers; not a medical device |
| FHIR token interception | High | Low | PKCE flow; tokens stored encrypted; short-lived access tokens |
| Unlawful access by law enforcement | Medium | Low | EU servers; data not held by US companies |
| AI model bias or hallucination | Medium | Medium | Medical model (Med42/Meditron); post-processing checks; user directed to doctor |
| Data retention beyond user intent | Low | Low | Configurable retention; scheduled deletion jobs |
| Insecure document upload | Medium | Low | 20 MB limit; file type validation; encryption before storage |

---

## 4. Risk Mitigation Measures

### 4.1 Technical Measures
- **Encryption**: Fernet (AES-128-CBC + HMAC) with HKDF-derived per-user keys
- **Data residency**: All processing on Hetzner Frankfurt (Germany, EU)
- **No external LLM**: Med42-70B / Meditron-70B served locally via vLLM
- **JWT authentication**: Short-lived tokens (60 min), HTTPS-only
- **Audit logging**: All data access logged (Phase 4)
- **Rate limiting**: Anti-abuse measures (Phase 4)

### 4.2 Organisational Measures
- Granular consent per processing purpose, versioned consent texts
- Medical boundary document maintained and enforced in code
- Staff access to production data restricted and logged
- Incident response procedure (to be documented before launch)
- DPO to be appointed before launch (required: Art. 37(1)(c) — systematic large-scale health data processing)

### 4.3 User Rights Measures
- **Art. 15** (access): `/gdpr/export` endpoint returns all user data as JSON
- **Art. 17** (erasure): `/gdpr/delete-account` permanently deletes all PHI
- **Art. 20** (portability): Same export endpoint, JSON format
- **Art. 7(3)** (withdraw consent): `/auth/consent` PATCH endpoint per consent type
- **Art. 22** (automated decisions): No automated decisions with legal/significant effects; human always in the loop

---

## 5. WhatsApp Metadata Disclosure (Special Consideration)

Using WhatsApp creates a metadata trail accessible to Meta Platforms Inc. (US company), including:
- Sender phone number
- Message timestamps
- Message length (approximate)
- Frequency of messaging

**Message content is end-to-end encrypted and not accessible to Meta.**

Mitigation:
- WhatsApp is offered as a convenience tier alongside Threema (EU-pure alternative)
- Explicit consent screen (`whatsapp_meta_exposure`) with exact disclosure text stored in user record with timestamp and version
- Users can switch to Threema at any time
- Standard Contractual Clauses (SCCs) with Sinch for data transfer documentation

---

## 6. Consultation and Sign-off

Before launch, the following must be completed:

- [ ] DPO appointment and DPIA review
- [ ] Legal review of consent texts (DK and DE versions)
- [ ] Security penetration test of the API and encryption implementation
- [ ] Review of Threema Gateway DPA
- [ ] Review of Sinch DPA (incl. SCCs for WhatsApp path)
- [ ] Review of Sundhedsjournalen API DPA
- [ ] Registration with relevant DPA (Datatilsynet DK / BfDI DE) if required
- [ ] Incident response procedure documented
- [ ] Staff data processing training completed

---

## 7. Residual Risk Assessment

After mitigations, residual risk is assessed as **LOW** for the Threema path and **MEDIUM** for the WhatsApp path (due to US metadata exposure, accepted with explicit consent).

The processing may proceed provided the above sign-off checklist is completed before launch.

---

*This document must be reviewed annually and after any significant change to data processing activities.*
