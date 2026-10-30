"""Telegram bot ke settings — phone se Jarvis tak (Tab jaisa).

Token `.env` me `JARVIS_TELEGRAM_TOKEN` hai (kabhi commit/log me nahi).

**Owner-only:** `JARVIS_TELEGRAM_CHAT` me apni chat id. Khaali ho to bot koi
command nahi chalata — sirf chat id bata deta hai, taaki wo `.env` me daal sako.
Ye jaan-boojh kar hai: bot internet par khula hota hai, bina allowlist ke koi
bhi PC chala sakta tha.
"""

import os

TOKEN = os.getenv("JARVIS_TELEGRAM_TOKEN", "").strip()
CHAT_ID = os.getenv("JARVIS_TELEGRAM_CHAT", "").strip()
# Telegram ka limit 4096 char hai; thoda neeche rakha.
TELEGRAM_MAX_CHARS = 3500
# Long-poll: itni der server intezaar karta hai (naya message aate hi laut aata hai).
TELEGRAM_POLL_SECONDS = int(os.getenv("JARVIS_TELEGRAM_POLL", "25") or 25)


def has_telegram() -> bool:
    """Token hai? (Chat id na ho to bot chalta hai par command nahi.)"""
    return bool(TOKEN)
