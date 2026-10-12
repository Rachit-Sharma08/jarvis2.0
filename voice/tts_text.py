"""Bolne se pehle text saaf karna — link, emoji, markdown, aur lambi line.

`voice/tts.py` se alag is liye ki ye **koi provider, network ya cache nahi**
chuaata — sirf string par kaam. Pure functions, is liye test me bina awaaz ke
chal jaate hain (`tests/test_voice_tts.py`).

Teen kaam:

- `clean()` — link/emoji/markdown hatao (warna awaaz ajeeb lagti hai).
- `clip()` — free quota bachaane ke liye shuruaat boli jaaye.
- `clip_answer()` — brain ka poora jawab HUD par rehta hai, **awaaz** chhoti.
  Vaakya ke end par kata jaata hai, beech se nahi.

`tts.py` inhe re-export karta hai, is liye production code aur test dono ab bhi
`tts.clean()` hi likhte hain (ek hi raasta).
"""

import re

import config

URL_RE = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U0001F1E6-\U0001F1FF\u2190-\u21FF\u2600-\u27BF\u2B00-\u2BFF\uFE0F]"
)
MARKDOWN_RE = re.compile(r"[*#`>_]+")
SPACES_RE = re.compile(r"[ \t]+")


def clean(text: str) -> str:
    """Awaaz se pehle text saaf karta hai: link, emoji aur markdown hatao."""
    text = URL_RE.sub(" ", text or "")
    text = EMOJI_RE.sub(" ", text)
    text = MARKDOWN_RE.sub(" ", text)
    text = SPACES_RE.sub(" ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def clip(text: str, limit: int = None) -> str:
    """Free quota bachaane ke liye sirf shuruaat boli jaati hai."""
    limit = limit or config.TTS_MAX_CHARS
    if len(text) <= limit:
        return text
    cut = text[:limit]
    if " " in cut:
        cut = cut[: cut.rfind(" ")]
    return cut.strip()


def clip_answer(text: str, limit: int = None) -> str:
    """Bade jawab ki **awaaz** chhoti — vaakya ke end par, beech se nahi.

    `clip()` kaat-ta hai, is liye usse sunne me ajeeb lagta hai. Yahan pehle
    `limit` ke andar ka aakhri **poora vaakya** (`. ` / `? ` / `! ` / `। `)
    dhoonda jaata hai. Sirf tab jab koi vaakya na mile (bahut lambe ek vaakya)
    tab `clip()` par hafta — beech se katna behtar hai pura sunne se.

    Sirf **awaaz** ke liye: HUD par brain ka poora jawab rehta hai
    (`config.VOICE_ANSWER_MAX_CHARS`)."""
    limit = limit or config.VOICE_ANSWER_MAX_CHARS
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    head = text[:limit]
    best = -1
    for mark in (". ", "? ", "! ", "। "):
        best = max(best, head.rfind(mark))
    # Sirf ek teen shabd ka vaakya na rahe - warna jawab ka matlab hi nahi bacha.
    if best > limit // 3:
        return head[:best + 1].strip()
    return clip(text, limit)


def sentences(text: str) -> list:
    """Text ke poore vaakya. Beech se nahi kaate — `. ` / `? ` / `! ` / `। `
    par hi. Shuru ke whitespace chhodi jati hai, khaali vaakya nahi."""
    out, buf = [], ""
    for ch in str(text or ""):
        buf += ch
        if ch in ".?!।" and not buf.rstrip().endswith((".", "!", "?", "।")):
            continue
        if ch in ".?!।" and len(buf.strip()) > 1:
            out.append(buf.strip())
            buf = ""
    if buf.strip():
        out.append(buf.strip())
    return out


def voice_answer(text: str, max_sentences: int = None) -> str:
    """Awaaz ke liye jawab — **pehle 1-2 poore vaakya** (KAAM 4).

    `clip_answer()` 220 **char** par kaatta tha, jo beech se vaakya tod sakta
    tha (awaaz mein beech ka tukda sunai deta hai). Yahan pehle vaakya
    **pura** hota hai; agar 1-2 vaakya me char limit aa jaaye to
    `clip_answer()` par hafte hain.

    HUD par **poora** jawab rehta hai — ye sirf awaaz ke liye hai.
    """
    limit = config.VOICE_ANSWER_MAX_CHARS
    want = max_sentences if max_sentences is not None else config.VOICE_SENTENCES
    text = (text or "").strip()
    if not text:
        return ""
    parts = sentences(text)
    if len(parts) > 1:
        head = " ".join(parts[:max(1, want)])
        if len(head) <= limit:
            return head                     # pura vaakya — sabse accha
        return clip_answer(head, limit)     # limit aayi to wahi purana kaat
    return clip_answer(text, limit)
