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
`MIC` | Ek click par recording shuru, dobara click par band. 30 second par apne aap band. |
`MUTE` | Mic poori tarah band. Phir se dabao to wapas on. |
`STOP` | Chal rahi awaaz ya recording turant rok do. |
`SEND` | Command box me likhi baat bhejo. |

Recording me stage par **MIC ON** (peela) nishaan dikhta hai. Recording khatam hote hi
mic turant chhod diya jaata hai (browser ka mic indicator band ho jaata hai).

## Status kya matlab rakhta hai

`IDLE` → `LISTENING` (mic on) → `TRANSCRIBING` (sun raha hai) → `THINKING` (soch raha hai)
→ `SPEAKING` (bol raha hai) → `IDLE`

## Kaun sa provider kab use hota hai

| Provider | Kab | Free? |
|---|---|---|
**ElevenLabs** | Pehle try hota hai. Sabse achhi awaaz. `ELEVENLABS_API_KEY` chahiye. | Free quota **10,000 character / mahina**. Khatam hone par `402` deta hai. |
**Cartesia** | ElevenLabs fail ho to. `CARTESIA_API_KEY` + voice id chahiye. | Free quota chhota. |
**edge-tts** | Hamesha aakhri bharosa. Koi key nahi chahiye. | Bilkul free, unlimited. |

- Voice ids na ho to wo provider skip ho jaata hai, agla try hota hai.
- Teeno fail hon to screen par saaf error aata hai — chup nahi hota.
- **Awaaz me sirf pehle 500 character** bolte hain (free quota bachaane ke liye).
  Poora jawab chat me likha rahe hota hai.
- Bolne se pehle link, emoji aur markdown (`*`, `#`, backtick, `_`, `>`) hata diye jate hain.

## Har mode ki awaaz

| Mode | ElevenLabs | Cartesia | edge-tts |
|---|---|---|---|
| `Sunday` | `JBFqnCBsd6RMkjVDRZzb` (George, male) `.env` me `ELEVENLABS_VOICE_SUNDAY` | khaali (skip) | `hi-IN-MadhurNeural` (professional) |
| `Prabh` | `XrExE9yKIg1WjnnlVkGX` (Matilda, **female**) `.env` me `ELEVENLABS_VOICE_PRABH` | `3b554273-4299-48b9-9aaf-eefd438e3941` (Simi, feminine) `.env` me `CARTESIA_VOICE_PRABH` | `hi-IN-SwaraNeural` (narm, pyaari) |

### Prabh ki awaaz hamesha female

Prabh ke liye male awaaz **kabhi** use nahi hogi. Chain ye hai:

`ElevenLabs (female id)` → `Cartesia (female id)` → `Edge hi-IN-SwaraNeural`

- Prabh ka ElevenLabs id `.env` me nahi hai ya galat hai to wo provider **chhop** diya
  jaata hai — default (male) awaaz par nahi jata.
- Cartesia voice ki gender `/voices` endpoint se check karo (`feminine`/`masculine`).
  Female nahi ho to wo id mat daalo.
- Koi bhi provider 10 min ke liye fail ho jaye (402/429/503) to wo side me chhoda
  jaata hai, agli baar turant agla try hota hai.

### Cartesia ke do zaroori rules

- `output_format` **object** hona chahiye: `{"container": "mp3", "sample_rate": 44100}`.
  `"mp3"` string bhejne par API `400` deta hai.
- `language` `voice.control.language` ke **andar** jaata hai, top-level par nahi
  (top-level par API `"Model sunsetted"` bhejti hai). Hum `"hi"` bhejte hain.

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
`server/voice_routes.py` | `POST /stt` (audio → text) + `POST /tts` (text → audio) |
`voice/stt.py` | Groq Whisper + `device="cpu"` |
`voice/tts.py` | Provider chain + markdown/emoji saaf karna |
`voice/tts_elevenlabs.py` | ElevenLabs provider |
`voice/tts_cartesia.py` | Cartesia provider |
`voice/tts_edge.py` | edge-tts provider (free, unlimited) |
`ui/recorder.js` | `getUserMedia` + `MediaRecorder` + track.stop() |
`ui/speaker.js` | Audio play + autoplay-block message |

`/stt` aur `/tts` dono ke liye token + origin + host check lagta hai — same jaise `/chat`.
