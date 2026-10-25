# Voice (mic se baat)

Mic aur speaker ka kaam **browser** me hota hai. Server sirf awaaz ko text me badalta hai
aur text ko awaaz me.

> **Wake word (Phase 5 Step 1) alag hai** — wo mic **Python** me (`sounddevice`)
> sunta hai taaki browser band ho tab bhi chale. Neeche "Wake word" section padho.

## Chalao

1. Server chalu karo (`main.py`).
2. Browser me **http://localhost:8000** kholo.
3. Browser puchega **"Use microphone"** — **Allow** dabao. Mana kiya to MIC kaam
   nahi karega aur screen par saaf message aayega.

## Buttons

| Button | Kaam |
|---|---|
| `MIC` | Ek click par recording shuru, dobara click par band. 30 second par apne aap band. |
| `MUTE` | Mic poori tarah band. Phir se dabao to wapas on. |
| `STOP` | Chal rahi awaaz ya recording turant rok do. |
| `SEND` | Command box me likhi baat bhejo. |

Recording me stage par **MIC ON** (peela) nishaan dikhta hai. Recording khatam hote hi
mic turant chhod diya jaata hai (browser ka mic indicator band ho jaata hai).

## Status kya matlab rakhta hai

`IDLE` → `LISTENING` (mic on) → `TRANSCRIBING` (sun raha hai) → `THINKING` (soch raha hai)
→ `SPEAKING` (bol raha hai) → `IDLE`

## Kaun sa provider kab use hota hai

| Provider | Kab | Free? |
|---|---|---|
| **ElevenLabs** | Pehle try hota hai. Sabse achhi awaaz. `ELEVENLABS_API_KEY` chahiye. | Free quota **10,000 character / mahina**. Khatam hone par `402` deta hai. |
| **Cartesia** | ElevenLabs fail ho to. `CARTESIA_API_KEY` + voice id chahiye. | Free quota chhota. |
| **edge-tts** | Hamesha aakhri bharosa. Koi key nahi chahiye. | Bilkul free, unlimited. |

- Voice ids na ho to wo provider skip ho jaata hai, agla try hota hai.
- Teeno fail hon to screen par saaf error aata hai — chup nahi hota.
- **Awaaz me sirf pehle 500 character** bolte hain (free quota bachaane ke liye).
  Poora jawab chat me likha rahe hota hai.
- Bolne se pehle link, emoji aur markdown (`*`, `#`, backtick, `_`, `>`) hata diye jate hain.

## Har mode ki awaaz — DONO female

Round 2 ke baad **Jarvis ki awaaz bhi female** hai. Pehle default mode par ElevenLabs ka
male (George) default pada tha; wo hata diya gaya hai.

| Provider | Chain me kab | Female check |
|---|---|---|
| **ElevenLabs** | Pehle | id `.env` me se. Female allowlist me na ho to **skip**. |
| **Cartesia** | ElevenLabs fail/limit par | id `.env` me se, `/voices` par `feminine` hona chahiye. |
| **edge-tts** | Hamesha aakhri | `hi-IN-SwaraNeural` (narm, pyaari) — dono mode. |

- Male voice id, ya female allowlist me na aane wala id — **kabhi use nahi hogi**.
  `voice/tts_female.py` har call par id check karta hai, na mile to agla provider.
- `edge-tts` ke liye allowlist: `hi-IN-SwaraNeural`, `hi-IN-MadhurNeural` — dono female.
- Koi provider 10 min ke liye fail ho jaye (402/429/503) to wo side me chhoda
  jaata hai, agli baar turant agla try hota hai.
- Cartesia voice id na mile to Cartesia **chhoot jati hai** — koi error nahi.

### Female kaise check hota hai

`voice/tts_female.py` me har provider ki **allowlist** hai:

- **edge**: naam me `Female` ya allowlist me hona chahiye (`Swara`, `Madhur`).
- **ElevenLabs**: `.env` ki id list me honi chahiye.
- **Cartesia**: id `.env` me explicit hona chahiye (gender `/voices` se pehle hi
  check kar lena — `feminine` wala hi daalna).

Naya female voice id add karna ho to wahin list me daalo, `.env` me id daalo.
Male id kabhi mat daalo — wo chup-chap skip ho jayegi.

