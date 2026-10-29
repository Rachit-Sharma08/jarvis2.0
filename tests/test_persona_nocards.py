"""Persona + prompt ki no-cards safai (P-2b-2b) - sirf source check, koi mock nahi."""
import sys
from pathlib import Path
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

from brain import prompt
from core import memory, modes
from datasafe import isolated_data

FAILED = []
BASE = 3256  # P-2b-2b se pehle naapa gaya prompt (tools ON, khaali memory)
MAX_GROW = 2050  # P-2b-2b + E-1 (+106) + E-2 (+50); 28-Oct: media suite (play_media
# + media_control + vscode_terminal - spec 3 line + rules 5 line) (+335);
# 29-Oct: close_app name='all' (+142); personal profile (remember/forget spec
# 2 line + rules 2 line) (+314); Avenger persona (Sir/protocol/profile lines) (+230);
# Hinglish jawab rule (+98).
# 29-Oct: parivaar/care persona (raat chup, "Pepper ko phone karu") (+280)
# + search rule "link mat maango, web_search chalao" (+56).


def check(name, got, want):
    if got == want:
        print(f"  OK   {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL {name} -> got {got!r}, want {want!r}")


def main():
    memory.MEM.clear()  # context na lagta hai warna lambai badalti rehti hai
    persona = modes.persona_for("sunday")
    built = prompt.build(persona, True)
    check("persona: 'UI button' gayi", "UI button" in persona, False)
    check("persona: purani 'confirm sirf' line gayi", "Har tool confirm sirf" in persona, False)
    check("persona: kaam seedha karo", "Kaam seedha karo" in persona, True)
    check("persona: ALLOW dabao mana hai", ("ALLOW dabao" in persona) and ("mat kaho" in persona), True)
    check("persona: samajh na aaye to puchho", "guess mat karo" in persona, True)
    check("prompt: file-naam wali line", "file ka naam do" in built, True)
    check("prompt: workspace zikr", "workspace" in built, True)
    check("prompt: absolute path mana", "absolute path" in built, True)
    check(f"prompt lambai base+{MAX_GROW} me", len(built) <= BASE + MAX_GROW, True)
    print(f"\npersona {len(persona)} chars | prompt {len(built)} chars | base {BASE}")
    if FAILED:
        print(f"{len(FAILED)} test fail: {FAILED}")
        sys.exit(1)
    print("Persona/prompt no-cards test pass.")


if __name__ == "__main__":
    # memory.MEM.clear() asli data/memory.json mita deta tha - ab tmp par.
    with isolated_data():
        main()
