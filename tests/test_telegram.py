"""Telegram bot — owner gate, jawab, aur error ka raasta.

**Koi asli Telegram call ya brain nahi:** `_call`/`ask` dono fake. Ye test
`data/` ko bhi nahi chhoota (engine kabhi chalta hi nahi, E-1b niyam).
"""

import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config_telegram
from server import telegram_bot as bot
from tests.wakecmdhelp import patch
from tests.wakehelp import check, finish

OWNER = "4242"


def update(chat, **msg):
    body = {"message": dict({"chat": {"id": chat}}, **msg)}
    return body


def run(upd, asked=None, voice=None):
    """`handle()` chalao; jo reply gaye wo wapas."""
    sent = []
    asked = asked if asked is not None else []

    def fake_ask(text):
        asked.append(text)
        return "haan Sir, ho gaya"

    with patch(config_telegram, "CHAT_ID", OWNER), \
            patch(bot, "ask", fake_ask), \
            patch(bot, "voice_text", voice or (lambda *_a: "")):
        got = bot.handle(upd, reply=lambda chat, text: sent.append((chat, text)))
    return got, sent, asked


print("OWNER GATE")
got, sent, asked = run(update(OWNER, text="time kya hua"))
check("owner ka text chala", got, "answered")
check("brain ko text wahi mila", asked, ["time kya hua"])
check("jawab owner ko gaya", sent, [(OWNER, "haan Sir, ho gaya")])

got, sent, asked = run(update("999", text="mere PC me file banao"))
check("ajnabi par koi command nahi", got, "not-owner")
check("brain chhua hi nahi", asked, [])
check("ajnabi ko apni chat id batai",
      "999" in (sent[0][1] if sent else ""), True)

with patch(config_telegram, "CHAT_ID", ""):
    got, sent, asked = run(update("999", text="format karo"))
check("allowlist khaali = koi command nahi", got, "not-owner")
check("allowlist khaali par brain nahi", asked, [])
check("owner() khaali par False", bot.owner("999"), False)

print("MESSAGE KE PRAKAAR")
check("updates bina message ignore", bot.handle({}, reply=lambda *_a: None), "ignore")
check("updates bina chat ignore",
      bot.handle({"edited_message": {"text": "x"}},
                 reply=lambda *_a: None), "ignore")

got, sent, asked = run(update(OWNER))
check("khaali message", got, "empty")
check("khaali par brain nahi", asked, [])

got, sent, asked = run(update(OWNER, voice={"file_id": "f1", "duration": 4}),
                       voice=lambda fid, dur: "whatsapp kholo")
check("voice note bhi chala", got, "answered")
check("voice ka text brain ko", asked, ["whatsapp kholo"])

got, sent, asked = run(update(OWNER, voice={"file_id": "f2", "duration": 2}),
                       voice=lambda *_a: "")
check("voice khaali -> brain nahi", got, "empty")
check("voice khaali par jawab nahi", sent, [])

print("ERROR")
def boom(_text):
    raise RuntimeError("network gaya")


with patch(config_telegram, "CHAT_ID", OWNER), patch(bot, "ask", boom):
    sent = []
    got = bot.handle(update(OWNER, text="kuch bhi"),
                     reply=lambda chat, text: sent.append((chat, text)))
check("crash par handle na toota", got, "error")
check("user ko saaf message", "Nahi ho paya" in (sent[0][1] if sent else ""), True)
check("jawab owner ko", sent[0][0] if sent else "", OWNER)

print("LAMBA JAWAB TUKDON ME")
calls = []
with patch(bot, "_call", lambda method, params=None, timeout=30:
           calls.append((method, params)) or {"ok": True}):
    bot.send(OWNER, "x" * (config_telegram.TELEGRAM_MAX_CHARS + 10))
check("sendMessage do baar", [c[0] for c in calls], ["sendMessage", "sendMessage"])
check("pehla tukda poora",
      len(calls[0][1]["text"]), config_telegram.TELEGRAM_MAX_CHARS)
check("doosra tukda bacha hua", len(calls[1][1]["text"]), 10)
check("chat id saath gaya", calls[0][1]["chat_id"], OWNER)

calls.clear()
with patch(bot, "_call", lambda method, params=None, timeout=30:
           calls.append((method, params)) or {"ok": True}):
    bot.send(OWNER, "   ")
check("khaali jawab par bhi ek message",
      len(calls[0][1]["text"]) > 0, True)

print("BOOL / TOKEN")
check("owner exact match", bot.owner(OWNER) is False, True)   # CHAT_ID abhi "" hai
with patch(config_telegram, "CHAT_ID", "77"):
    check("owner match", bot.owner(77), True)
    check("owner alag id", bot.owner(78), False)
check("token khaali par bot nahi", bot.start(), False)

print("PURANE MESSAGE DOBARA NAHI")
with patch(bot, "_call", lambda *_a, **_k: {"result": [{"update_id": 5}]}):
    check("aakhri id ke baad se shuru", bot._next_offset(), 6)
with patch(bot, "_call", lambda *_a, **_k: {"result": []}):
    check("koi update nahi = 0", bot._next_offset(), 0)
with patch(bot, "_call", lambda *_a, **_k: (_ for _ in ()).throw(OSError("net"))):
    check("net gira to 0 (phir try karega)", bot._next_offset(), 0)

finish("Telegram bot: owner-only, text/voice, error, lamba jawab.")