### Cartesia ke do zaroori rules

- `output_format` **object** hona chahiye: `{"container": "mp3", "sample_rate": 44100}`.
  `"mp3"` string bhejne par API `400` deta hai.
- `language` `voice.control.language` ke **andar** jaata hai, top-level par nahi
  (top-level par API `"Model sunsetted"` bhejti hai). Hum `"hi"` bhejte hain.

## Mic band karna (sabse aasan galti)

`recorder.js` me mic band karne ke liye **`track.stop()`** use karo. `release()` jaisa koi
method hota hi nahi. Ye har raaste par zaroori hai:

- recording apne aap 30 second par khatam hui
- mic permission ya koi error aaya
- user ne **MUTE** / **STOP** dabaya
- naya recording shuru karte waqt (pehle wala track chhod do)

Track nahi roka to browser ka mic indicator (red dot) **chalu** reh jaata hai, aur agle
`getUserMedia` call par "mic busy" error aata hai — isliye ye chhota sa rule bada kaam
ka hai.

Recording ka **timer `recorder.js` me mat banao** — duration browser se `x-audio-ms`
header me bhejte hain, server usi par decide karta hai.

## Sunne wala (STT) ki suraksha

Whisper chhoti ya khaali recording par apne mann ka text bana deta hai
("Thank you for watching", subtitles, aise). Isliye `voice/stt_guard.py` teen
guard lagata hai:

| Guard | Rule | Kyun |
|---|---|---|
| **Duration** | Browser `x-audio-ms` bhejta hai. `<600ms` par reject. | `dab dab` par kuch nahi hota, par Whisper bana deta hai. |
| **Silence / khaali** | Text khaali, sirf punctuation, ya `.`/`♪` jaisa ek-aksh pattern | Awaaz me kuch nahi tha — text bhi nahi. |
| **Script** | Text me Devanagari ya Latin letter hi nahi (CJK/Cyrillic/Arabic allowed nahi) | Galat recording par ajeeb output. |

Ek aur baat: `language="hi"` **bilkul nahi** bhejte. Whisper Hinglish (romanized
Hindi) ko Hindi maan kar Devanagari me convert kar deta tha, jo galat tha. Auto
detection sahi rehti hai.

Guard reject kare to user ko saaf message milta hai — "bolege nahi sun paya, thoda
lamba bolo", brain call hota hi nahi.

## Mode bolke switch karo

Whisper (sunne wala) Hindi + English dono samajhta hai, to naam bhi bol sakte ho:

- `"Jarvis..."`, `"संडे..."` → Jarvis
- `"Prabh..."`, `"Prabhu..."`, `"प्रभ..."`, `"प्रभु..."` → Prabh

## Wake word (Phase 5 Step 1) — "Jarvis" bolkar bulao

Browser band ho tab bhi kaam karta hai, is liye ye mic **Python** me sunta hai
(`sounddevice`) — hamesha chalta hai, band kabhi nahi hota (duty cycle nahi).

| Baat | Detail |
|---|---|
| Kaam | App shuru hote hi mic khulta hai. **"Jarvis"** (ya "hello/hey jarvis") bolte hi **HUD khul jaata hai**. |
| Model | `models/vosk-model-small-en-us-0.15` — **Vosk**, 100% offline, awaaz bahar nahi jaati |
| Grammar | **Shabd, poori phrase nahi** (5-Oct ka fix): `hello`, `hey`, `jarvis`, `hlo`, `helo`, `hi`, `yo`, `[unk]` — trigger hamesha `jarvis` par hi hota hai, bas Hinglish bhi sahi shabd pe chun sake |
| Audio | 16 kHz mono, 30 ms chunk, energy VAD (threshold `.env` se `JARVIS_VAD`, ab **0.010** — door se/dheere "Hlo Jarvis" par trigger aata hai) |
| Battery | Vosk **sirf awaaz par** chalta hai (`wake/gate.py`) — khamoshi me chunk recognizer tak jaata hi nahi. Napi napa 4.8% → 0.9% core. Mic ka stream phir bhi khula rehta hai, is liye "Jarvis" har waqt sun sakta hai |
| Gate band | `.env` me `JARVIS_VOSK_GATE=0` — purana behaviour (har chunk Vosk ko), debug ke liye |
| Cooldown | Ek trigger ke baad **1.5 second** dobara nahi pakadta |
| Mute | Tray ka **Mic Mute** sunna rok deta hai (mic khula rehta hai, sunta nahi) |
| Band karo | `.env` me `JARVIS_WAKE=0` — phir startup me `wake: JARVIS_WAKE=0 se band hai` dikhega |
| Startup line | `wake: sun raha hai (jarvis)` — ya mic band/model missing ho to wajah |
| Mic busy | Chrome/Teams mic pakde ho to app **3 koshish** karti hai (`JARVIS_MIC_ATTEMPTS`, beech me `JARVIS_MIC_RETRY` second), phir `wake: nahi chala`. Wajah log me: `MME error 1` = mic kisi aur app ne pakda hua hai |

