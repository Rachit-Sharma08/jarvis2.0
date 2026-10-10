# JARVIS (D:\prabh) - Roadmap vs Reality, Mistakes, Free-Only Fix Plan

**Ye file owner (Rachit) ka brief hai — 2026-10-04 | Reader: opencode coding agent.**
Project ke andar hamesha ke liye yahin rehti hai. Iske baad ka plan isi file me
aayega (status update + naye task), taaki ek hi jagah se pata chale.

---

> **OPENCODE - PEHLE YE PADHO.** Ye file project ka AGENTS.md aur NEW_AGENT_BRIEF.md ko replace nahi karti. Pehle wo dono padho; ground rules wahin hain (127.0.0.1 only, file <=200 lines, ek hi raasta, textContent only, secret kabhi nahi, chhote step: test -> commit -> AGENTS.md update).
>
> 1) File lambi hai - poori ek saath mat padho. Section-wise padho (S1..S10).  2) Ek time par sirf ek task (T-xx).  3) Jahan status VERIFY hai, pehle code padh kar confirm karo; andaza mat lagao.  4) Naya package/provider bina owner se poochhe mat jodo (D-2).  5) Owner coding nahi jaanta: har baat simple Hinglish me samjhao.  6) Windows native PowerShell me kaam karo (WSL nahi) - tray, registry, mic Windows par hain.
>
> **Is file ko project me rakhne ka tareeka:** docs/ROADMAP_STATUS.md (Markdown twin). opencode.json ke instructions me poori file mat daalo - har request me context khayegi aur free quota (Groq 8,000 tokens/min) jaldi khatam hogi. Bas AGENTS.md me ek line likho: 'Roadmap planning se pehle docs/ROADMAP_STATUS.md ke relevant section padho.' Docs index (AGENTS.md section 14) me bhi naam jodo.

## S1. Scoreboard

**Kya mazboot hai:** security (127.0.0.1, token, mask), tools + gatekeeper + ALLOW card (roadmap ke RED tier se bhi sakht), voice loop (wake -> VAD -> STT -> brain -> TTS), always-on launcher. Stage 02 ka bada hissa aur Stage 03 ka lagbhag poora kaam ho chuka.

**Kya kamzor/adhoora hai:** saboot (20x hammer, metrics, false-trigger log), fast path (har cheez LLM se), offline fallbacks (TTS/STT/LLM), aur Stage 04-06 (automation, business, one-system) lagbhag shuru hi nahi.

**Brief ke 2 open items:** tray icon (section 6) aur PLAN-TRUST.md (D-3, owner confirm ke baad).

**Free-only haqeeqat (2026-10-04):** free LLM tiers ghat gaye (Gemini ~20 req/day Flash par, OpenRouter 50/day); Groq abhi sabse kaam ka. Har cloud hisse ka offline fallback chahiye (section 7).

| Stage | Items | DONE | PARTIAL | VERIFY | TODO |
|---|---|---|---|---|---|
| Stage 02 ACTIONS | 9 | 1 | 2 | 2 | 4 |
| Stage 03 VOICE | 15 | 8 | 2 | 2 | 3 |
| Stage 04 AUTOMATION | 8 | 0 | 3 | 0 | 5 |
| Stage 05 BUSINESS | 6 | 0 | 2 | 0 | 4 |
| Stage 06 ONE SYSTEM | 8 | 3 | 1 | 1 | 3 |
| TOTAL | 46 | 12 | 10 | 5 | 19 |

Status words: DONE = brief me saaf likha hai. PARTIAL = kuch hissa hai. VERIFY = brief khamosh hai, code padh kar confirm karo. TODO = nahi hai.

## S2. Reality check: roadmap Mac smart-room hai, project Windows PC hai

Roadmap (Stage 01 ke baad) ek **Mac** par chalne wale **smart room** ke liye likha hai: Broadlink IR se AC/projector, smart plugs/bulbs, launchd, macOS Keychain. Tumhara project **D:\prabh Windows PC par chalne wala local assistant** hai: PC tools, HUD, voice, tray, HKCU Run auto-start.

Isliye comparison 'idea ke hisaab se' hai, device ke hisaab se nahi: roadmap ka 'tool layer' = tumhare 10 PC tools; 'room' = tumhara PC; 'launchd' = HKCU Run + launcher.py; 'menu-bar app' = tray; 'Keychain' = .env. Room-device wale hisse (AC, projector, plugs) is repo me nahi hain - woh D-1 decision par rukte hain.

**Decision D-1 (owner, 4-Oct — BAAT KHATAM):** **A) PC-first final.** AC/TV/smart-room/hardware **permanently chhoda** — koi hardware/room task roadmap me nahi. Is roadmap ka "room" = **PC + phone** (phone ka scope S12 me).

## S3. Stage-by-stage status

Stage 01: codebase DONE, dev loop DONE (opencode), runtime = Windows PC, smart room = not in this repo (N/A, D-1).

### Stage 02 ACTIONS

