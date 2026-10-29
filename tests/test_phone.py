"""Phone tool (Artemis) ka dhaancha — koi asli adb/phone call nahi.

`tools/phone.py` ka `_run` fake se badalta hai, is liye test me `uv`/Artemis
kabhi nahi chalta. Yahan sirf command ka shape, jawab nikalna, aur gatekeeper
ka faisla check hota hai. Asli phone test owner ke haath se hota hai.
"""
import inspect
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config  # noqa: E402
import tools  # noqa: E402
from gatekeeper import nocards, rules  # noqa: E402
from tools import phone  # noqa: E402

FAILED = []
OK_OUT = """info Artemis started
report_task_status({'status': 'completed', 'explanation': 'Settings khula, battery 64% hai.'})
done
"""


def check(name, got, want):
    if got == want:
        print(f"  OK   {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL {name} -> got {got!r}, want {want!r}")


class Res:
    def __init__(self, stdout="", stderr=""):
        self.stdout, self.stderr, self.returncode = stdout, stderr, 0


def fake(out="", boom=None):
    calls = []

    def run(cmd, timeout, cwd):
        calls.append((cmd, timeout, cwd))
        if boom:
            raise boom
        return Res(out)

    return run, calls


def main():
    print("PHONE: command ka shape")
    cmd = phone._command("Karun ko call karo")
    check("argv list (shell nahi)", cmd[:5], ["uv", "run", "artemis", "run", "Karun ko call karo"])
    check("profile flag", cmd[-2:], ["--profile", phone.config_phone.ARTEMIS_PROFILE])
    check("shell=False code me", "shell=False" in inspect.getsource(phone._run), True)
    check("text me & / ; se command nahi banti", phone._command("a & calc; x")[4], "a & calc; x")

    print("PHONE: jawab nikalna")
    check("explanation", phone._answer(OK_OUT), "Settings khula, battery 64% hai.")
    check("double quote wala explanation",
          phone._answer('{"explanation": "Battery 64% hai."}'), "Battery 64% hai.")
    check("kuch na mile to khaali", phone._answer("no report here"), "")

    print("PHONE: har raasta ek saaf line")
    run, calls = fake(OK_OUT)
    phone._run = run
    check("kaam hua", phone.phone_task("battery batao"), "Phone: Settings khula, battery 64% hai.")
    check("goal saaf bheja", calls[0][0][4], "battery batao")
    check("cwd Artemis", calls[0][2], phone.config_phone.ARTEMIS_DIR)

    run, _ = fake("error: no devices/emulators found")
    phone._run = run
    check("phone connect nahi", phone.phone_task("call karo"),
          "Phone connect nahi hai — USB ya wireless debugging on karo.")

    boom = subprocess.TimeoutExpired("uv", phone.config_phone.PHONE_TIMEOUT_SECONDS)
    run, _ = fake(boom=boom)
    phone._run = run
    check("timeout", str(phone.config_phone.PHONE_TIMEOUT_SECONDS) in phone.phone_task("call"),
          True)

    run, _ = fake(boom=FileNotFoundError())
    phone._run = run
    check("uv nahi mila", "Artemis nahi mila" in phone.phone_task("call"), True)

    run, _ = fake("kuch samajh nahi aaya")
    phone._run = run
    check("bina jawab", "saaf jawab nahi mila" in phone.phone_task("call"), True)

    run, _ = fake("Android secure keyguard is locked. Unlock the device manually")
    phone._run = run
    check("phone locked hai", "Phone locked hai" in phone.phone_task("battery batao"), True)

    called = []
    phone._run = lambda *a: called.append(a) or Res(OK_OUT)
    check("khaali task par sawaal", phone.phone_task(""),
          "Phone par kya karna hai? (jaise 'Karun ko call karo')")
    check("khaali task par phone nahi chala", called, [])

    print("PHONE: registry + gatekeeper")
    check("TOOLS me", "phone_task" in tools.TOOLS, True)
    check("args", tools.TOOL_ARGS["phone_task"], ("task",))
    check("visible", "phone_task" in tools.visible(), True)
    check("spec me", "phone_task(task)" in tools.spec(), True)
    check("risk ASK", rules.decide("phone_task", {"task": "call"})[0], config.ASK)
    check("nocards allow (awaaz se chale)", nocards.resolve_ask("phone_task", {"task": "call"}),
          (nocards.ALLOW, None))
    check("prompt me phone rule", "phone_task(task)" in
          __import__("brain.prompt", fromlist=["build"]).build("p", True), True)


with __import__("tests.datasafe", fromlist=["isolated_data"]).isolated_data():
    main()

if FAILED:
    print(f"{len(FAILED)} test fail: {FAILED}")
    sys.exit(1)
print("Phone tool test pass.")