### Trigger ke **teen raaste** (5-Oct ka fix — "ek command ke baad doosra nahi")

Pehle sirf ek raasta tha (Vosk ka `final`). Wahan se do command me bug tha: gate
khamoshi par `listener.reset()` karta tha, jisse Vosk ka **pending** text chhoot
jata tha. Log me ye dikhta tha — `sun liya: 'hello'`, phir `sun liya: 'yo'`:
"Hlo Jarvis" do tukde me toot raha tha aur **trigger hi nahi** hota tha.

Ab teeno ka faisla **ek** jagah hai (`wake/trigger.py`), koi bhi ek kaafi hai:

| Raasta | Kab | Kyun |
|---|---|---|
| **final** | Vosk ne vaakya poora kiya | Purana raasta, abhi bhi |
| **partial** | Vosk **abhi** bol raha hai aur text me `jarvis` hai | Sabse tez — khamoshi ka intezaar nahi |
| **flush** | Gate ne khamoshi par `FinalResult()` se pending text nikaala | Wahi bug ka pakkaura |

Naye `start()` par cooldown saaf hota hai, warna restart ke baad pehla "Jarvis"
1.5 second tak pakda hi nahi jata. Wake debug line (`JARVIS_WAKE_DEBUG=1`) se
chunk/Vosk ka hisaab dekha ja sakta hai — **hamesha 0** rakho, warna har 3 second
ek line log me.

### Command sunna + bolna (Step 2c) — poora

Ab wake ke baad **poora command** chalta hai. "Jarvis" bolo, Jarvis "Ji, boliye"
bolega, aap apni baat bolo, aur jawab **awaaz me** aayega:

| Kya | Kahan |
|---|---|
| Command capture (pre-roll, VAD, max/min/wait) | `wake/utterance.py` |
| PCM -> WAV (Groq ko bhejne ke liye) | `wake/wav.py` |
| Speaker — TTS bytes bajana | `desktop/playback.py` |
| Mic wale paanch kaam (drain/warmup/**peek**/capture/STT) | `wake/listen.py` |
| Brain + speaker (awaaz) | `wake/ask.py` |
| Poora flow (peek -> ack -> suno -> brain -> awaaz) | `wake/command.py` |

#### Window (`.env` se badal sakte ho)

| Kya | Default | `.env` |
|---|---|---|
| Chup ho jaane par band | **0.7 s** | `JARVIS_CMD_SILENCE` |
| Ack se pehle sunna ("Ji, boliye" chhod do) | **0.18 s** | `JARVIS_ACK_PEEK` |
| Jawab ki **awaaz** ki limit | **220** char (HUD par poora jawab) | `JARVIS_VOICE_MAX` |
| Sabse lamba command | **30 s** | (constant) |
| Turn ka max step | 5 | (constant) |
| STT ka timeout | **6 s** | `JARVIS_STT_TIMEOUT` |
| STT ki retry | **1** | `JARVIS_STT_RETRIES` |

0.7 s: pehle 2.0 s tha, phir 1.2 s, phir 0.9 s. Beech ka 0.4 s `HANGOVER` alag hai
aur waise hi hai (warna beech ka vaakya kat jaata). Kam chuppi = tez jawab, par
thoda kam pakka text — is liye badalna `.env` se easy hai.

