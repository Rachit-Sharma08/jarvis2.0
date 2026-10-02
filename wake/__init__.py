"""Wake word — offline sunna ("hello sunday") + command recording.

Step 3a me sirf `worker.py` ka stub hai (shell pehle bana rahe hain).
Step 1 me is package ke asli files aayenge: `model`, `audio`, `detect`,
`phrase`, `worker`. Step 2 me `vad`, `recorder`, `session`, `playback`,
`chime`, `wav`, `bench`.

Rule: mic ka EK hi owner `audio.py` hai. Wake sunta hai aur command bhi usi
stream se record hoti hai — do stream kabhi nahi.
"""
