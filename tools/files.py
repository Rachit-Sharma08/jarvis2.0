"""Folder/file tools. Gatekeeper se guzkar hi yahan aate hain.

read_file sirf TEXT: 20 KB tak, binary mana. delete hamesha Recycle Bin me.
"""

from pathlib import Path

import config
from gatekeeper import paths

MAX_ENTRIES = 200


def list_dir(path: str) -> str:
    folder = paths.resolve(path)
    if not folder.is_dir():
        return f"ye folder nahi mila: {folder}"
    rows = []
    for item in sorted(folder.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
        if len(rows) >= MAX_ENTRIES:
            rows.append(f"... aur {len(list(folder.iterdir())) - MAX_ENTRIES} hain")
            break
        rows.append(f"{item.name}{'/' if item.is_dir() else ''}")
    return f"{folder}\n" + ("\n".join(rows) if rows else "(khaali folder)")


def read_file(path: str) -> str:
    target = paths.resolve(path)
    if not target.is_file():
        return f"ye file nahi mili: {target}"
    size = target.stat().st_size
    if size > config.READ_FILE_MAX_BYTES:
        return (
            f"file {size} bytes ki hai, {config.READ_FILE_MAX_BYTES} se badi hai. "
            "Sirf chhoti text file hi padhi ja sakti hai."
        )
    data = target.read_bytes()
    if b"\x00" in data:
        return "ye binary file hai (image/exe/pdf). Sirf text file padhi ja sakti hai."
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return "ye file text nahi hai (encoding alag hai). Sirf plain text padhi ja sakti hai."
    return f"--- {target} ({size} bytes) ---\n{text}"


def write_file(path: str, content: str) -> str:
    target = paths.resolve(path)
    if not target.parent.is_dir():
        return f"folder nahi mila: {target.parent}. Naya folder banane ke liye mujhe pucho."
    existed = target.exists()
    try:
        target.write_text(content, encoding="utf-8")
    except Exception as exc:
        return f"likh nahi paya: {type(exc).__name__}: {exc}"
    return f"{'badli' if existed else 'bana'} ({len(content)} characters): {target}"


def delete_to_trash(path: str) -> str:
    target = paths.resolve(path)
    if not target.exists():
        return f"ye cheez nahi mili: {target}"
    from send2trash import send2trash  # halka import, tabhi chahiye

    send2trash(str(target))
    return f"Recycle Bin me bhej diya: {target}. (permanent delete kabhi nahi hota)"
