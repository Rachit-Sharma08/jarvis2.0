"""Wake word — offline sunna ("hello sunday") + command recording.

**Step 1 (abhi poora):** `config_wake.py` ke constants + is package ke
`model`, `audio`, `detect`, `phrase`, `worker`. Sirf **sunta** hai: mic khula
rehta hai, Vosk text laata hai, "sunday" milte hi `on_wake(phrase)`. Koi
recording, koi STT, koi brain call nahi — wo Step 2 hai.

Step 2 me aayenge: `command` (wake ke baad sunna), `session`, `playback`
("Ji, boliye" bolna), `chime`.

Rule: mic ka EK hi owner `audio.py` hai. Wake sunta hai aur command bhi usi
stream se record hoti hai — do stream kabhi nahi.
"""
