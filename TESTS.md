# Tests (22 suites)

Sab suite **standalone** hain — ek-ek karke ya loop me. Koi **asli API call nahi**
karta, koi **khatarna command** nahi chalta, aur key ki zarurat nahi padti.
Har file ke end me "OK" / "Saare ... test pass." aana chahiye aur **exit code `0`**.

Kuch suite aakhir me `print("FAIL:", FAILED if FAILED else "koi nahi")` likhte hain —
usme `"FAIL:"` sirf static label hai. **`koi nahi` matlab sab pass**. asli faisla exit
code se lena, text se nahi.

## Sab ek saath

```powershell
cd D:\prabh
$fail = @()
Get-ChildItem tests\test_*.py | ForEach-Object {
  .\.venv\Scripts\python.exe $_.FullName
  if ($LASTEXITCODE -ne 0) { $fail += $_.Name }
}
if ($fail) { "FAILED: $($fail -join ', ')" } else { "SUITE GREEN" }
```

Ek-ek karke:

```powershell
.\.venv\Scripts\python.exe tests\test_gatekeeper.py
.\.venv\Scripts\python.exe tests\test_pool.py
```

## Kaunsa suite kya check karta hai

| Suite | Kya check karta hai |
|---|---|
| `test_basic.py` | Chat, mode switching, brain, logging |
| `test_security.py` | Token, origin, host, dangerous endpoints |
| `test_paths.py` | Traversal, case, 8.3 naam, junction, drive root |
| `test_gatekeeper.py` | SAFE/ASK/BLOCKED cases, path tricks, mode parity |
| `test_gatekeeper_approval.py` | Card hash, single use, 60s timeout, kill switch, rate limit, log masking |
| `test_tools.py` | 10 tools (temp folder me), 20 KB limit, scrubbed env, timeout |
| `test_tool_routes.py` | Tool endpoints, CSP, UI source safety |
| `test_prompt_strict.py` | LLM JSON strict validation + duplicate key reject |
| `test_engine_tools.py` | 5-step loop, ASK/BLOCKED, kill switch, mode parity |
| `test_engine_detail.py` | Tool output aur confirm card ki masking |
| `test_pool.py` | Tier failover, 404 par agla model, khaali jawab + 1 retry, 429 par retry nahi |
| `test_pool_billing.py` | Cooldown, Retry-After, credits lock, daily quota, free-only, sab-fail message |
| `test_probe.py` | Strict JSON probe, 2-call limit, 8s latency gate, 24h cache |
| `test_brain_status.py` | `/brain/status` route, Host/Origin/token, key masking, `.env` ignored |
| `test_voice.py` | Voice chain, limit, mode naam, `/stt` `/tts` |
| `test_voice_tts.py` | TTS chain order, clean(), teeno fail par saaf error |
| `test_voices_female.py` | Female allowlist, male id skip, Edge Swara fallback |
| `test_stt_guard.py` | Duration <600ms, silence/khaali, non-Hindi/English script reject |
| `test_fixes_r1.py` | Round-1 fixes (modes, events, engine) |
| `test_fixes_r1_brain2.py` | Brain fallback + health rules |
| `test_fixes_r1_ui.py` | UI fixes, dedupe, labels |
| `test_fixes_r1_voice.py` | Cartesia payload, female chain, khaali text block |

## Naya test likhte waqt

- **Asli network call kabhi nahi.** `httpx`/provider hamesha fake.
- Khatarna command **sirf faisle se** test karo (executor mock) — chalao mat.
- File tools **sirf temp folder** me.
- Bade suite ko 2-3 file me todo — har file `<200` lines rahe.
- Hindi print ho to pehli line ke baad `sys.stdout.reconfigure(encoding="utf-8")`
  zaroori hai, warna Windows console par `UnicodeEncodeError` aata hai.
- Route test me `app.routes` par `.path` mat pakdo (lazy router object);
  `app.openapi()["paths"]` use karo.
- Mile hue helpers `tests/poolhelp.py` me hain — naya pool test wahin se import kare.
