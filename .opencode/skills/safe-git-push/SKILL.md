---
name: safe-git-push
description: Push se pehle author email + key scan, force-push kabhi nahi, main me merge nahi
---

# Safe git push

## Pehle ye do check (har push se pehle)

1. **Author email** — naye commits sab isi email ke hone chahiye:
   `git log --format="%ae" origin/main..HEAD`
   Sab `339157645+Rachit-Sharma08@users.noreply.github.com` honi chahiye.
2. **Key scan** — `git log -p origin/main..HEAD` me ye pattern gino:
   `gsk_`, `sk_`, `sk-`, `AIza`. **Sirf ginti batao**, koi line print mat
   karo. Sab 0 hona chahiye.

## Niyam

- `git push -u origin <branch>` — sirf apni branch. **main push nahi.**
- **Force-push kabhi nahi.** History kabhi mat badlo.
- **main me merge nahi** — branch par kaam, push, bas.
- Login/permission maange to **ruk jao**. Password/token kabhi mat maango,
  credential/account kabhi mat badlo.
- Git identity: global config (Rachit Sharma + noreply) chalegi.
  Kabhi `-c user.name`, `--author`, ya local user config mat lagao.
- Commit message file se do (`git commit -F <file>`) — shell quoting se
  PowerShell me message toot jaata hai.
