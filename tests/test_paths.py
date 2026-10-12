"""Path normalisation ke safety test: traversal, case, 8.3, junction, drive root.

Koi file delete/overwrite nahi hoti — sirf `paths` ke faisle check hote hain.
"""

import os
import subprocess
import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config
from gatekeeper import paths


class PathsTest(unittest.TestCase):
    def test_resolve_joins_and_keeps_within(self):
        inside = paths.resolve(str(config.WORKSPACE / "a" / ".." / "b.txt"))
        self.assertEqual(config.WORKSPACE / "b.txt", inside)
        self.assertTrue(paths.is_readable(inside))

    def test_case_insensitive(self):
        upper = paths.resolve(str(config.WORKSPACE).upper() + "\\x.txt")
        self.assertTrue(paths.is_workspace(upper), "case change se bahar nahi jaana chahiye")

    def test_short_name_trick(self):
        self.assertTrue(paths.has_short_name(Path(r"C:\PROGRA~1\x")))

    def test_drive_root(self):
        self.assertTrue(paths.is_drive_root(Path("C:/")))

    def test_symlink_out_of_workspace(self):
        """Junction se bahar nikalna band hona chahiye (admin ki zarurat nahi)."""
        base = Path(os.environ.get("TEMP", ".")) / "prabh_junction_test"
        outside = Path(os.environ.get("TEMP", ".")) / "prabh_outside_test"
        for folder in (base, outside):
            folder.mkdir(parents=True, exist_ok=True)
        link = base / "link_out"
        made = True
        try:
            if not link.exists():
                made = (
                    subprocess.run(
                        ["cmd", "/c", "mklink", "/J", str(link), str(outside)],
                        capture_output=True,
                        timeout=20,
                    ).returncode
                    == 0
                )
        except Exception:
            made = False
        if not made:
            self.skipTest("is PC par junction nahi ban payi")
        try:
            resolved = paths.resolve(str(link / "secret.txt"))
            self.assertFalse(
                paths.is_workspace(resolved) and not paths.is_workspace(outside / "secret.txt"),
                "junction se workspace me rehna chahiye tha",
            )
        finally:
            try:
                subprocess.run(["cmd", "/c", "rmdir", str(link)], capture_output=True, timeout=20)
            except Exception:
                pass


if __name__ == "__main__":
    unittest.main(verbosity=1)
