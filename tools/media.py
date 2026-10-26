"""YouTube gaana/video play + player control (Brave me).

- play_media: search se pehla video nikaal ke Brave me kholta hai (autoplay).
- media_control: YouTube keyboard shortcuts — forward/back 10s, play/pause, next/prev.

Keys sirf tab kaam karte hain jab YouTube tab focus me ho; is liye pehle
browser window ko foreground laate hain (`AppActivate`).
"""

import re
import urllib.parse
import urllib.request

from tools.apps import open_app
from tools.quick import _ps

_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
_VIDEO = re.compile(r'"videoId":"([A-Za-z0-9_-]{11})"')
_KEYS = {
    "forward": "l",       # +10s
    "back": "j",          # -10s
    "play_pause": "k",
    "next": "+n",         # Shift+N
    "prev": "+p",         # Shift+P
}

# Brave > Chrome > Edge > Firefox: jo pehla window wala mile use focus karo.
_FOCUS_PS = r"""
$ErrorActionPreference = 'SilentlyContinue'
foreach ($n in @('brave', 'chrome', 'msedge', 'firefox')) {
  $p = Get-Process -Name $n | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
  if ($p) {
    $shell = New-Object -ComObject WScript.Shell
    if ($shell.AppActivate($p.Id)) {
      Start-Sleep -Milliseconds 300
      $shell.SendKeys('%s')
      'ok'
      exit 0
    }
  }
}
'no-window'
"""


def _fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": _UA,
                                               "Accept-Language": "en-US,en;q=0.9"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        # ytInitialData page ke ~1 MB baad aata hai — 600 KB me videoId nahi milta.
        return resp.read(2_000_000).decode("utf-8", "replace")


def _first_video_id(html: str) -> str:
    match = _VIDEO.search(html or "")
    return match.group(1) if match else ""


def play_media(query: str) -> str:
    text = str(query or "").strip()
    if not text:
        return "Kya play karun? (gaane ka naam do)"
    text = text[:200]
    search = ("https://www.youtube.com/results?search_query="
              + urllib.parse.quote_plus(text))
    try:
        video = _first_video_id(_fetch(search))
    except Exception:
        video = ""
    if not video:
        open_app("brave", search)
        return f"'{text}' ka video nahi mila - Brave me search khol diya."
    watch = f"https://www.youtube.com/watch?v={video}"
    opened = open_app("brave", watch)
    if "nahi mila" in opened:
        return opened
    return f"Brave me '{text}' play kar raha hoon."


def _send_key(key: str) -> str:
    out = _ps(_FOCUS_PS % key, timeout=15).strip()
    return "ok" if out == "ok" else "no-window"


def media_control(action: str) -> str:
    name = str(action or "").strip().lower()
    key = _KEYS.get(name)
    if not key:
        return f"action ye ho sakta hai: {', '.join(_KEYS)}"
    if _send_key(key) != "ok":
        return "koi browser window nahi mili (pehle kuch play karo)."
    if name == "forward":
        return "10 second aage kar diya."
    if name == "back":
        return "10 second peeche kar diya."
    if name == "play_pause":
        return "play/pause kar diya."
    return "agla video laga diya." if name == "next" else "pichla video laga diya."
