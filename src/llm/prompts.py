"""
System prompts and post-processing rules for the health AI companion.

Medical boundary (non-negotiable):
- Provides health INFORMATION, not medical advice or diagnoses
- No treatment recommendations (Germany Fernbehandlungsverbot)
- Every response touching symptoms or conditions includes a disclaimer
- Encourages consulting a healthcare professional for clinical decisions
"""

SYSTEM_PROMPT_BASE = """You are a personal health information assistant operating in the European Union.
You help users understand their health records, interpret lab results, prepare questions for doctor visits, and find reliable health information.

CRITICAL BOUNDARIES — you must never cross these:
1. You provide health INFORMATION only. You do not provide diagnoses, medical advice, or treatment recommendations.
2. You do not tell users what medication to take, change, or stop.
3. You do not interpret symptoms as a diagnosis.
4. For any clinical decision, you direct the user to consult their doctor or healthcare provider.
5. In Germany: you do not make Fernbehandlung (remote treatment) recommendations under any circumstances.

LANGUAGE: Respond in the same language the user writes in. Support Danish (da), German (de), and English (en).

TONE: Warm, clear, and precise. You have clinical literacy — use it to explain things at the right level for the user without being condescending or overly technical.

DISCLAIMER: When discussing symptoms, conditions, lab results, or medication-adjacent topics, end your response with a brief, natural disclaimer directing the user to their doctor for clinical decisions."""

SYSTEM_PROMPT_WITH_PROFILE = """{base}

USER HEALTH PROFILE (for context — do not quote raw values back unless helpful):
{profile_summary}"""

DISCLAIMER_VARIANTS = [
    "For clinical decisions or if you have concerns about your health, please speak with your doctor.",
    "This information is for context only — your doctor is the right person to advise on your specific situation.",
    "Always check with your healthcare provider before making any changes to your treatment or medications.",
    "If you're worried about these results or symptoms, a conversation with your GP or specialist is the right next step.",
]

POST_PROCESSING_TRIGGER_KEYWORDS = [
    "symptom", "diagnos", "medic", "prescri", "treatment", "condition",
    "result", "lab", "blood", "pain", "dose", "tablet", "drug",
    "symptom", "symptomer", "diagnose", "behandling", "medicin",  # Danish
    "symptom", "diagnose", "behandlung", "medikament", "arznei",  # German
]


def build_system_prompt(profile_summary: str | None = None) -> str:
    if profile_summary:
        return SYSTEM_PROMPT_WITH_PROFILE.format(
            base=SYSTEM_PROMPT_BASE, profile_summary=profile_summary
        )
    return SYSTEM_PROMPT_BASE


def needs_disclaimer(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in POST_PROCESSING_TRIGGER_KEYWORDS)


def ensure_disclaimer(text: str, variant_index: int = 0) -> str:
    """Add a disclaimer if the response touches clinical topics and doesn't already have one."""
    disclaimer_markers = ["doctor", "healthcare", "læge", "lege", "arzt", "clinical", "provider"]
    if any(m in text.lower() for m in disclaimer_markers):
        return text  # already has a disclaimer
    disclaimer = DISCLAIMER_VARIANTS[variant_index % len(DISCLAIMER_VARIANTS)]
    return f"{text}\n\n_{disclaimer}_"


def summarise_profile_for_context(profile_data: dict) -> str:
    """Convert decrypted health profile to a compact context string for the system prompt."""
    parts = []
    if profile_data.get("conditions"):
        names = [c.get("name", "") for c in profile_data["conditions"] if c.get("status") == "active"]
        if names:
            parts.append(f"Active conditions: {', '.join(names)}")
    if profile_data.get("medications"):
        active = [m.get("name", "") for m in profile_data["medications"] if m.get("active")]
        if active:
            parts.append(f"Current medications: {', '.join(active)}")
    if profile_data.get("allergies"):
        subs = [a.get("substance", "") for a in profile_data["allergies"]]
        if subs:
            parts.append(f"Allergies: {', '.join(subs)}")
    if not parts:
        return "No profile data available yet."
    return "\n".join(parts)
