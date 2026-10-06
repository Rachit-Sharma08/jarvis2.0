# Maya AI vs JARVIS (Jarvis2.0 / Prabh)

## Quick Comparison

| Aspect | Maya AI | JARVIS (Prabh/Jarvis2.0) | Verdict |
|---|---|---|---|
| Type | General AI assistant (cloud) | Local-first voice assistant (desktop app) | Different focus |
| Local vs Cloud | Mostly cloud | Local-first (Vosk wake, 127.0.0.1) | JARVIS more private/local |
| Voice | Natural TTS/STT | Wake word + Groq STT + TTS chain (ElevenLabs/Cartesia/Edge), female-only | Strong hands-free |
| System Control | Chat-focused | Tools (files/apps/system/run_command), Gatekeeper ASK, tool loop | Action-taking |
| Memory | Session/context varies | Short-term memory (JSON local) + summary slot | Local-controlled |
| HUD/UI | Web/chat UI | 3-column HUD, WebSocket live, Orb pulse, tray+hotkey | MCU-style HUD-first |
| Proactivity | Mostly reactive | Reminders/todos/HUD badge, timers | Becoming proactive |
| Privacy | Cloud-dependent | Local-first, secrets never logged/git | Better for privacy |
| Internet Search | Built-in | SerpAPI tool (API-based, user key) | Flexible |
| Cost | Freemium | Free-heavy + local (budget 0) | Budget-friendly |

## Conclusion
- Maya AI = general cloud chat assistant
- JARVIS (this project) = action-taking local desktop butler (voice+tools+HUD)

Ham khud ka local Maya/JARVIS hybrid bana rahe hain - zyada focus action + HUD + wake word pe.
