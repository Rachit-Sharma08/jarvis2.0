"""Ollama offline brain + SerpAPI search ka dhaancha (koi network call nahi).

Ollama pool ka **aakhri** provider hai — internet band ho to bhi Jarvis jawab de.
Yahan sirf config/entry check hota hai; asli jawab live test se dekha gaya tha.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config  # noqa: E402
from brain import pool_config  # noqa: E402
from brain import prompt  # noqa: E402
from tools import search  # noqa: E402

FAILED = []


def check(name, got, want):
    if got == want:
        print(f"  OK   {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL {name} -> got {got!r}, want {want!r}")


def main():
    print("OLLAMA: local last resort")
    check("enabled by default", config.OLLAMA_ENABLED, True)
    check("local URL", config.OLLAMA_BASE_URL, "http://127.0.0.1:11434/v1")
    names = [p["name"] for p in pool_config.POOL]
    check("pool me hai", "ollama" in names, True)
    check("sabse aakhir me", names[-1], "ollama")
    entry = pool_config.by_name()["ollama"]
    check("key bhari (pool skip na kare)", pool_config.has_key(entry), True)
    check("model wahi jo pull kiya", entry["model"], config.OLLAMA_MODEL)
    check("timeout sabse zyada (slow local)", entry["timeout"] >= 60, True)

    print("SERP: search tool model ko dikhta hai")
    check("web_search visible", "web_search" in __import__("tools").visible(), True)
    check("khaali query par sawaal", search.web_search(""), "Search query kya hai?")
    # Test `.env` nahi padhta (logsafe JARVIS_NO_DOTENV=1) — is liye key ka
    # asli hona live test se dekha gaya, yahan sirf "key na ho" ka raasta.
    saved = search.SERPAPI_KEY
    search.SERPAPI_KEY = ""
    check("key na ho to saaf baat", "SERPAPI_API_KEY" in search.web_search("delhi weather"), True)
    search.SERPAPI_KEY = saved
    check("prompt: link mat maango",
          "link/exact naam mat maango" in prompt.build("p", True), True)
    check("prompt: apni yaad se number/link nahi",
          "apni yaad se number/link" in prompt.build("p", True), True)


with __import__("tests.datasafe", fromlist=["isolated_data"]).isolated_data():
    main()

if FAILED:
    print(f"{len(FAILED)} test fail: {FAILED}")
    sys.exit(1)
print("Ollama + SerpAPI test pass.")
