"""STT guard: chhoti recording, khamoshi ke phrases, galat script.

Ye filter recording se PEHLE (duration) aur Whisper ke BAAD (text) dono par
lagta hai. Romanized Hinglish jaan-boojh kar chalta hai.
"""

import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from voice.stt_guard import (MIN_DURATION_MS, bad_duration, guard_text,
                              is_silence_phrase, script_ok)

FAILED = []


def check(name, got, want):
    if got == want:
        print(f"  OK   {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL {name} -> got {got!r}, want {want!r}")


print("DURATION (600ms rule)")
check("600ms theek hai", bad_duration(600), "")
check("601ms theek hai", bad_duration(601), "")
check("599ms chhoti", bool(bad_duration(599)), True)
check("1ms chhoti", bool(bad_duration(1)), True)
check("0ms chhoti", bool(bad_duration(0)), True)
check("bada time theek", bad_duration(30000), "")
check("negative galat", bad_duration(-5), "duration negative hai")
check("text hi galat", bool(bad_duration("abc")), True)
check("khaali matlab theek", bad_duration(""), "")
check("missing matlab theek", bad_duration(None), "")
check("600 rule value", MIN_DURATION_MS, 600)

print("KHAMOSHI KE PHRASES")
for phrase in ("Thank you", "Thanks for watching!", "Subtitles by Amara.org",
               "Please subscribe", "Bye.", "[Music]", "silence", "inaudible"):
    check(f"reject: {phrase[:26]}", bool(is_silence_phrase(phrase)), True)

print("ASLI BAAT REJECT NAHI HONI CHAHIYE")
for text in ("namaste, kya haal hai", "notes.txt khol do", "Prabh kaun hai",
             "aaj mausam kaisa hai bhai", "batao shaam ko kya karna hai"):
    check(f"chalte: {text[:26]}", is_silence_phrase(text), "")

print("SCRIPT CHECK")
check("devanagari theek", script_ok("नमस्ते"), "")
check("romanized theek", script_ok("namaste kya haal hai"), "")
check("dono mila theek", script_ok("prabh नमस्ते kaise ho"), "")
check("khaali", script_ok(""), "khaali text")
check("sirf space", script_ok("   "), "khaali text")
check("sirf number", script_ok("12345"), "sirf number/symbol")
check("sirf ek akshar", script_ok("a"), "sirf ek akshar")
check("sirf punctuation", script_ok("!!! ???"), "khaali text")
check("cyrillic reject", bool(script_ok("привет как дела")), True)
check("arabic reject", bool(script_ok("مرحبا كيف حالك")), True)
check("chinese reject", bool(script_ok("你好怎么样")), True)
check("japanese reject", bool(script_ok("こんにちは元気ですか")), True)
check("thai reject", bool(script_ok("สวัสดีครับ")), True)
check("greek reject", bool(script_ok("γεια σου πώς είσαι")), True)
check("korean reject", bool(script_ok("안녕하세요 어때요")), True)
check("cyrillic+latin reject", bool(script_ok("hello привет")), True)
check("number+akshar, number hi zyada", script_ok("1234 5678 90 12 34 ab"), "zyada number")
check("thoda number theek", script_ok("mera number 42 hai"), "")

print("POORA GUARD")
check("khaali text reject", guard_text(""), "khaali text")
check("sirf space reject", guard_text("   "), "khaali text")
check("khamoshi reject", guard_text("Thank you"), "khamoshi ka phrase")
check("galat script reject", bool(guard_text("こんにちは元気ですか")), True)
check("normal hindi jaare", guard_text("namaste, prabh"), "")
check("normal devanagari jaare", guard_text("नमस्ते, आज मौसम कैसा है"), "")
check("command jaari", guard_text("desktop ka folder khol do"), "")

print()
if FAILED:
    print(f"{len(FAILED)} fail: {FAILED}")
    sys.exit(1)
print("Saare stt_guard test pass.")