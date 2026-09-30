"""Har stage ka time. Ek hi jagah: STT, brain, TTS aur total."""

import time

from log_setup import get_logger

log = get_logger("timing")


def ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)


class Stopwatch:
    """Total + stage times. Upar wala total, andar har stage."""

    def __init__(self, name: str = "request"):
        self.name = name
        self.start = time.perf_counter()
        self.stages = []

    def stage(self, label: str, start: float) -> int:
        took = ms(start)
        self.stages.append((label, took))
        log.info("TIME %s: %s %dms (total %dms)", self.name, label, took, ms(self.start))
        return took

    def total(self) -> int:
        took = ms(self.start)
        detail = " ".join(f"{label}={value}ms" for label, value in self.stages) or "-"
        log.info("TIME %s: TOTAL %dms | %s", self.name, took, detail)
        return took
