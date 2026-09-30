"""SAFE tools: time/date aur system info. Koi file, koi command nahi."""

import ctypes
import os
import platform
from datetime import datetime

import config


def get_time_date() -> str:
    now = datetime.now()
    return f"{now.strftime('%A, %d %B %Y, %I:%M %p')} (IST, {now.astimezone().tzname()})"


class _MemStatus(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


class _PowerStatus(ctypes.Structure):
    _fields_ = [
        ("ACLineStatus", ctypes.c_byte),
        ("BatteryFlag", ctypes.c_byte),
        ("BatteryLifePercent", ctypes.c_byte),
        ("Reserved1", ctypes.c_byte),
        ("BatteryLifeTime", ctypes.c_ulong),
        ("BatteryFullLifeTime", ctypes.c_ulong),
    ]


def _ram() -> str:
    try:
        status = _MemStatus()
        status.dwLength = ctypes.sizeof(_MemStatus)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
        used = (status.ullTotalPhys - status.ullAvailPhys) / 1024 ** 3
        return f"{used:.1f} GB / {status.ullTotalPhys / 1024 ** 3:.1f} GB ({status.dwMemoryLoad}%)"
    except Exception:
        return "pata nahi chala"


def _battery() -> str:
    try:
        power = _PowerStatus()
        if not ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(power)):
            return "pata nahi chala"
        if power.BatteryFlag in (1, 255) or power.BatteryLifePercent in (255, -1):
            return "is PC me battery nahi (plugged)"
        state = "charging" if power.ACLineStatus == 1 else "on battery"
        return f"{power.BatteryLifePercent}% ({state})"
    except Exception:
        return "pata nahi chala"


def system_info() -> str:
    return (
        f"CPU: {os.cpu_count()} cores ({platform.processor() or 'x64'})\n"
        f"RAM: {_ram()}\n"
        f"Battery: {_battery()}\n"
        f"System: {platform.system()} {platform.release()}\n"
        f"Workspace: {config.WORKSPACE}"
    )
