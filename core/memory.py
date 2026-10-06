"""Short-term conversation memory (local JSON)."""
import json
import os
from datetime import datetime
from pathlib import Path

import config

DATA_DIR = Path(config.BASE_DIR) / 'data'
MEM_FILE = DATA_DIR / 'memory.json'
SUM_FILE = DATA_DIR / 'memory_summary.txt'


class Memory:
    def __init__(self, max_turns: int = 12):
        self.max_turns = int(max_turns)
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._items = self._load()

    def _load(self):
        try:
            if MEM_FILE.exists():
                with open(MEM_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, list):
                    return data[-self.max_turns * 2:]
        except Exception:
            pass
        return []

    def _save(self):
        try:
            with open(MEM_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._items[-self.max_turns * 2:], f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def add(self, role: str, text: str):
        if not text:
            return
        self._items.append({'role': role, 'text': str(text)[:1000], 'ts': datetime.now().isoformat(timespec='seconds')})
        if len(self._items) > self.max_turns * 3:
            self._items = self._items[-self.max_turns * 2:]
        self._save()

    def context(self, max_turns: int | None = None) -> str:
        n = max_turns or self.max_turns
        items = self._items[-n:]
        parts = []
        try:
            if SUM_FILE.exists():
                with open(SUM_FILE, 'r', encoding='utf-8') as f:
                    s = f.read().strip()
                if s:
                    parts.append('[CONTEXT SUMMARY]\n' + s + '\n[END SUMMARY]')
        except Exception:
            pass
        if items:
            lines = ['[CONTEXT RECENT]']
            for it in items:
                lines.append(f"{it['role']}: {it['text']}")
            lines.append('[END CONTEXT]')
            parts.append('\n'.join(lines))
        return '\n\n'.join(parts) if parts else ''

    def clear(self):
        self._items = []
        try:
            if MEM_FILE.exists():
                os.remove(MEM_FILE)
        except Exception:
            pass


MEM = Memory()