#### STT tez + pakka (13-Oct)

Pehle `voice/stt.py` brain wala **10 s** timeout uthata tha aur Groq SDK apne aap
**2 baar retry** karta tha — 3.5 s ki audio par call **43 s** tak atak sakta tha.
Ab:

| Kya | Value | Kahan |
|---|---|---|
| Per-attempt timeout | `6 s` | `config.STT_TIMEOUT_SECONDS` |
| SDK retry | `1` (matlab 2 koshish) | `config.STT_MAX_RETRIES` |
| App ceiling | `16 s` (`6*2 + 4`) | `config.stt_deadline()` |

Ceiling ke liye SDK call ek **daemon thread** me chalti hai (`join(timeout)`).
`asyncio.to_thread` akela kaafi nahi tha — `wake/listen.py` ke `asyncio.run()`
band hote waqt executor ka **join** wait karta hai, matlab hung thread par
caller bhi atkta. Ab caller saaf `SttError` ke saath turant laut aata hai.

Log me do naye number har command ke saath aate hain (`wake/utterance.py`):

```
command capture: 113 chunk = 3389ms | peak_rms=0.6210 clip=3.40%
```

- `peak_rms` — sabse loud 30 ms chunk ka RMS. Asli bol-chal ~0.02–0.2 hoti hai.
- `clip` — kitne % sample full-scale par the (mic bahut tez / AGC utha hua).

Sirf **number** log hote hain — audio kahin save nahi hoti. `clip` bada ya
`peak_rms` bahut kam dikhe to STT ka bakwas text samajh me aata hai.

#### ElevenLabs 401 (13-Oct)

`brain/health_words.py` me 401/403 ka pattern nahi tha, is liye wo `"other"` ban
kar `classify_and_skip()` se guzar jata tha (wo sirf `busy/billing/auth/empty`
par kuch karta hai) — matlab **har jawab me** ElevenLabs dobara poochha jaata
tha (`TIME tts: elevenlabs-fail 957ms`). Ab 401 → `auth` → `lock_auth()` →
poore session me BAND, seedha Edge. Nayi key daalo to `health.reset_provider()`.
Key khaali ho to provider bilkul try hi nahi hota (`voice/tts.py` ka
`missing_key()`) — voice id wala check alag hai.

#### Kya hota hai, ek line me

`"Ji, boliye"` → mic ka purana queue phenka + mic garam kiya → aapki baat record
(1.2 s chup par band, 30 s par force) → Groq STT → brain → HUD par jawab + **awaaz**.

- ❌ **Suna hi nahi** → "Main theek se sun nahi paya, dobara boliye."
- ❌ **Brain/net fail** → sirf "Abhi jawab nahi mil pa raha." (provider ke
  technical reasons **awaaz par nahi** padhe — wo sirf HUD par dikhte hain)
- ❓ **Tool chahiye (ASK card)** → HUD par confirm card + "Screen par confirm
  kijiye." — **awaaz se allow kabhi nahi hota**, button se hi hoga. Ye line
  card ke aate hi boli jaati hai, 60 s baad nahi.
- 🔇 **Mute ya PC lock** → command bilkul nahi chalta (na record, na awaaz, na brain).

#### Do awaaz kyun nahi bajti

Wake se aaye har brain event par `via="voice"` lagta hai; `ui/app.js` us par
browser ka TTS **skip** karta hai. Awaaz sirf `desktop/playback.py` se balti hai.
Jo message tum **type** karte ho usme `via` nahi hota — wo waise hi browser se
bolte hain.

#### Recording ke pakkaurey

- Command ka audio **kabhi disk par save nahi hota** — memory me byte buffer,
  seedha Groq STT ko. Wake word (Vosk) poora **offline** hai, koi recording
  provider ko nahi jaati.
- Mic band karte waqt jo chunk queue bacha hota hai use pehle phenka jaata hai
  (`listen.drain()`) — warna Jarvis apni hi awaaz sun kar dobara trigger hota.

### Tez kyun hai (Step 2 speed fix, 3 Oct)

Pehle log me ye dikhta tha:
`TIME wake_command: TOTAL 18450ms | ack=3520ms warmup=1036ms capture=8088ms`.
Brain to tez tha (~1.1–1.7 s), der **wake path** me thi. Teen fix:

