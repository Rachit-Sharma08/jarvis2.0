"""Path ki jaanch: ..\\..\\, symlink/junction, case, 8.3 naam, drive root, .env.

`resolve()` se path hamesha asli (real) path ban jaata hai, isliye `..`,
symlink aur junction se bahar nikalna possible nahi.
"""

import os
import re
from pathlib import Path

import config

_SHORT_NAME = re.compile(r"~[0-9]")


def resolve(raw: str) -> Path:
    """Text ko asli absolute path banao. Naam se pehle expand karke resolve."""
    text = str(raw).strip().strip('"')
    path = Path(text).expanduser()
    if not path.is_absolute():
        path = config.WORKSPACE / path
    return Path(os.path.normpath(str(path))).resolve()


def is_drive_root(path: Path) -> bool:
    return str(path).rstrip("\\/") == path.anchor.rstrip("\\/")


def has_short_name(path: Path) -> bool:
    """8.3 trick: C:\\PROGRA~1\\ ... ko hamesha block karo."""
    return any(_SHORT_NAME.search(part) for part in path.parts)


def is_secret_file(path: Path) -> bool:
    name = path.name.lower()
    return name in config.SECRET_FILE_NAMES or name.startswith(".env")


def blocked_reason(path: Path, raw: str = "") -> str:
    """Path BLOCKED hai to wajah, warna khaali string. Raw aur resolved dono dekhte hain."""
    if is_drive_root(path):
        return "drive root"
    if has_short_name(path) or (raw and has_short_name(Path(raw))):
        return "8.3 short-name trick"
    if is_secret_file(path):
        return ".env / key wali file"
    protected = config.PROTECTED_FOLDER_NAMES
    for part in list(path.parts) + (list(Path(raw).parts) if raw else []):
        if part.strip().lower() in protected:
            return f"protected folder ({part})"
    low = os.path.normcase(str(path))
    for root in config.BLOCKED_ROOTS:
        root_text = os.path.normcase(str(root))
        if low == root_text or low.startswith(root_text + os.sep):
            return f"protected folder ({root.name})"
    return ""


def within(path: Path, folders: tuple) -> bool:
    low = os.path.normcase(str(path))
    for folder in folders:
        base = os.path.normcase(os.path.normpath(str(Path(folder))))
        if low == base or low.startswith(base + os.sep):
            return True
    return False


def is_readable(path: Path) -> bool:
    return within(path, config.READ_FOLDERS)


def is_workspace(path: Path) -> bool:
    return within(path, (config.WORKSPACE,))
