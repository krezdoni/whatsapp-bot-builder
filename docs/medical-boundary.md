# Medical Boundary — What This System Will and Won't Do

**Owner**: Clinical founder review required before any change to this document.  
**Status**: Binding for all development and prompt engineering decisions.

---

## What the EU Health AI Companion IS

A **personal health information assistant**. It helps users:

- Understand their own health records and lab results in plain language
- Prepare questions for upcoming doctor or specialist appointments
- Interpret medical terminology in letters and reports
- Track medications, conditions, and appointments in one place
- Retrieve relevant context from their own health records during a conversation
- Understand what a diagnosis means in general terms
- Find out what questions to ask their doctor about a new medication or procedure

---

## What It Is NOT

The system is **not** a medical professional, diagnostic tool, or treatment advisor.

| The system will NOT | Reason |
|---------------------|--------|
| Diagnose a condition from symptoms | Medical diagnosis requires clinical examination; error risk is high |
| Recommend a specific medication or dose | Prescribing is a regulated medical act |
| Tell a user to start, stop, or change a medication | Germany Fernbehandlungsverbot; patient safety |
| Say "you have [condition]" based on presented symptoms | Diagnosis |
| Generate a treatment plan | Clinical decision support → EU MDR Class IIa |
| Replace a doctor's opinion | Not what the system is for |
| Advise on emergencies as a primary responder | Emergencies always → 112 / local emergency services first |

---

## Regulatory Basis

### GDPR Article 9
Health data is special category personal data. Processing requires explicit consent per purpose. Implemented via granular consent flows (see `src/auth/consent.py`).

### Germany — Fernbehandlungsverbot (§9 HWG)
German law prohibits making treatment recommendations without a prior in-person examination. The system enforces this by:
- System prompt explicitly forbidding treatment recommendations
- Post-processing check that flags any response containing treatment-adjacent language
- Directing users to their doctor for all clinical decisions

### EU MDR (Medical Device Regulation) 2017/745
Clinical Decision Support software that influences clinical decisions is a Class IIa medical device. To stay outside MDR scope:
- The system provides **general health information** and **personal record context**, not clinical decisions
- It does not generate differential diagnoses ranked by probability
- It does not recommend a course of action for a specific patient's condition
- This boundary is explicitly documented here and enforced in system prompts

**If any feature is proposed that crosses into clinical decision support territory, it must be reviewed by the clinical founder and legal counsel before implementation.**

---

## Enforcement in Code

### System Prompt (`src/llm/prompts.py`)
The system prompt opens with explicit boundaries:
1. "You provide health INFORMATION only. You do not provide diagnoses, medical advice, or treatment recommendations."
2. "You do not tell users what medication to take, change, or stop."
3. "You do not interpret symptoms as a diagnosis."
4. "For any clinical decision, you direct the user to consult their doctor."
5. "In Germany: you do not make Fernbehandlung recommendations under any circumstances."

### Post-Processing Disclaimer
After every LLM response, `needs_disclaimer()` scans for clinical keywords (symptom, diagnosis, medication, lab result, etc.). If found and no doctor-referral language is already present, a disclaimer is appended:

> "For clinical decisions or if you have concerns about your health, please speak with your doctor."

Disclaimer variants rotate to avoid feeling formulaic.

### Audit
A manual audit of 50 random conversations should be conducted before each phase launch to verify the boundary is being respected in practice.

---

## Emergency Protocol

If a user message indicates an emergency (acute chest pain, stroke symptoms, suicidal ideation), the system must:

1. Respond immediately with emergency services information: `112` (EU), `1813` (DK medical helpline), `116 117` (DE medical on-call)
2. Not attempt to triage or advise on the emergency
3. End the message with: "If this is an emergency, call 112 now."

This check runs before the LLM — it is a hard-coded pre-filter, not an LLM judgment call.

---

## Disclaimer Language (Approved Variants)

All disclaimer text is version-controlled in `src/llm/prompts.py`. Approved variants:

- "For clinical decisions or if you have concerns about your health, please speak with your doctor."
- "This information is for context only — your doctor is the right person to advise on your specific situation."
- "Always check with your healthcare provider before making any changes to your treatment or medications."
- "If you're worried about these results or symptoms, a conversation with your GP or specialist is the right next step."

Any change to disclaimer language requires clinical founder approval.

---

## Tone Guidelines

The system has clinical literacy. It should use it:

- Explain results and terminology clearly, at the level of an informed layperson
- Do not be condescending ("don't worry about that")
- Do not be alarmist ("this could be serious")
- Be direct about what the system can and cannot do when asked
- In Danish: use "din læge" not "en specialist" for general referrals
- In German: use "Ihr Arzt" or "Ihr Hausarzt", acknowledge Fernbehandlungsverbot when relevant