| Kya | Pehle | Ab |
|---|---|---|
| "Ji, boliye" ki awaaz | har baar banti thi (~1.5 s) | `voice/tts.py` me cache — dusri baar **0 ms** |
| Warm-up | har baar 1 s dead wait | ack chalti hai, usi me mic settle (deadline) |
| Chuppi | 2.0 s | **1.2 s** |

- Cache **bounded** hai (`CACHE_MAX = 8`, purani entry nikal jaati hai) aur
  provider fail hone par **kuch store nahi** hota — warna app hamesha "nahi bola"
  repeat karegi aur recovery kabhi na ho.
- Brain ka naya jawab bhi `speak_cached()` se hi jaata hai (awaaz ka ek hi raasta
  hai) — par unique hai to hit nahi hoga. Memory par koi asar nahi (`~50 KB` × 8).
- Test: `tests/test_tts_cache.py`, `tests/test_speed_fix.py`.

### "So jao" — battery (4-Oct)

| Kya | Kaise |
|---|---|
| Awaaz se so jao | "Jarvis, **so jao**" bolo (ya `so jaiye`, `sone jao`, `soye raho`, `band ho jao`) — HUD band, sirf mic sunna bacha |
| Tray se | Tray menu me **SO JAAO** item (menu me 6 button) |
| Jaagna | Wake word — "Jarvis" / "Hlo Jarvis". HUD + command dono waise chalte hain |
| Puri tarah band | Tray ka **Quit** (ya Ctrl+C). CPU 0. **Wake se start nahi hoga** — mic hi nahi bachega. Dobara kholne ke liye Desktop shortcut / launcher |

**Sach baat:** mic ko software se band karna = "Hlo Jarvis" feature hi khatam.
Is liye battery ka bachat "sunna band karke" nahi, bhaari kaam band karke milta
hai (HUD/browser/stats). Step 1 ka gate + ye sleep mode = mic+gate ~0.9% core.

### Tez kyun hai (speed fix 2, 4-Oct)

| Kya | Pehle | Ab |
|---|---|---|
| "Ji, boliye" | har baar, chahe aap bol bhi rahe ho | Sirf tab jab aap **chup** ho — pehle 0.18 s suno, awaaz mili to ack chhod do (pehle hamari awaaz aapke upar chadh jaati thi) |
| Chuppi | 1.2 s | **0.9 s** |
| Jawab ki awaaz | 500 char (playback hi 4.3 s) | **220 char**, vaakya ke end par kata (`tts.clip_answer`) — HUD par poora jawab |

### Speaker ke do pakkaurey (Step 2)

1. **`miniaudio.decode`, `decode_file` nahi.** `decode_file` sirf filename leta
   hai. Bytes dene par wo poora audio buffer apne error message me daal deta
   hai — yaani terminal par MB ka dump. `desktop/playback.py` sirf `decode()`
   (memory buffer) use karta hai.
2. **`sd.query_devices(kind="output")` list nahi deta** — sirf default output
   device ka ek dict deta hai. List ke liye `query_devices()` (bina argument)
   + `max_output_channels > 0` filter. `desktop/playback.py` me yahi hai.

TTS ka provider **yahan chuna nahi jaata** — awaaz hamesha `voice/tts.py` se
aati hai (AGENTS.md ka "TTS provider ka ek hi raasta") aur `say()` sirf use
bajata hai. `.env` me `JARVIS_SPEAKER=<device name>` se speaker badal sakte ho,
`JARVIS_SPEAKER_RATE` se rate (default 32 kHz mono).

### Abhi kya **nahi** hota

- ✅ Command sunna, brain tak jaana, jawab ki awaaz — **Step 2c poora**
- ❌ **Tool sunke chalana** — card aata hai, par ALLOW hamesha screen par button
  se hi hoga, awaaz se nahi (AGENTS.md section 3.5)
- ❌ **Model kahan hai** ka section — samne wala paragraph dekho

### Awaaz app ke bina test karo

