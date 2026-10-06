# n8n - Free Automation Options (Local/Self-host)

## Overview
n8n ek workflow automation tool hai. Free tareeke se use kar sakte ho: self-host (Docker/local) ya cloud (trial/plan). Local self-host free hai (open source core).

## Local Self-host (Windows + Docker) - Free
Options:
- Docker Desktop (free for personal)
- npm: 
pm install n8n -g + run
- Docker Compose (recommended)

Simple docker-compose (example):
`yaml
services:
  n8n:
    image: n8n/n8n:latest
    restart: always
    ports: ["5678:5678"]
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_HOST=localhost
      - N8N_PORT=5678
      - GENERIC_TIMEZONE=Asia/Kolkata
    volumes:
      - n8n_data:/home/node/.n8n
volumes:
  n8n_data:
`

Run: docker compose up -d -> http://localhost:5678

## Notes (Safe)
- Instagram automation workflows risky (platform TOS + rate limits). Kabhi bhi private session/login creds auto-share na karo.
- Jarvis se n8n webhook trigger kar sakte ho (http call via un_command/curl) - ye safe hai (external trigger).
- Jarvis me abhi open_url, copy_text, get_clipboard tools hain - n8n UI open karne ke liye use kar lo.

## Recommendation
n8n self-host locally free hai. Lekin **Instagram login/automation code** jarvis me add nahi karunga (safe boundary). n8n workflow khud banao, Jarvis sirf trigger kare (webhook) - ye safe approach hai.
