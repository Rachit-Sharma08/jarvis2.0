"""Webhook sender (safe POST)."""
import json
import urllib.request


def webhook_post(url: str = '', data: str = '') -> str:
    if not url or not str(url).strip():
        return 'URL kya hai?'
    try:
        payload = data or '{}'
        req = urllib.request.Request(str(url).strip(), data=payload.encode('utf-8'), headers={'Content-Type': 'application/json', 'User-Agent': 'Jarvis/1.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            return 'ok'
    except Exception as exc:
        return f'err: {type(exc).__name__}'