| # | Roadmap item | Status | Now (per brief) | Next |
|---|---|---|---|---|
| 2.1 | Typed tools with named inputs | DONE | 10 PC tools in tools/ (get_time_date, system_info, list_dir, read_file, write_file, open_website, open_app, close_app, run_command, delete_to_trash). Room tools (ac.set etc.) not built - see D-1. | Keep. New tool only via: rules.py risk -> tools/ -> engine.run_tool() -> TOOLS.md -> test. |
| 2.2 | Adapters (one interface per device family) | PARTIAL | tools/ is one registry - fine for a PC. No adapter layer for room devices or work apps. | Make adapters only when a 2nd device family exists. Interface: name, call(args) -> result, health(). |
| 2.3 | One tool server (MCP, JSON-schema inputs) | TODO | Own path engine.run_tool() -> keeper.review() -> tools.execute() is used instead. Works, but not MCP. | OPTIONAL. Only if a 2nd front end needs it; then MCP must be a thin wrapper over engine.run_tool() (ek hi raasta). |
| 2.4 | Log every call: who, what, result, time taken | VERIFY | gatekeeper/audit.py + mask() exist. Brief does not say result and duration are logged for every call. | Read audit.py. Each line must have: ts, via, tool, masked args, verdict, ok/fail, duration_ms. (T-03) |
| 2.5 | Dry-run mode (log without acting) | TODO | Not mentioned in brief. | Add DRY_RUN to config_tools.py (+ config.py export, .env.example, describe(), test). (T-03) |
| 2.6 | Hammer test: every tool 20x, report failures | TODO | 52-test suite uses fakes; no 20x loop. | tests/test_tools_hammer.py with temp workspace + fakes. (T-04) |
| 2.7 | Safety tiers GREEN / AMBER / RED | PARTIAL | SAFE / ASK / BLOCKED in gatekeeper/rules.py; ALLOW only via UI button (AST test); 60 s auto-DENY; same-hash 409; 5 steps/request; 20 req/min; delete = Recycle Bin; .env/key files BLOCKED. RED side is stronger than roadmap. AMBER (per-tool rate cap, safe ranges) missing. | Add per-tool rate caps for allowed-but-risky tools (open_app, close_app, run_command). (T-03) |
| 2.8 | State model (what each device is doing now) | TODO | Only DesktopState (tray/HUD). No 'what did Jarvis last do' state. | Small in-memory last_result per tool. Low priority until hardware exists. |
| 2.9 | Verify after acting, retry once, be honest | VERIFY | Brain-pool retry rules are defined. For tools it is not stated. | Check open_app / close_app confirm the process really started/stopped; else say 'maine bheja, par confirm nahi hua'. (T-04) |

### Stage 03 VOICE

