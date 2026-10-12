# Sentence streaming — design note (KAAM 4c)

**Status: design only, code nahi.** Neeche jo likha hai wo 13-Oct ki raat ko
soch kar likha gaya hai; implement nahi kiya gaya. Kyun — sabse neeche "Kyun
abhi nahi" me saaf likha hai.

## Maqsla

Aaj jawab ka raasta ek hi hai: brain poora jawab deta hai → `voice/tts.py`
poora text provider ko deta hai → audio pura aata hai → phir `desktop/playback.py`
usay bajata hai.

Matlab **pehla shabd** tabhi sunai deta hai jab **poora** audio ban chuka ho.
Live numbers (13-Oct ka log):

```
TIME tts: edge 5168ms (total 6126ms)      <- poora audio banane me
speaker: 12264ms                          <- uske baad playback
TIME wake_command: brain 1897ms speak 18530ms
```

Matlab brain khatam hone ke **~18 s** baad pehla shabd bolta hai. Brain khud
1.9 s laga — 16 s sirf "awaaz ban rahi thi".

## Idea

Text ko **vaakya-vaakya** tod kar alag-alag bhejna, aur pehla vaakya jaise
hi ready ho playback shuru karna:

```
brain ──► answer (ek saath)
            │
            ├─ vaakya 1 ──► TTS ──► audio 1 ──► play (turant)
            └─ vaakya 2 ──► TTS ──► audio 2 ──► queue
```

`sentence-by-sentence` streaming bhi ek option hai — kuch providers dete hain
(Chunked HTTP + incremental decode). Wo zyada asaan hai par har provider ka
support alag hai, aur ElevenLabs abhi **401** de raha hai is liye Edge hi asli
provider hai.

## Ek hi raasta jo saaf rahega

`voice/tts.py` me ek naya public function, aur **sirf** wahi call karega jo
aaj `speak()` call karta hai:

```python
async def speak_stream(text, mode):
    """(audio_chunks, provider) — pehla chunk jaise hi ready ho."""
```

Phir `desktop/playback.py` me:

```python
def play_stream(chunks):
    """Pehla chunk bajate hi queue bharte raho (worker thread)."""
```

`wake/ask.py` ke `speak()` aur `desktop/playback.py` ke `say()` — dono yahin
jaayenge. **Naya raasta nahi** (AGENTS ka niyam: TTS ka ek hi raasta).

## Jo dhyan rakhna padega

1. **Tail guard ke saath:** pehla vaakya bajte hi mic sunna shuru ho jaata
   hai, aur agle vaakya ban rahe hote hain. `wake/worker.py` ka hold poore
   jawab tak rakhna padega, warna apni awaaz se WAKE HIT (KAAM 2 ka bug).
2. **Playback queue:** `sounddevice` ka `sd.play` blocking hai. Ya to har vaakya
   alag `sd.play` + `sd.wait`, ya `sd.OutputStream` (streaming). Doosra tez hai
   par `tests/desktophelp.py` ke fakes ko badalna padega.
3. **Cache:** `voice/tts.py` ka `_CACHE` poora text ke liye hai. Streaming me
   har vaakya ka alag audio cache karna padega, warna "Ji, boliye" dobara bane.
   Size badhegi — `CACHE_MAX` soch-na padega.
4. **Cut:** agar jawab beech me kaate (220 char), to streaming me jo ban chuka
   uske baad ka text **waste** ho jaata hai (provider call ho chuki). Is liye
   sirf aakhri vaakya pe hi clip karna padega.
5. **Test:** `tests/desktophelp.py` ke audio fake pe timing test — pehla chunk
   kitni der me aata hai, poori stream kitni.

## Ek seedha fayda jo isse pehle mil sakta hai

Ye **bina** naye code ke bhi 60% faida de sakta hai: brain se sirf **pehla
vaakya** maango (`tts.voice_answer()` ab yahi kar chuka hai, 1-2 vaakya), aur
uska TTS turant banao. Baaki jawab HUD par already poora dikhta hai. Isi liye
wo pehle kar diya gaya hai — streaming ki zaroorat iske baad bhi rahegi par
usda kuch kam hoga.

## Kyun abhi nahi

- Raat ke 4 baje me ye bhaari refactor (playback + cache + tail guard ka
  interaction) bina asli speaker sune likhna khatarna tha — test me sab fake
  hota, yaani asli `sounddevice` ki streaming koi test nahi pakadti.
- Ek galti yahan seedha **self-hearing** wapas la deti (mic hold chhoot jaata,
  humari awaaz trigger) — wahi bug jo do ghante pehle fix kiya.
- Rachit ko subah **kaam dekhna** hai, kaam chalu karne se pehle nahi.

**Agla kadam (Rachit ke decide karne par):** ek branch me sirf `say()` ka
streaming wala prototype, Edge ke saath, aur `TIME` log me pehla-shabd ka
time alag se. Phir decide karna ki rakhe ya chhode.
