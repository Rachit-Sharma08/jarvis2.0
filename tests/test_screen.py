"""Screen dekhne wala tool — ffmpeg/OpenRouter kabhi sach me nahi chalta.

`_grab` aur `_ask` fake se badalte hain. Yahan sirf command ka shape, har
error ka saaf jawab, temp file ka delete hona, aur gatekeeper ka faisla check
hota hai.
"""
import os
import subprocess
import sys
import tempfile
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config  # noqa: E402
import tools  # noqa: E402
from core import directreply  # noqa: E402
from gatekeeper import nocards, rules  # noqa: E402
from tools import screen  # noqa: E402

FAILED = []


def check(name, got, want):
    if got == want:
        print(f"  OK   {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL {name} -> got {got!r}, want {want!r}")


class Res:
    def __init__(self, code=0):
        self.returncode = code


def grab_ok(path):
    Path(path).write_bytes(b"png")
    return Res(0)


def grab_boom(exc):
    def run(path):
        raise exc
    return run


def main():
    real_ask, real_grab = screen._ask, screen._grab
    print("SCREEN: screenshot ka shape")
    seen = []

    def fake_run(cmd, **kw):
        seen.append((cmd, kw))
        return Res(0)

    real_run, screen.subprocess.run = screen.subprocess.run, fake_run
    try:
        screen._grab("x.png")
    finally:
        screen.subprocess.run = real_run
    cmd, kw = seen[0]
    check("gdigrab", "gdigrab" in cmd, True)
    check("ek frame", "1" in cmd[cmd.index("-frames:v") + 1], True)
    check("scale width config se",
          ("scale=%d:-1" % screen.config_vision.SCREEN_MAX_WIDTH) in cmd, True)
    check("shell=False", kw.get("shell"), False)
    check("ffmpeg path config se", cmd[0], screen.config_vision.FFMPEG_EXE)

    print("SCREEN: jawab ek line")
    check("newline saaf", screen._one_line("  Chrome khula hai\n do tab "), "Chrome khula hai do tab")
    check("400 char limit", len(screen._one_line("a" * 900)), 400)

    print("SCREEN: har raasta ek saaf line")
    screen._grab = grab_ok
    screen._ask = lambda b64, q: "  Screen par Chrome khula hai.  "
    out = screen.screen_look("kya hai")
    check("kaam hua", out, "Screen par Chrome khula hai.")
    check("temp png delete", os.path.exists(os.path.join(tempfile.gettempdir(),
                                                        "jarvis_screen.png")), False)

    asked = []
    screen._ask = lambda b64, q: asked.append(q) or "theek"
    screen.screen_look("ye error kya hai")
    check("sawaal aage gaya", asked[-1], "ye error kya hai")

    screen._grab = grab_boom(FileNotFoundError())
    check("ffmpeg nahi", "ffmpeg nahi mila" in screen.screen_look(""), True)

    screen._grab = grab_boom(subprocess.TimeoutExpired("ffmpeg", 25))
    check("grab timeout", "Screenshot nahi ban paya" in screen.screen_look(""), True)

    screen._grab = lambda p: Res(1)
    check("grab fail", "Screenshot nahi bana" in screen.screen_look(""), True)

    print("SCREEN: model ki galtiyan")
    saved_key = config.OPENROUTER_API_KEY
    screen._grab = grab_ok
    screen._ask = real_ask
    config.OPENROUTER_API_KEY = ""
    try:
        check("key na ho", "OpenRouter key chahiye" in screen.screen_look(""), True)
    finally:
        config.OPENROUTER_API_KEY = saved_key

    def http_boom(b64, q):
        raise urllib.error.HTTPError("u", 429, "slow", None, None)

    screen._ask = http_boom
    check("http 429", "HTTP 429" in screen.screen_look(""), True)

    def net_boom(b64, q):
        raise urllib.error.URLError("no net")

    screen._ask = net_boom
    check("net down", "Internet/model se baat nahi" in screen.screen_look(""), True)

    screen._ask = lambda b64, q: ""
    check("khaali jawab", "kuch saaf nahi bataya" in screen.screen_look(""), True)
    check("temp png delete (error ke baad bhi)",
          os.path.exists(os.path.join(tempfile.gettempdir(), "jarvis_screen.png")), False)

    print("SCREEN: registry + gatekeeper")
    screen._ask, screen._grab = real_ask, real_grab
    check("TOOLS me", "screen_look" in tools.TOOLS, True)
    check("question optional", tools.TOOL_OPTIONAL["screen_look"], {"question": ""})
    check("visible", "screen_look" in tools.visible(), True)
    check("spec me optional", "screen_look(question?)" in tools.spec(), True)
    check("risk ASK (privacy)", rules.decide("screen_look", {"question": "x"})[0], config.ASK)
    check("nocards allow", nocards.resolve_ask("screen_look", {"question": "x"}),
          (nocards.ALLOW, None))
    check("direct reply (doosra LLM call nahi)", "screen_look" in directreply.DIRECT_TOOLS, True)
    check("prompt me rule", "screen_look(question)" in
          __import__("brain.prompt", fromlist=["build"]).build("p", True), True)


with __import__("tests.datasafe", fromlist=["isolated_data"]).isolated_data():
    main()

if FAILED:
    print(f"{len(FAILED)} test fail: {FAILED}")
    sys.exit(1)
print("Screen look test pass.")
