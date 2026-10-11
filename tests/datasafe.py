"""Tests ko asli `data/` se door rakhne wala helper (E-1b).

Test ke dauran data-folder + memory/audit/todos/reminders/kb/notes ke path ek
temp folder par; khatam hote hi wapas. Guard: koi path asli `data/` ke andar
gir gaya to AssertionError - taaki test chup-chaap asli memory.json na mita sake.

    with isolated_data() as tmp: ...   # plain test
    class Meri(DataSafeCase): ...      # unittest (setUp/tearDown)
"""
import shutil, sys, tempfile, unittest
from contextlib import contextmanager
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config  # noqa: E402
from core import memory as _mem, summarizer as _sum  # noqa: E402
from tools import kb as _kb, notes as _nt, pomodoro as _pm  # noqa: E402
from tools import reminders as _rm, rss as _rs, todo as _td  # noqa: E402


@contextmanager
def isolated_data():
    """App ke saare `data/` raaste ek temp folder par - ek `with` block me."""
    real = config.DATA_DIR  # patch se PEHLE asli folder pakad lo
    tmp = Path(tempfile.mkdtemp(prefix="prabh-test-"))
    plan = [(config, "DATA_DIR", tmp), (config, "ACTION_LOG", tmp / "actions.log"),
            (_mem, "DATA_DIR", tmp), (_mem, "MEM_FILE", tmp / "memory.json"),
            (_mem, "SUM_FILE", tmp / "memory_summary.txt"), (_sum, "SUM_FILE", tmp / "memory_summary.txt"),
            (_kb, "KB_DIR", tmp / "kb")]
    for mod, fname, attr in ((_td, "todos.json", "TFILE"), (_rm, "reminders.json", "RFILE"),
                             (_nt, "notes.json", "NFILE"), (_rs, "rss_feeds.json", "RFILE"),
                             (_pm, "pomodoro.json", "PFILE")):
        plan += [(mod, "DATA_DIR", tmp), (mod, attr, tmp / fname)]
    saved = []
    try:
        for mod, attr, value in plan:
            home, here = real.resolve(), Path(value).resolve()
            if here == home or home in here.parents:
                raise AssertionError(f"datasafe: {attr} asli data/ me gir gaya: {here}")
            saved.append((mod, attr, getattr(mod, attr)))
            setattr(mod, attr, value)
        saved.append((_mem.MEM, "_items", list(_mem.MEM._items)))
        _mem.MEM._items = []  # memory khaali - asli file ko chhue bina
        yield tmp
    finally:
        for obj, attr, old in reversed(saved):
            setattr(obj, attr, old)
        shutil.rmtree(tmp, ignore_errors=True)


class DataSafeCase(unittest.TestCase):
    def setUp(self):
        self._ctx = isolated_data()
        self.data_dir = self._ctx.__enter__()

    def tearDown(self):
        self._ctx.__exit__(None, None, None)