```powershell
cd D:\Projects\jarvis\jarvis2.0
# 1. Kaunse speaker hain
.\.venv\Scripts\python.exe -m desktop.playback_cli --list
# 2. Asli awaaz (ek baar "Ji, boliye" bolega)
.\.venv\Scripts\python.exe -m desktop.playback_cli --say "Ji, boliye"
```

Poora voice flow (mic + STT + brain + awaaz) test karne ke liye app chala kar
"Jarvis" bolo — `logs/jarvis.log` me har stage ka time (`ack / warmup / capture /
stt / brain / speak`) ek line me dikhta hai.

### Model kahan hai / kya hua to

Model `D:\Projects\jarvis\jarvis2.0\models\` me hona chahiye. Ho to startup par khud load ho jaata hai.
Na ho to ek hi baar download karo (~40 MB, 100% offline chalta hai):

```powershell
# 1. Download + unzip (ek hi baar). Folder ka naam bilkul yahi hona chahiye.
cd D:\Projects\jarvis\jarvis2.0
New-Item -ItemType Directory -Force models | Out-Null
Invoke-WebRequest -Uri https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip -OutFile "$env:TEMP\vosk.zip"
Expand-Archive "$env:TEMP\vosk.zip" -DestinationPath models -Force

# 2. Model ka folder check (app band ho to)
.\.venv\Scripts\python.exe -c "import config; print(config.describe())"
```

`models\vosk-model-small-en-us-0.15\` ke andar `am\`, `conf\`, `graph\` dikhne chahiye —
agar zip ne ek extra folder banaya ho to andar wala folder hi `models\` me rakho.

`model=MISSING` aaye to app chalega, par wake nahi. Wajah log me:
`logs/jarvis.log` me `wake chalu nahi:` ya `Vosk model nahi mila`.

### Test me kya hota hai

`tests/test_wake.py` (constants, VAD, phrase, model error),
`tests/test_wake_loop.py` (poora loop), aur Step 2c ke teen suite —
`test_wake_command.py` (poora flow), `test_wake_brain.py` (brain + ASK) aur
`test_wake_listen.py` (mic + pause). Sab **asli mic, Vosk model aur speaker kabhi
nahi** chalate, fakes `tests/wakecmdhelp.py` se aate hain. Isi liye test laptop
ki battery/CPU par asar nahi dale aur flaky nahi hote.

## Limit

- Recording: **30 second** (server par 10 MB se bada audio reject).
- Agar browser autoplay rok de to screen par likha aayega:
  **"Awaaz chalane ke liye kahin click karo."** — kahin ek click kar dena kaafi hai.

## Server side

| File | Kaam |
|---|---|
| `server/voice_routes.py` | `POST /stt` (audio → text) + `POST /tts` (text → audio) |
| `config_voice.py` | Saare voice/TTS/STT constants + `voice_for()` |
| `voice/stt.py` | Groq Whisper + `device="cpu"` |
| `voice/stt_guard.py` | Duration / silence / script guard |
| `voice/tts.py` | Provider chain + markdown/emoji saaf karna |
| `voice/tts_female.py` | Female allowlist + Edge fallback |
| `voice/tts_elevenlabs.py` | ElevenLabs provider |
| `voice/tts_cartesia.py` | Cartesia provider |
| `voice/tts_edge.py` | edge-tts provider (free, unlimited) |
| `config_wake.py` | Wake word + VAD + command window ke constants |
| `wake/worker.py` | Wake ka module-level raasta (ek hi worker, poori app me) |
| `wake/session.py` | Worker ka asli loop: mic → VAD → Vosk → trigger (thread, cooldown) |
| `wake/audio.py` | Mic ka ek owner (`sounddevice`) + energy VAD + PCM helpers |
| `wake/detect.py` | Vosk `KaldiRecognizer` ka wrapper (JSON → saaf text) |
| `wake/phrase.py` | "jarvis" pakadna — pure functions |
| `wake/model.py` | Vosk model load + cache, saaf Hinglish error |
| `ui/voice_ui.js` | Mic + speaker wiring (chat `app.js` se alag) |
| `ui/recorder.js` | `getUserMedia` + `MediaRecorder` + `track.stop()` |
| `ui/speaker.js` | Audio play + autoplay-block message |

`/stt` aur `/tts` dono ke liye token + origin + host check lagta hai — same jaise `/chat`.
