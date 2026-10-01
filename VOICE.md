# Voice (mic se baat)

Mic aur speaker ka kaam **browser** me hota hai. Server sirf awaaz ko text me badalta hai
aur text ko awaaz me.

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

Round 2 ke baad **Sunday ki awaaz bhi female** hai. Pehle Sunday par ElevenLabs ka
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

- `"Sunday..."`, `"संडे..."` → Sunday
- `"Prabh..."`, `"Prabhu..."`, `"प्रभ..."`, `"प्रभु..."` → Prabh

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
| `ui/voice_ui.js` | Mic + speaker wiring (chat `app.js` se alag) |
| `ui/recorder.js` | `getUserMedia` + `MediaRecorder` + `track.stop()` |
| `ui/speaker.js` | Audio play + autoplay-block message |

`/stt` aur `/tts` dono ke liye token + origin + host check lagta hai — same jaise `/chat`.
