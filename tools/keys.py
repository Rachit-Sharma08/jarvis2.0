"""Kisi app ko foreground laa kar ek key bhejo (WScript.Shell).

Pehle dekhte hain ki app **pehle se foreground** hai — tab AppActivate nahi
chalate (wo ek process ki doosri window pakad sakta hai, jaise VS Code ki purani
window). Warna `AppActivate` best-effort hai; fail par `False`, crash nahi.
"""

from tools.quick import _ps

_PS = r"""
$ErrorActionPreference = 'SilentlyContinue'
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class JarvisFg {
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint pid);
}
"@
$fgPid = 0
[void][JarvisFg]::GetWindowThreadProcessId([JarvisFg]::GetForegroundWindow(), [ref]$fgPid)
$fgName = (Get-Process -Id $fgPid).ProcessName
$names = @(%s)
$shell = New-Object -ComObject WScript.Shell
if ($names -contains $fgName) {
  $shell.SendKeys('%s')
  'ok'
  exit 0
}
foreach ($n in $names) {
  $p = Get-Process -Name $n | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
  if ($p -and $shell.AppActivate($p.Id)) {
    Start-Sleep -Milliseconds 300
    $shell.SendKeys('%s')
    'ok'
    exit 0
  }
}
'no-window'
"""


def send_key(names: tuple, key: str) -> bool:
    """App foreground ho to seedha key, warna focus karke. -> True/False."""
    quoted = ", ".join("'%s'" % name for name in names)
    return _ps(_PS % (quoted, key, key), timeout=15).strip() == "ok"
