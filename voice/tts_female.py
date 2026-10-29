"""Female voice-id ALLOWLIST. Dono mode ki awaaz female honi chahiye.

Live gender detection nahi hai (udhar se gender nahi aata). Isliye config me
allowlist hai: jo id isme nahi, us provider ko chhod diya jaata hai aur agle
par chala jata hai. Agar koi id galat (male) aa rahi ho to bhi aisa hi hoga —
male awaaz bolna possible hi nahi.

Nayi female voice id istemal karne se pehle yahan add karo (gender check karke).
"""

from log_setup import get_logger

log = get_logger("voice_female")

# ---- ElevenLabs (Multilingual v2) ----
# Dono verified female voice ids. Groq/voice ke liye: ElevenLabs ki voice
# library me "female" filter laga kar confirm kiye gaye the.
ELEVENLABS_FEMALE = {
    "JBFqnCBsd6RMkjVDRZzb",   # Jarvis
    "XrExE9yKIg1WjnnlVkGX",   # Prabh
}

# ---- Cartesia ----
# Voices API se gender=feminine + hi-IN accent wali. Id guess nahi ki jaati.
CARTESIA_FEMALE = {
    # "Skylar - Friendly Guide" (feminine, standard-hindi accent)
    "db6b0ed5-d5d3-463d-ae85-518a07d3c2b4",
}

# ---- Edge (Microsoft neural voices) ----
# 'Swara' female hai (female prefix). Dono mode abhi Swara.
EDGE_FEMALE = {
    "hi-IN-SwaraNeural",
    "hi-IN-MadhurNeural",
}

ALLOW = {
    "elevenlabs": ELEVENLABS_FEMALE,
    "cartesia": CARTESIA_FEMALE,
    "edge": EDGE_FEMALE,
}


def is_allowed(provider: str, voice_id: str) -> bool:
    """Voice id female allowlist me hai?"""
    if not voice_id:
        return False
    return voice_id in ALLOW.get(provider, set())


def next(ids):
    """Allowlist ka pehla id (test/diagnostic ke liye). Khaali = ''."""
    for value in ids:
        return value
    return ""


def check(provider: str, voice_id: str) -> str:
    """'' = theek hai. Nahi to chhodne ka saaf reason (UI/log dono ke liye)."""
    if not voice_id:
        return f"{provider}: voice id nahi hai"
    if not is_allowed(provider, voice_id):
        log.error("%s voice id %s allowlist me nahi — skip", provider, voice_id[-6:])
        return f"{provider}: voice id female list me nahi (…{voice_id[-4:]})"
    return ""


def allowlist_report() -> dict:
    """Debug/diagnostic ke liye — id ke aakhri 4 akshar hi (poori id nahi)."""
    return {
        name: sorted(v[-4:] for v in ids) for name, ids in ALLOW.items()
    }