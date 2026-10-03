"""Wake word — offline sunna ("hello jarvis") + wake ke baad ka command.

**Step 1 poora:** `config_wake.py` ke constants + is package ke `model`,
`audio`, `detect`, `phrase`, `session`, `worker`. Sirf **sunta** hai: mic khula
rehta hai, Vosk text laata hai, wake shabd milte hi `on_wake(phrase)`.

**Step 2 shuru ho chuka hai:** `utterance` (wake ke baad command uthata hai)
aur `wav` (Groq ke liye WAV). Awaaz ka raasta `desktop/playback.py` me hai —
peaker ka wo hissa pura hai. Jo baki hai: command ka text lene se lekar brain
ke jawab tak ka glue (`command`), yaani `wake/command.py`.

Rule: mic ka EK hi owner `audio.py` hai. Wake sunta hai aur command bhi usi
stream se record hoti hai — do stream kabhi nahi.
"""
