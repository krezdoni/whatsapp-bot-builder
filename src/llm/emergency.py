"""
Emergency keyword pre-filter — runs before the LLM, not instead of it.

If a user message contains acute emergency signals, we respond immediately
with emergency services contact info and do NOT send the message to the LLM.
This is a hard-coded safety net, not an LLM judgment call.

Covers: cardiac, stroke, overdose, self-harm, severe trauma.
"""

# (keyword, language hint) — checked case-insensitively
_EMERGENCY_PATTERNS: list[tuple[str, str]] = [
    # English
    ("chest pain", "en"), ("can't breathe", "en"), ("cannot breathe", "en"),
    ("heart attack", "en"), ("stroke", "en"), ("unconscious", "en"),
    ("not breathing", "en"), ("severe bleeding", "en"), ("overdose", "en"),
    ("kill myself", "en"), ("end my life", "en"), ("suicide", "en"),
    # Danish
    ("brystsmerter", "da"), ("kan ikke trække vejret", "da"), ("hjerteanfald", "da"),
    ("slagtilfælde", "da"), ("bevidstløs", "da"), ("selvmord", "da"),
    ("tage mit liv", "da"), ("overdosis", "da"), ("kraftig blødning", "da"),
    # German
    ("brustschmerzen", "de"), ("herzinfarkt", "de"), ("schlaganfall", "de"),
    ("bewusstlos", "de"), ("kann nicht atmen", "de"), ("selbstmord", "de"),
    ("überdosis", "de"), ("starke blutung", "de"), ("suizid", "de"),
]

EMERGENCY_RESPONSE = {
    "en": (
        "This sounds like a potential emergency. Please call **112** (EU emergency) immediately "
        "or have someone call for you.\n\n"
        "- Denmark medical on-call: **1813**\n"
        "- Germany medical on-call: **116 117**\n\n"
        "_If this is an emergency, call 112 now. Do not wait._"
    ),
    "da": (
        "Dette lyder som en potentiel nødsituation. Ring venligst **112** (nødopkald) med det samme "
        "eller få nogen til at ringe for dig.\n\n"
        "- Akutlæge (ikke-livstruende): **1813**\n\n"
        "_Hvis dette er en nødsituation, ring 112 nu. Vent ikke._"
    ),
    "de": (
        "Das klingt nach einem möglichen Notfall. Bitte rufen Sie sofort **112** (Notruf) an "
        "oder lassen Sie jemanden für Sie anrufen.\n\n"
        "- Ärztlicher Bereitschaftsdienst (nicht lebensbedrohlich): **116 117**\n\n"
        "_Bei einem Notfall: Rufen Sie jetzt 112 an. Warten Sie nicht._"
    ),
}


def check_emergency(text: str) -> str | None:
    """
    Returns an emergency response string if the text matches any emergency pattern,
    otherwise returns None. Call this before sending any message to the LLM.
    """
    lower = text.lower()
    for pattern, lang in _EMERGENCY_PATTERNS:
        if pattern in lower:
            return EMERGENCY_RESPONSE.get(lang, EMERGENCY_RESPONSE["en"])
    return None
