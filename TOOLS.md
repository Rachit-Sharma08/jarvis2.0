# PC Tools (Sunday aur Prabh dono ke liye)

Prabh PC ka koi kaam kar sakta hai — file banana, folder dekhna, app kholna, command
chalana. Har kaam ke pehle **gatekeeper** faisla karta hai. Koi bhi tool bina faisle ke
nahi chalta.

## Sabse pehle: TOOLS ON karo

Screen par upar **`TOOLS OFF`** button hota hai (default `OFF` hai).

- **OFF** — koi bhi PC tool nahi chalega. Chat bilkul waise hi kaam karega.
- **ON** — tool chal sakte hain, par har tool pehle gatekeeper se gujarta hai.
- Beech me bichhna ho to **`STOP`** daba do (script bhi, card bhi band ho jaata hai).

Server **har restart par OFF** ho jaata hai (ya `.env` me `PRABH_TOOLS_ON=1` likha ho to
ON). Matlab band karke chalao to phir se khud ON karna padega — ye jaan-boojh kar rakha
gaya hai.

## Teeno faisle

| Faisla | Kya hota hai | Example |
|---|---|---|
**SAFE** | Seedha chalta hai, ACTIVITY panel me dikhta hai | `get_time_date`, `system_info`, allowed folder me `list_dir` / `read_file`, `open_website` (http/https), list ki hui app kholna |
**ASK** | Screen par card aata hai — tumhe **ALLOW** ya **DENY** dabana hai | `write_file`, `run_command`, `delete_to_trash`, `close_app`, allowed folder ke bahar kuch bhi |
**BLOCKED** | Hamesha mana. Card nahi, command nahi | disk format/partition, `del C:\`, registry delete, `.env`/key files padhna-likhna, `-EncodedCommand`, `iwr ... \| iex`, `certutil -urlcache`, firewall band karna |

- **60 second me jawab na diya to apne aap DENY** ho jaata hai. Kuch bhi chalta nahi.
- Card ek hi waqt me rehta hai. Doosra card tab tak nahi banta.
- Allow **sirf UI button** se hota hai. Chat ya awaaz me "haan bol de" se kuch nahi hota.
- Sunday aur Prabh dono ka faisla **bilkul same** hota hai — farak sirf andaaz ka hai.

## Allowed jagahen

| Kaam | Kahan |
|---|---|
Sirf workspace | `D:\prabh_workspace` (config me badal sakta hai) |
Padhna (bina card) | workspace + Desktop + Downloads + Documents |
Workspace ke bahar | **Card aayega** (ASK) |

## Tools ki list

| Tool | Kya karta hai | Risk |
|---|---|---|
`get_time_date` | Date aur time | SAFE |
`system_info` | CPU, RAM, battery | SAFE |
`list_dir` | Folder ki listing | SAFE (allowed folder) / ASK (bahar) |
`read_file` | Text file padhta hai (UTF-8, **sirf 20 KB tak**) | SAFE (allowed) / ASK (bahar) |
`write_file` | File likhta hai (naya banata hai) | ASK |
`run_command` | PowerShell command (30 second limit) | ASK |
`open_website` | Browser me site kholta hai | SAFE (`http`/`https`) |
`open_app` | Config ki list me se app | SAFE (list me) / ASK (nahi) |
`close_app` | App band karta hai | ASK |
`delete_to_trash` | File/folder **Recycle Bin** me bhejta hai | ASK |

- Delete **hamesha Recycle Bin** me jaata hai. Permanent delete ka koi tool hi nahi hai.
- `read_file` binary file ya 20 KB se badi file refuse kar deta hai.
- `run_command` me `KEY` / `TOKEN` / `SECRET` / `PASSWORD` wale environment variables
  bilkul nahi jaate. Sirf `PATH`, `TEMP`, `USERPROFILE` jaise normal variables milte hain.

## ACTIVITY panel

Dayin taraf neeche **ACTIVITY** box me har tool ka hisaab rehta hai:

```
20:31:42  write_file   allow  live_test.txt
20:32:05  write_file   deny   60 second me jawab nahi aaya
```

Yahi `logs/actions.log` me bhi likha jaata hai.

## Suraksha ke niyam

1. **Key kabhi nahi dikhti.** `.env` ki asli key value, aur `gsk_` / `sk_` / `AIza` /
   `Bearer` / `api_key=` jaise pattern — tool output, log, ACTIVITY panel, confirm card
   aur LLM tak bheja gaya text, sab jagah `***` ho jaate hain.
2. **`.env` aur key files BLOCKED** hain — `read_file`, `write_file`, `list_dir`, koi bhi
   command, sab. `..`, `config\..`, `C:\PROGRA~1` (8.3 naam) aur junction se bhi nikal kar
   `.env` nahi padha ja sakta.
3. **Ek chhoti si window** — koi bhi tool ke liye tumse ek click zaroori hai jab wo
   BADALNA (write/delete/command) ho.
4. **UI me koi HTML text ki tarah nahi** — sab `textContent` se, plus strict CSP header.
5. **Tool output LLM ko DATA ki tarah** jaata hai; usme likha koi instruction follow
   nahi hota.
6. Ek request me **max 5 tool step** aur **minute me 20 request**.

## Server side endpoints

| Endpoint | Kaam |
|---|---|
`POST /tool/confirm` | Card ka jawab (`id` + `hash` + `allow`) |
`POST /tools/toggle` | Kill switch on/off |
`POST /tools/cancel` | Pending card + chal raha tool rok do |
`POST /tools/status` | Tools on ya off? |

Card ka hash **exact tool + args** ka SHA-256 hai. Galat hash, ya wahi hash dobara
(use/replay) — dono 409. Har card **ek baar** hi use hota hai.
