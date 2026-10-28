"""UI source-guard + khatarnak endpoint checks (test_tool_routes.py se 28-Oct aaye).

Koi server na chalta — sirf source text aur OpenAPI paths.
"""

import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config

FAILED = []


def check(name, got, want):
    if got == want:
        print(f"  OK   {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL {name} -> got {got!r}, want {want!r}")


def test_ui_uses_textcontent():
    print("UI SURAKSHA (source check)")
    ui = config.UI_DIR
    for name in ("app.js", "tools.js"):
        source = (ui / name).read_text(encoding="utf-8")
        check(f"{name}: innerHTML nahi", "innerHTML" in source, False)
        check(f"{name}: outerHTML nahi", "outerHTML" in source, False)
        check(f"{name}: insertAdjacentHTML nahi", "insertAdjacentHTML" in source, False)
        check(f"{name}: eval nahi", "eval(" in source, False)
    tools_js = (ui / "tools.js").read_text(encoding="utf-8")
    check("tools.js: textContent hai", "textContent" in tools_js, True)
    check("Allow/Deny par isTrusted check", "isTrusted" in tools_js, True)


def test_no_dangerous_endpoints():
    print("KHATARNAK ENDPOINT NAHI")
    from server.app import app

    paths = set(app.openapi()["paths"])
    check("/shell nahi", "/shell" in paths, False)
    check("/exec nahi", "/exec" in paths, False)
    check("/env nahi", "/env" in paths, False)
    check("/tool/confirm hai", "/tool/confirm" in paths, True)
    check("/tools/toggle hai", "/tools/toggle" in paths, True)
    check("/tools/cancel hai", "/tools/cancel" in paths, True)
    check("/stt voice bhi hai", "/stt" in paths, True)


if __name__ == "__main__":
    test_ui_uses_textcontent()
    test_no_dangerous_endpoints()
    print()
    if FAILED:
        print(f"{len(FAILED)} test fail: {FAILED}")
        sys.exit(1)
    print("UI guard + endpoint naqsha theek.")