| # | Roadmap item | Status | Now (per brief) | Next |
|---|---|---|---|---|
| 3.1 | Mic input (single stream) | DONE | wake/audio.py is the only mic path (bug #1 fixed). | Keep. Guard G-1. |
| 3.2 | Wake word | DONE | Vosk offline (models/vosk-model-small-en-us-0.15). hello/hey/hlo/helo/hi/yo jarvis + jarvis; energy gate (battery 4.8% -> 0.9%); cooldown 1.5 s. | Roadmap suggests openWakeWord. Switch only if the false-trigger log (T-06) shows a problem. |
| 3.3 | End-of-speech detection (VAD) | DONE | numpy RMS VAD 0.010; pre-roll 0.6 s; silence 0.9 s; hangover 0.4 s; max 30 s. | Silero VAD is an optional free upgrade later. |
| 3.4 | Speech to text | DONE | Groq (cloud, free tier). | No offline fallback when quota ends. (T-08) |
| 3.5 | Fast path: rules first, LLM only when needed | TODO | Only sleep words are matched by rule; everything else goes to brain pool. | Rules router before brain/pool.ask(), but STILL through engine.run_tool() -> keeper. (T-05) |
| 3.6 | LLM brain with fallbacks | DONE | brain/pool.ask(): groq 120b -> gemini -> openrouter free -> groq_slow 20b -> nvidia; retry/429/402/404 rules. | Free-tier numbers changed in 2026 - refresh pool_config.py. (T-09) |
| 3.7 | Text to speech | DONE | voice/tts.py edge-tts + cache; answer clipped to 220 chars; HUD shows full text. | edge-tts has no SLA. Offline fallback (Piper or Kokoro). (T-08) |
| 3.8 | Speaker + interruptible (barge-in) | PARTIAL | desktop/playback.py plays audio. Barge-in not mentioned. | (T-07) Reuse the single mic stream - see bug #1. |
| 3.9 | Does not hear itself (echo) | VERIFY | Not mentioned in brief. | Check: is mic ignored/muted while speak() plays? Test with fake audio. (T-07) |
| 3.10 | Log wake scores / false triggers | TODO | No false-trigger counter. | Metrics file. (T-06) |
| 3.11 | Latency measured per stage | PARTIAL | Tuned by hand (ack peek 0.18 s) but no stage timing log. | (T-06) |
| 3.12 | Short spoken replies | DONE | VOICE_ANSWER_MAX_CHARS=220, clipped at sentence end. | Keep. |
| 3.13 | Tested on real speech (Hinglish, fan noise) | VERIFY | Wake phrases are English; sleep words are Hinglish. No noise test noted. | Manual live checklist, NOT in suite (rule 10). (T-06) |
| 3.14 | Push-to-talk fallback | TODO | Ctrl+Alt+S only opens HUD; text chat is the fallback. | Optional PTT hotkey through the same desktop/ path. |
| 3.15 | Sleep / privacy word (extra) | DONE | 'so jao' etc. closes HUD; mic keeps running; wake word wakes. | Beyond roadmap. Keep. |

### Stage 04 AUTOMATION

| # | Roadmap item | Status | Now (per brief) | Next |
|---|---|---|---|---|
| 4.1 | Context: time, system, weather, calendar, presence | PARTIAL | get_time_date, system_info (CPU/RAM/battery/disk), Delhi weather exist. Calendar, presence (idle/active), work state missing. | Idle time via Windows GetLastInputInfo (ctypes, free). Calendar via .ics or free Google Calendar API - later. |
| 4.2 | Event bus (time_is, battery_low, idle ...) | PARTIAL | events HUB exists but streams chat/tool events to /ws -> HUD. It is not a signal bus. | New small automation/ package. Do NOT overload HUB. (T-10) |
| 4.3 | Rule engine: IF event AND condition THEN tool calls | TODO | None. | Deterministic, tested, actions only via engine.run_tool(). (T-10) |
| 4.4 | 5 routines as readable YAML in git | TODO | None. | PC-version routines listed in T-11. PyYAML = new package, ask owner first. |
| 4.5 | Explain why an automation fired | TODO | None. | Every rule writes a 'because ...' line to log + HUD card. |
| 4.6 | Undo + manual override for every automation | TODO | None. | Each routine has an undo: section; tray item 'Automation OFF'. |
| 4.7 | Suggest-only first week | TODO | ALLOW-card machinery exists and can be reused. | SUGGEST mode: rule posts card 'karun?'; owner taps ALLOW. |
| 4.8 | LLM only for fuzzy requests | PARTIAL | LLM currently handles everything. | Comes free with T-05. |

### Stage 05 BUSINESS

| # | Roadmap item | Status | Now (per brief) | Next |
|---|---|---|---|---|
| 5.1 | Daily briefing | PARTIAL | Pieces exist (time, weather, stats). No composed briefing, no calendar/tasks. | (T-12) |
| 5.2 | Ask my files, answer with source | PARTIAL | read_file / list_dir work (privacy: file text goes to a free provider). No index, no sources shown. | Local index with sqlite3 FTS5 (stdlib, free). (T-13) |
| 5.3 | Drafts replies/reminders; owner approves before sending | TODO | ALLOW card exists. No draft tool. | Draft-only tool. Sending stays RED and never from chat/voice. (T-14) |
| 5.4 | Weekly report | TODO | None. | Build after 5.1 and 5.5. |
| 5.5 | Scoreboard: time saved per week | TODO | None. | Count briefings/automations run x estimated minutes. (T-15) |
| 5.6 | Work-app adapters (calendar.read, mail.draft, docs.search) | TODO | None. | One adapter per app, same interface as 2.2. |

### Stage 06 ONE SYSTEM

| # | Roadmap item | Status | Now (per brief) | Next |
|---|---|---|---|---|
| 6.1 | One orchestrator for voice, text, phone | DONE | Shared server/state.ENGINE; events tagged via=voice / text. | Keep. A phone entry needs a VPN (see 6.7). |
| 6.2 | Memory I can read and edit (plain files) | TODO | personas/ exists; no long-term preferences file noted. | memory/preferences.md (plain text) loaded into persona; owner can edit. (T-16) |
| 6.3 | Dashboard: success rate, latency, errors | TODO | HUD (3 columns) and /brain/status exist; no metrics view. | Needs T-06 first, then a HUD panel with textContent only. (T-17) |
| 6.4 | Always on with auto-restart | DONE | HKCU Run -> pythonw.exe D:\prabh\desktop\launcher.py; supervisor next_step(). | Keep. Never use -m in the Run key (bug #12). |
| 6.5 | Survives sleep / reboot unattended | VERIFY | Auto-start done. Sleep prevention + reboot soak test not mentioned. | (T-18) |
| 6.6 | Secure by default | DONE | 127.0.0.1 only; Host/Origin/token; CORS off; mask(); .env git-ignored; CSP script-src 'self'. | Keep. Optional later: Windows Credential Manager. |
| 6.7 | Many faces (tray, phone page, tablet) | PARTIAL | Tray + HUD + Desktop shortcut + Ctrl+Alt+S exist. Tray icon not visible (open bug). No phone page. | Fix tray first (section 6). Phone page only via a free VPN, never open ports. |
| 6.8 | Final test: one sentence = two actions | TODO | No reminder tool, no multi-intent handling. | Example: 'Focus mode on karo aur 6 baje report bhejne ka reminder do'. After T-10/T-11 add reminder tool (max 5 steps already enforced). |

## S4. Process mistakes and the right way

| # | What went wrong | Right way |
|---|---|---|
| M-1 | Roadmap aur project alag-alag raaste par chal pade. Roadmap = Mac + Broadlink smart room. Project = Windows PC assistant (D:\prabh). | Ek page ka scope decision likho (D-1). Roadmap ko 'concept map' maano, copy-paste plan nahi. PLAN.md me ek line likho kaunsa hissa lagu hai. |
| M-2 | Numbers 'feel' se tune hue (peek 0.18 s, chuppi 0.9 s, VAD 0.010) - koi log nahi jo saabit kare ki sahi hain. (Battery fix 4.8% -> 0.9% measured tha - wahi style baaki jagah bhi chahiye.) | T-06: har stage ka latency + wake score + false trigger JSONL me. Fir numbers data se badlo. |
| M-3 | Reliability ka saboot adhoora: 52 tests hain par sab fakes par; 20x hammer aur real-world smoke nahi. | Fakes suite me rakho (rule 10). Alag se tests/hammer (fakes) + owner ka manual live checklist (suite ke bahar). |
| M-4 | Bahar ke single points of failure: edge-tts (unofficial Microsoft endpoint, no SLA), Groq STT daily quota, free LLM tiers ghat rahe hain. | Har cloud hisse ka ek fallback: TTS -> Piper/Kokoro, STT -> faster-whisper, LLM -> local Ollama (last). |
| M-5 | Free-tier numbers code me purane ho sakte hain (Gemini ka free quota 2026 me kaafi ghata). | pool_config.py me har provider ke limits ke saath date likho; mahine me ek baar python -m brain.probe <p>; local daily counter. |
| M-6 | Wahi bug-classes baar baar: fake update bhoola, constant export bhoola, purana process, Windows encoding. | Section 5 ke guards (G-1..G-15) tests ki tarah add karo - ek baar likho, hamesha bachao. |
| M-7 | Har command LLM se ja raha hai - 'time kya hai' jaisa kaam bhi. Slow, quota aur battery kharch. | T-05 fast-path router (roadmap ka two-path idea). Fir bhi engine.run_tool() -> keeper ke through. |
| M-8 | Tray bug me Windows ko registry entry banane par majboor karne ki koshish (SHChangeNotify). Entry Explorer banata hai; hum force nahi kar sakte. Asli reason shayad icon add hi fail/hidden hai. | Section 6 ka order follow karo: pehle ^ me dekho, fir icon-exists check + re-add watchdog, fir hi registry (export -> ek value -> count compare). |

## S5. The 15 real bugs and the guards

| # | Bug | Class | Guard (T-02) |
|---|---|---|---|
| 1 | Doosra InputStream -> mic RMS zero (device busy) | Shared hardware | G-1: AST test - sounddevice.InputStream sirf wake/audio.py me. Barge-in bhi usi stream se. |
| 2 | miniaudio.decode_file bytes par MB dump | Wrong API | G-2: grep test - decode_file ban; sirf decode(). |
| 3 | sd.query_devices(kind='output') list nahi deta | API behaviour | G-3: ek wrapper device_list() (query_devices() + filter) + fake test. |
| 4 | bytes() int64 samples par gadbad | dtype | G-4: ek helper pcm16() = np.asarray(samples, '<i2'); test dtype + length. |
| 5 | speak() me return await bhoola -> nested coroutine -> awaaz chup | Async | G-5: test: result coroutine nahi hona chahiye; tests -W error::RuntimeWarning (never awaited). |
| 6 | TTS cache fail par bhi store -> 'nahi bola' repeat | Cache on failure | G-6: sirf tab cache jab audio bytes > 0 aur status ok; failing-fake test. |
| 7 | drain() peek ke baad -> wake goonj + command dono delete | Ordering | G-7: scripted audio queue test - command frames bachne chahiye. |
| 8 | Callback signature badla, fake update nahi -> trigger chup | Fake drift | G-8: contract test - inspect.signature(fake) == inspect.signature(real) (tests/*help.py). |
| 9 | config.py me constant bhoola -> 3 suite palat gaye | Export gap | G-9: test - config_*.py ka har UPPER constant config se import ho. |
| 10 | Split ke baad helper adhoora -> silent false pass | Refactor | G-10: split ke baad compileall + purane naam grep + suite; har test file kam se kam 1 assertion print kare. |
| 11 | .bat me raw ( ) -> cmd block toota | Windows batch | G-11: .bat lint test: no raw parens, CRLF, ASCII (rule 7). |
| 12 | Run key me -m -> cwd System32 -> app chup-chaap mari | Windows autostart | G-12: test - Run command string launcher.py par khatam, '-m' nahi. |
| 13 | Purana process chalta raha - code badalne ka asar nahi | Stale process | G-13: /brain/status me started_at; restart ke baad compare. Nayi suite se pehle purana process band. |
| 14 | Grid % + gap + padding -> overflow | CSS | G-14: CSS lint test - grid-template-columns me minmax(0, Nfr), % nahi. |
| 15 | PowerShell se UTF-8 file likhi -> double-encode | Encoding | G-15: files Python se likho (encoding='utf-8'); test mojibake pattern; .bat/log ASCII. |

## S6. Tray icon: correct diagnosis order

| Step | What | Detail |
|---|---|---|
| 1 | Pehle dekho, guess mat karo | Taskbar ke ^ (hidden icons) me icon dhundo. Windows 11 me naye exe path ka icon aksar ^ ke andar chhup jaata hai. Mil jaye to drag karke taskbar par daalo (ek baar). Bug closed. |
| 2 | Read-only check (registry badalna nahi) | PowerShell: Get-ChildItem 'HKCU:\Control Panel\NotifyIconSettings' / ForEach-Object { Get-ItemProperty $_.PSPath } / Select-Object ExecutablePath, IsPromoted . Dekho pythonw.exe ki entry hai ya nahi. |
| 3 | Icon add hua ya nahi - code me check | pystray NIM_ADD ek baar bhejta hai aur result check nahi karta. Ek chhota watchdog: Explorer se pucho icon hai ya nahi (Shell_NotifyIconGetRect, ctypes) - nahi hai to icon dobara add karo. Pehle 1 min har 3 s, fir har 30 s. Ye pattern community project ai-quota-tray (PR #19, 2026-09-30) me dikha - copy mat karo, idea lo. |
| 4 | Ek hi interpreter pin karo | Launcher hamesha D:\prabh\.venv ka pythonw.exe chalaye (Store/py launcher wala nahi). Wrong interpreter se tray silently headless ho jaata hai (clawdmeter-daemon v1.0.1 ka sabak). |
| 5 | Tab hi registry (rule 13 ke hisaab se) | Entry bani ho to hi IsPromoted=1 us ek entry par. Pehle: reg export 'HKCU\Control Panel\NotifyIconSettings' backup\notify_before.reg -> ek value -> count compare -> proof. Entry nahi bani to registry me nayi entry khud mat likho. |
| 6 | Aakhri raasta (brief ka option b) | Launcher ka child python.exe + CREATE_NO_WINDOW. Sirf step 1-5 fail hone par. |

## S7. Free-only stack (checked 2026-10-04)

### S7.1 Brain providers

| Provider | Free limits found | Use in Jarvis |
|---|---|---|
| Groq gpt-oss-120b (T1) | 30 req/min, 1,000 req/day, 8,000 tokens/min, 200,000 tokens/day - per organisation (ek source ne 2026-09-14 ko measure kiya). Har model ka alag bucket. Whisper STT: 2,000 req/day. | Already T1. Prompt chhota rakho - asli limit tokens/min hai. groq_slow 20b = doosra bucket. |
| OpenRouter ':free' models | 20 req/min. 50 req/day jab tak $10 lifetime credit nahi kharide; uske baad 1,000/day. Yaani sach-much free = 50/day. | Sirf emergency fallback. |
| Gemini (AI Studio free) | Google ab fixed free numbers print nahi karta; Sept 2026 ke third-party sources: Flash models ~20 req/day, Flash-Lite ~500 req/day. Free-tier prompts Google product improvement me use ho sakte hain. | Flash-Lite model use karo. Private file text yahan mat bhejo. Apne AI Studio dashboard me asli quota dekho. |
| Cerebras (naya, optional) | Community lists: ~30 req/min, ~14,400 req/day, ~1M tokens/day, free me 8K context cap. | OpenAI-compatible, openai_pool.py me fit. Naya provider = owner se poochho. |
| Cloudflare Workers AI | 10,000 neurons/day (community list). | Low priority, optional. |
| Ollama (local) | Koi quota nahi; PC ki CPU/RAM/disk lagti hai; quality model size par. | Aakhri offline fallback. Owner approval + disk check. |
| NVIDIA build | Credits kat-te hain (brief ke mutabik). | Aakhir me hi rakho. |

### S7.2 Paid thing -> free alternative

| Item | Free alternative | Note |
|---|---|---|
| Dev agent (Claude Code, paid) | opencode - open source, apni key lao (BYOK). Already use ho raha hai. | OpenCode Zen free models ki list badalti rehti hai; 2026-10-03 se kuch users ko 'free tier can only be used from within OpenCode' error (GitHub issue #52907). Isliye opencode me apni Groq/OpenRouter key main provider rakho, Zen ko bonus maano. Docs Windows par WSL recommend karte hain, par Jarvis ko native Windows chahiye (tray, registry, mic) - D:\prabh me PowerShell se chalao. |
| Brain (Claude API, paid) | Groq / OpenRouter free / Gemini Flash-Lite / Cerebras / Ollama local - table 7.1. | Free limits tezi se badalte hain. Dated limits pool_config.py me. |
| Speech to text | Groq Whisper (free, 2,000 req/day) abhi; fallback faster-whisper (local, CPU int8, built-in Silero VAD filter). | faster-whisper naya package - owner se poochho. |
| Text to speech (cloud voice, paid) | edge-tts abhi (free). Offline fallback: Piper (tez, CPU) ya Kokoro-82M (Apache 2.0, behtar quality, CPU par near real-time). | edge-tts Microsoft endpoint par nirbhar hai, no SLA; pehle kabhi hafton tak block hua tha (community mention). Hindi voice ki availability fallback chunne se pehle check karo. |
| Wake word | Vosk (done). Optional: openWakeWord - pre-trained 'hey jarvis' model hai; Windows par default ONNX. | Sirf tab badlo jab false-trigger log kharab dikhaye. |
| End-of-speech | numpy RMS (done). Optional Silero VAD (free). | Optional. |
| Tool server (MCP) | MCP khud free/open standard hai. | Optional; thin wrapper only. |
| Scheduling | APScheduler (free) ya Windows Task Scheduler. Auto-start HKCU Run (done). | Naya package = owner se poochho. |
| State / memory | sqlite3 (Python stdlib) + plain Markdown/YAML files. | Koi naya package nahi (YAML ko chhod kar). |
| Secrets (macOS Keychain) | Windows par .env (git-ignored) rakho. Optional: Windows Credential Manager (keyring library). | Roadmap ka Keychain Mac-only hai. |
| Smart-room (Broadlink, plugs) | Software free: python-broadlink, Home Assistant. Hardware paid hai. | **Chhoda gaya (D-1 = A, 4-Oct).** Koi room/hardware task nahi — sirf PC + phone. |
| Phone access | Sirf **USB ADB** (platform-tools, free) — Wi-Fi ADB ya VPN nahi (D-2, 4-Oct). | P-01 (S12), T-01 ke baad. |
| Dashboard | Existing HUD + JSONL/sqlite3 metrics. | Koi paid tool nahi chahiye. |

## S8. Ordered tasks

| ID | Task | How | Done when |
|---|---|---|---|
| D-1 | ~~Scope decide karo (owner)~~ **4-Oct: A FINAL** | A) PC-first chuna gaya. AC/TV/smart-room/hardware **permanently chhoda** gaya — koi bhi naya hardware/room kaam nahi. Is roadmap ka "room" = **PC + phone**. | **Ho gaya.** Na AC/TV/buying ka koi task nahi. |
| D-2 | ~~Naye packages/providers ki permission~~ **4-Oct: sirf ADB** | Sirf **Google platform-tools (adb)** allowed hai (phone control ke liye). Piper/Kokoro/faster-whisper/Cerebras/Ollama **abhi nahi**; baaki har naya package/provider pehle owner se poochhna hai (AGENTS rule 2/8). | **Ho gaya (4-Oct).** P-01 me sirf adb use hoga; adb ke alawa koi package nahi bina poochhe. |
| D-3 | PLAN-TRUST.md (brief item 2) | Baad me, owner se confirm karke - bina poochhe shuru nahi. | Owner confirm. |
| T-01 | Tray icon fix | Section 6 ke steps 1-6 order me. Registry **sirf padho** (GetRect is PC par kaam nahi karta - live proof). | **4-Oct: ASLI BUG mila - `run_detached(setup=...)` par pystray `visible=True` khud nahi karta** (`_base.py:395` - `setup` diya to sirf `setup(icon)` chalta hai). `_on_setup` sirf log karta tha → icon invisible → `NIM_ADD` chala (registry entry banti thi) par shell render nahi karta. Fix: `_on_setup` me `icon.visible = True`. Live proof (UIA se taskbar padh kar): pehle overflow me kuch nahi, fix ke baad `Jarvis - band` promoted tray me. `IsPromoted=1` bhi likha tha (backup ke saath) par usse koi fark nahi padha - wajah yeh nahi thi. **4-Oct: OWNER NE CONFIRM KIYA - icon taskbar me dikh raha hai. Task poora.** |
| T-02 | Guards G-1..G-15 (sirf tests) | Section 5 ke guards. Behaviour mat badlo. TESTS.md me rows. | Suite green; har guard ek purani bug ko pakad sake (temporarily tod kar dekho). |
| T-03 | Action log + dry-run + AMBER caps | audit.py me ts/via/tool/verdict/ok/duration_ms; DRY_RUN setting; per-tool rate cap. | Har tool call ek masked log line banata hai; DRY_RUN me kuch execute nahi hota. |
| T-04 | Tool hammer (20x) + verify-after-act | tests/test_tools_hammer.py; open_app/close_app ke baad process confirm. | Har SAFE tool 20/20 pass ya failure detect+report. |
| T-05 | Fast-path rules router | time/date, system_info, open_website/app, sleep words rules se. engine.run_tool() -> keeper.review() bypass NAHI. | 'time kya hai' ~1 s ke aas-paas bina LLM; ASK wale kaam phir bhi card dikhayein. |
| T-06 | Metrics + live checklist | Per-stage latency, wake score, false-trigger counter (ASCII JSONL). Owner ke liye 10-line manual checklist. | Ek hafte ka data; false trigger/day ginti me. |
| T-07 | Echo check + barge-in | Pehle verify: speak() ke dauraan mic ignore? Fir barge-in usi single stream se. | Bolte waqt Jarvis khud ko trigger nahi karta; beech me bolne par ruk jaata hai. |
| T-08 | Offline fallbacks | voice/tts.py me fallback (Piper/Kokoro) - TTS ka ek hi darwaza. Fir STT fallback. | Internet band karke 'Jarvis' bol sake (limited offline mode). |
| T-09 | Brain pool free-tier refresh | pool_config.py: limits + date; Gemini -> Flash-Lite ya neeche; daily counter; (D-2 ke baad) Cerebras/Ollama. | python -m brain.probe har provider par; 429 par agla provider bina crash. |
| T-10 | Signal bus + rule engine (suggest-only) | automation/ package; time, battery, idle signals; action sirf engine.run_tool(). | Rule fire -> card 'karun?' -> ALLOW par hi chale; 'kyun' line log me. |
| T-11 | 5 PC routines | 1 Good morning (time + Delhi weather + battery). 2 Focus (apps band karne se pehle ASK). 3 Low battery <=20% alert. 4 Idle 10 min -> sleep mode. 5 Good night -> din ka summary + sleep. Sab ka undo. | 14 din bina manual fix; har ek ka undo chalta hai. |
| T-12 | Daily briefing | Existing time/weather/stats ko ek spoken+HUD summary me jodo. | Roz ek baar bina galti. |
| T-13 | Notes search with source | sqlite3 FTS5 local index; jawab ke saath file name. | Jawab me source dikhe; index local rahe. |
| T-14 | Draft-only tool | Reply/reminder drafts; bhejna RED aur sirf UI ALLOW se. | Zero message bina approval. |
| T-15 | Scoreboard | Briefing/automation count x estimated minutes. | Weekly number HUD par. |
| T-16 | Readable memory file | memory/preferences.md; persona me load; owner edit kar sake. | Preference badli to agla jawab badle. |
| T-17 | Dashboard panel | Success rate, latency, errors (textContent only). | 7-din success rate dikhe. |
| T-18 | Sleep/reboot soak | Run ke dauraan PC sleep roko (Windows API) ya watchdog; reboot test. | Reboot ke baad bina haath lagaye live. |
| **P-01** | **Phone control SPIKE (spike = chhota paroda, poora feature nahi)** | **Sirf adb** (D-2). USB se phone jodo; `adb devices` se device ka model/OS pata karo; phir **3 cheezein** chala kar dekho: (1) **incoming call ki state** (`dumpsys telephony.registry` ya `adb shell dumpsys`), (2) **call uthana / kat-na** ka adb command (ya ADB se nahi hota to SEEDHA bol do — WhatsApp-web/USB-C SDK ka option), (3) **call state ka HUD event** (Hub par, `via="voice"` ke saath). **Koi permanent code nahi** - sirf probe + likha hua "haan/na" ka jawab. | Owner ne phone ka type/OS/USB-debugging bataya; spike report likhi (kaam karta hai / nahi karta, kaunsi command, kitni der). **P-01 ke baad hi T-02 shuru hoga.** |

## S12. Phone control ka plan (owner ke faisle ke baad, 4-Oct)

Owner ne 4-Oct ko scope band kiya. Ye sirf **record** hai — implementation
**P-01 ke baad** shuru hoga, aur P-01 owner ke phone type ke bina nahi.

**Jo pakka hai (faisal):**

| Item | Faisla |
|---|---|
| Scope | Sirf **incoming call**: uthana, khatam karna, aur call ki **state** batana (aaya/ringing/chala gaya). Message/sms/camera baad me — abhi koi nahi. |
| Inkaam ka raasta | Sirf **USB ADB** (Google platform-tools). Wi-Fi/network ADB nahi. |
| Call uthana | **ASK** — gatekeeper ka confirm card, sirf UI ka **ALLOW** button. Awaaz se ya chat se allow **nahi** (AGENTS 3.5). Decline bhi user ke confirm se hi. |
| Naya package | Adb ke alawa **kuch nahi** bina owner ke 'haan' ke (D-2). |
| Order | **T-01 ho gaya (4-Oct). Ab: P-01 → T-02 baaki** (ek time par ek hi kaam). P-01 owner ke phone type + USB debugging par depend hai. |

**Code me pehle se pada hai par dead hai (P-01 me mat use karo):**
`config_wake.py` me `WHATSAPP_WEB`, `CDP_HOST`, `CDP_PORT`, `CALL_ASK_FIRST`
constants hain, par aaj koi code unhe **use nahi** karta (grep verified).
Ye WhatsApp-web + Chrome-CDP ka purana idea hai — **ADB ka raasta nahi**. P-01 me
inhe hata kar `CALL_ASK_FIRST` ki jagah adb-based settings rakhi jayengi, warna
do raasta ban jayenge (AGENTS: "ek hi raasta").

**VERIFY (code padh kar, koi naya kaam nahi):**

| Item | Kya mila (4-Oct) |
|---|---|
| 3.9 mic-during-playback | `config_wake.PLAYBACK_MUTE_MIC = True` **constant hai par use nahi** hoti — matlab pehla VERIFY step (implement karna) T-07 me hai, confirm nahi kiya gaya. |

## S9. Definition of done (PC version)

| Stage | Roadmap target | Jarvis (PC) |
|---|---|---|
| 02 ACTIONS | Har tool 20 baar lagatar pass ya failure report. Har call logged. Red-tier confirm kaam kare. | Same, PC tools par: T-03 + T-04 + existing ALLOW card. |
| 03 VOICE | Across the room kaam kare; <1 false trigger/day (ek hafta); simple command ~1 s; beech me interrupt. | 'Hey Jarvis, time kya hai' ~1 s fast path; false-trigger log <1/day; barge-in. |
| 04 AUTOMATION | 5 routines 14 din bina fix; har ek undo; kyun fire hua bata sake. | T-10 + T-11. |
| 05 BUSINESS | 3 workflows har hafte; time saved tracked; bina approval zero message. | Briefing + notes search + draft-only (T-12..T-15). |
| 06 ONE SYSTEM | Ek conversation me room+work; reboot survive; dashboard 7 din >95% success. | T-16..T-18; 'room' = PC (D-1). |

## S10. Sources

- OpenCode Zen free-tier error (2026-10-03) - https://github.com/anomalyco/opencode/issues/52907
- OpenCode Zen 403 report (2026-09-19) - https://github.com/Alishahryar1/free-claude-code/issues/1837
- OpenCode rules / AGENTS.md / instructions - https://opencode.ai/docs/rules/
- OpenCode intro (Windows note) - https://opencode.ai/docs/
- Groq 120b free numbers (measured 2026-09-14) - https://github.com/Antoniodeoliveirasegura/boilerindy/issues/253
- Groq free tier summary - https://www.cloudzero.com/blog/groq-pricing/
- Free LLM API list (Groq, Cerebras, Gemini, OpenRouter) - https://github.com/cheahjs/free-llm-api-resources
- OpenRouter / Groq / Gemini limit discussion - https://github.com/xyzs996/free-llm-api/discussions/3
- Gemini free tier per model (Sept 2026) - https://www.scriptbyai.com/gemini-api-free-tier-limits/
- Gemini free tier - Google prints no numbers - https://www.memetik.ai/guides/gemini-api-free-tier-limits
- Gemini official rate-limit page - https://ai.google.dev/gemini-api/docs/rate-limits
- Python TTS libraries 2026 - https://www.bland.ai/blog/best-text-to-speech-python
- Self-hosted TTS (Kokoro, Piper, Edge-TTS) - https://offlinetts.com/blog/self-hosted-tts-guide-2026/
- edge-tts stats and block history - https://www.libhunt.com/r/edge-tts
- openWakeWord releases (hey jarvis, ONNX on Windows) - https://www.github.com/dscripka/openWakeWord/releases
- faster-whisper review (int8 CPU, Silero VAD) - https://www.promptquorum.com/power-local-llm/faster-whisper-review
- Tray watchdog + IsPromoted pattern (2026-09-30) - https://github.com/yhm138/ai-quota-tray/pull/19
- Windows 11 tray icon registry (IsPromoted) - https://www.elevenforum.com/t/hide-or-show-notification-icons-on-taskbar-system-tray-in-windows-11.415/
- Wrong interpreter -> headless tray - https://github.com/giovi321/clawdmeter-daemon/releases/tag/v1.0.1

---

## S11. Progress log (opencode yahan update karta hai)

Format: `T-xx | date | kya hua | file/commit | baaki`

| Task | Date | Kya hua | File / commit | Baaki |
|---|---|---|---|---|
| T-01 | 4-Oct-2026 | **Asli bug mila: pystray `visible=True` khud nahi karta jab `setup` callback diya ho.** `desktop/tray.py` me `run_detached(setup=self._on_setup)` tha aur `_on_setup` sirf `log.info("tray ready")` karta tha → icon **kabhi visible nahi hua**. `NIM_ADD` chala tha (is liye `NotifyIconSettings` me entry banti thi aur `tray_watch` "dikh raha hai" bolta tha) par shell use taskbar me render **nahin** karta tha. Pehle 3 din ye `^` me chhupa hone / `IsPromoted` missing samjhe gaye — galat. `Shell_NotifyIconGetRect` is PC par `E_INVALIDARG` deta hai (live proof, raw Win32 probe par bhi) → wo bhi galat source. **Dhyan se pakda:** UIA se taskbar ka asli naam padha → overflow me `Jarvis` nahi; raw Win32 probe (`NIM_ADD=1`) overflow me dikha; bare pystray bhi dikha; hamara `Tray` class nahi dikha → farq sirf `_on_setup` me. Fix: `_on_setup` me `icon.visible = True`. **Live proof:** app restart ke baad promoted tray me `Jarvis - band` dikha. `IsPromoted=1` bhi likha tha (backup `notifyicon-traywatch-20261004-123546.reg`) par usse koi fark nahi padha. S6 step 6 (base `python.exe`) try kiya — `uvicorn` missing, chhoda. **Owner ne live confirm kiya: taskbar par icon dikh raha hai.** Task khatam. | `desktop/tray.py`, `desktop/launcher.py`, `tests/test_desktop.py`, `tests/test_desktop_autostart.py`, `tests/test_desktop_login.py`, `docs/ROADMAP_STATUS.md`, `AGENTS.md`, `CHANGELOG.md` | **Khatam.** Agla: **P-01** (phone type chahiye). |
| A1-A3 | 5-Oct-2026 | **Wake do command + mic busy fix.** Asli bug: `wake/gate.py` khamoshi par sirf `listener.reset()` karta tha, jisse Vosk ka pending partial text chhoot jata tha (`sun liya: 'hello'` phir `sun liya: 'yo'` - trigger nahi). Naye teen raaste, ek faisla (`wake/trigger.py`): final (purana), partial (naya, sabse tez), flush (gate silence par `FinalResult()` se pending text nikalta hai). **Asli bug 2:** grammar me poori phrase (`"hello jarvis"`) thi - Vosk/Kaldi multi-word phrase map nahi kar pata; ab `grammar_words()` har **shabd** alag deta hai. **Asli bug 3:** mic busy (`MME error 1`) par ek hi koshish thi; ab `_open_mic()` 3 koshish (`PRABH_MIC_ATTEMPTS`/`PRABH_MIC_RETRY`). **Do bonus bug:** `stop()` ke baad double loop, aur `worker.wakes()` ka count reset. **51 suite green**, sab file `<=200`. Naye: `wake/trigger.py`, `wake/lifecycle.py`, `tests/test_wake_trigger.py`, `tests/test_wake_phrases.py`. | `wake/trigger.py`, `wake/lifecycle.py`, `wake/session.py`, `wake/gate.py`, `wake/detect.py`, `wake/audio.py`, `config_name.py`, `config_wake.py`, `config.py`, `tests/wakehelp.py`, `tests/test_wake_gate.py`, `tests/test_wake_trigger.py`, `tests/test_wake_phrases.py`, `tests/test_wake_loop.py`, `VOICE.md`, `TESTS.md`, `CHANGELOG.md` | **Code poora.** Live verify baaki: mic pakadne wala Chrome tab band karke app restart, phir do command. Aage (owner order): **C = P-01** ADB pair karna baaki (baad me), phir **B1** OpenCode Zen, **B2** 5TB storage, **D** roadmap. |
| (decide) | 4-Oct-2026 | **D-1 = A final** (PC-first; AC/TV/hardware permanently chhoda; "room" = PC + phone) · **D-2 = sirf ADB** allowed. `WHATSAPP_WEB`/`CDP_*`/`CALL_ASK_FIRST` dead constants (grep verified) | `docs/ROADMAP_STATUS.md` S8 + S12 | D-3 (PLAN-TRUST.md) abhi bhi owner-confirm ka wait me. |
| T-1B-1 | 10-Oct-2026 | **Docs saaf:** naming (sirf Jarvis), suite ginti 52 (README/NEW_AGENT_BRIEF/AGENTS/CLAUDE/ROADMAP), ADB IP:port+code hata diya, .env.example voice keys code se match (`*_VOICE_SUNDAY`). Koi .py/.js nahi chhua. | README.md, NEW_AGENT_BRIEF.md, AGENTS.md, CLAUDE.md, docs/ROADMAP_STATUS.md, .env.example | Baaki: TESTS.md (L1/L23) me abhi bhi 48 likha hai (aapki list me nahi tha). |
