"""Simple RSS reader (local, read-only)."""
import json
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import config

DATA_DIR = Path(config.BASE_DIR) / 'data'
RFILE = DATA_DIR / 'rss_feeds.json'


def _load():
    try:
        if RFILE.exists():
            with open(RFILE, 'r', encoding='utf-8') as f:
                d = json.load(f)
            return d if isinstance(d, list) else []
    except Exception:
        pass
    return []


def _save(items):
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(RFILE, 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def rss_add(url: str = '') -> str:
    if not url or not str(url).strip():
        return 'URL kya hai?'
    items = _load()
    items.append({'id': len(items) + 1, 'url': str(url).strip()})
    _save(items)
    return 'RSS feed add ho gaya'


def rss_list() -> str:
    items = _load()
    if not items:
        return 'Koi feed nahi'
    return '\n'.join(f"#{x['id']}: {x['url']}" for x in items)


def rss_read(limit: int = 5) -> str:
    items = _load()
    if not items:
        return 'Koi feed nahi'
    out = []
    for x in items[:2]:
        try:
            req = urllib.request.Request(x['url'], headers={'User-Agent': 'Jarvis/1.0'})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = r.read().decode('utf-8', errors='ignore')
            root = ET.fromstring(data)
            for item in root.findall('.//item')[:limit]:
                title = item.findtext('title') or ''
                link = item.findtext('link') or ''
                out.append(f'- {title}\n  {link}')
            break
        except Exception:
            continue
    return '\n\n'.join(out) if out else 'Kuch nahi mila'
