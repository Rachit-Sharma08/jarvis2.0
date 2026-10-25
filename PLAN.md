# PLAN.md — Phase 5: Sunday OS (wake word, face, loyalty, seekhna)

Yeh sirf **plan** hai. Code tab likha jayega jab tum "haan" bolo.
AGENTS.md ke niyam: pehle plan dikha, phir code. Har step ka apna commit.

Detail ka doosra hissa: **[PLAN-TRUST.md](PLAN-TRUST.md)** (secret, loyalty,
Sunday ka khud assistant banana, Wednesday).

---

## 1. Tumne jo maanga — wo kaise banaoge

| Tumhari demand | Feature | File |
|---|---|---|
| "Hello Sunday" bolu → PC ki screen khule | Wake word (Vosk, offline) | `wake/` |
| Screen khulte hi mic on ho jaaye | Wake ke baad auto-listen | `wake/listen.py` |
| Khud detect karke mic band | Silence detect (VAD) + hard limit | `wake/listen.py` |
| Face na dikhe to tools na chale | Screen unlock (trust level) | `trust/` + `face/` |
| "Rachit, kya haal hai" | Greeting | `face/identity.py` |
| Owner ko pehchan ke secret share | 3-layer secret rule | `trust/secrets.py` |
| Meri galti samjhe | Self-correction | `learn/` |
| Meri raksha kare, family member bane | Trust levels + code guard | `trust/guard.py` |
| Sunday **khud ek AI assistant bana sake** | Meta-builder | `maker/` |
| Wednesday assistant (kam power, Sunday kuch na bataye) | Do-brain | `wed/` |

---

## 2. Architecture map (har file <200 lines)

```
wake/
  listen.py       mic sunta hai, Vosk se text
  trigger.py      "hello sunday" pakda -> server
  idle.py         silence detect + auto mic off
  autostart.py    Windows login par chalu

face/
  capture.py      camera se frame (opencv)
  enroll.py       pehli baar "Rachit" ka face register
  recognize.py    frame ko pichhle se mila -> naam + confidence
  identity.py     kaun hai, kab se, kitni confidence

trust/
  levels.py       GUEST / FAMILY / OWNER
  guard.py        sensitive tool se pehle face + PIN
  secrets.py      secret ka 3-layer rule
  audit.py        har access ka record (log + ACTIVITY)

learn/
  corrections.py  galtiyan yaad rakhna (corrections.txt)
  reflect.py      error dekhke "agli baar aisa mat kar"

maker/            <- Sunday khud assistant banayega (Step 9)
  spec.py         assistant ki spec likhna
  scaffold.py     files/folders banana
  review.py       likha hua code jaanchna

wed/
  brain.py        Wednesday persona — NO tool power
  delegate.py     Sunday -> Wednesday (sirf output aata hai Sunday ko)
```

Naye dependency (sab free): `vosk`, `opencv-python`, `insightface`, `onnxruntime`

---

## 3. Steps (har step alag commit)

| Step | Kya | Free |
|---|---|---|
| 0 | `trust/levels.py` + `audit.py` (pehle se safe) + rule approval | ₹0 |
| 1 | Vosk + `wake/` — "hello sunday" se trigger | ₹0 |
| 2 | `wake/idle.py` — mic on, suno, khud band | ₹0 |
| 3 | Auto-start (Windows login) | ₹0 |
| 4 | OpenCV + `face/enroll.py` — "Rachit" register | ₹0 |
| 5 | `face/recognize.py` + screen unlock | ₹0 |
| 6 | Greeting + `trust/secrets.py` | ₹0 |
| 7 | `learn/` — galti yaad rakhna | ₹0 |
| 8 | `wed/` — Wednesday (Sunday kuch nahi batayega) | ₹0 |
| 9 | `maker/` — Sunday khud assistant banayega (**sabse mushkil, aakhir me**) | ₹0 |
| 10 | End-to-end test + docs | ₹0 |

Har step: test chalao, live check karo, commit karo.

---

## 4. Tumhare sawaal, mere jawab (2-10 Oct 2026 ko decide hua)

| Sawaal | Tumhara jawab |
|---|---|
| "Sunday" bolne ke baad kya? | Local PC ki screen khule **+ mic on ho jaaye** |
| Mic kab band? | **Khud** silence detect karke, aur ek hard limit |
| Wednesday ko Sunday kya bataye? | **Kuch nahi.** Sunday sirf output leta hai, apna plan/secret nahi |
| Face ka kaam? | Screen unlock + greeting + secret (teeno) |
| Sunday kitna strong? | **Wo khud ek AI assistant bana sake** — code likh ke |

---

## 5. Wake word ke baad ka flow (jo humne fix kiya)

```
1. Tum bolte ho      "hello sunday"
2. Vosk sunta hai    (browser band ho tab bhi)         <- Python side, sirf sunta
3. Trigger mila       screen khule: http://127.0.0.1:8000
4. Mic auto-on        browser me, tumse baat karne ke liye
5. Wo sunta hai       tumhara command → text → brain → jawab
6. Silence detect     3 second tum kuch bolo nahi → sunna band
7. Mic off            + red dot bujha
8. Hard limit         30 second se zyada sunna KABHI nahi
```

**Kamzor par kya hoga (honest):**
- Agar do log baat kar rahe hon, ek shabd "sunday" sun kar trigger ho sakta hai
  (sirf trigger — andar ka command phir bhi confirm karega)
- Step 4-6 browser me hi — wahan pehle se ASR + recording + VAD sab hai

---

## 6. Policy conflict — approval chahiye

**AGENTS.md aaj kehta hai:** "Mic/speaker sirf browser me. Python me
`sounddevice`/`PyAudio` kabhi use mat karo."

**Wake word me ye todna padega** (browser band ho tab sunna hai), isliye naya rule:

> Mic: **browser me** jab page khula ho (record + play + silence detect).
> Wake word: **Python me sirf `wake/listen.py`** — sirf sunta hai, kabhi record
> nahi karta, sirf word pakad ke ruk jaata hai. Recording browser me hi rahegi.

**Bina tumhare "haan" ke main ye rule nahi badalunga.**

---

## 7. Free — confirm

| Item | Cost |
|---|---|
| Vosk (~40 MB, ek baar) | ₹0, uske baad offline |
| opencv-python | ₹0 |
| insightface + onnxruntime (~300 MB, ek baar) | ₹0, uske baad offline |
| Brain, TTS, HUD, tools, Sunday ka naya assistant | ₹0 (pehle se) |
| Server laptop pe | ₹0 |

**Ek limitation:** laptop me GPU nahi (sirf Intel Iris Xe) → face check CPU pe
~1-3 check/second. Aur andhera/mehri roshni me face match gir sakta hai — is
liye PIN bhi rakha hai.

---

## 8. Step 9 ki honest warning (Sunday khud assistant banayega)

Ye **sabse bada** step hai aur sabse risky bhi. Sunday jab code likhega aur
chalayega — matlab woh khud apna kaam kar sakta hai. Is liye plan me:

- sirf `D:\Projects\jarvis\jarvis2.0\` ke andar hi likh sakta hai (bahar kahin nahi)
- har run ke liye confirm card (ASK), auto-run nahi
- har change git me commit → galti ho to pichle wapas
- likhe hue code ko `maker/review.py` jaanche (tests chale) — bina green test
  ke uska assistant merge nahi hoga

Isi karan se wo **Step 9** me hai, sabse aakhir me — pehle Sunday khud solid
banna chahiye, phir usse aur banane ka kaam dena.