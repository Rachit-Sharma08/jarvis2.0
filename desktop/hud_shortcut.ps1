# "Sunday HUD" shortcut banao ya hatao - sirf ek kaam.
#
# Python se hi chalaaya jaata hai (`desktop/shortcut.py`). WScript.Shell
# (Windows ka apna COM) `.lnk` likhta hai, is liye koi package nahi lagta.
#
# Ye .bat NAHI hai, is liye CRLF ka pakkaura zaroori nahi - par file chhoti
# aur ASCII rakhi hai. Bracket ki koi parwah nahi (PowerShell par sahi hai).

param(
  [Parameter(Mandatory=$true)][string]$Mode,
  [Parameter(Mandatory=$true)][string]$Link,
  [string]$Target = '',
  [string]$ArgLine = '',
  [string]$WorkDir = '',
  [string]$Icon = '',
  [string]$Desc = ''
)

$ErrorActionPreference = 'Stop'

switch ($Mode) {

  'install' {
    $shell = New-Object -ComObject WScript.Shell
    $sc = $shell.CreateShortcut($Link)
    $sc.TargetPath = $Target
    $sc.Arguments = $ArgLine
    if ($WorkDir -ne '') { $sc.WorkingDirectory = $WorkDir }
    if ($Icon -ne '') { $sc.IconLocation = $Icon }
    $sc.Description = $Desc
    $sc.WindowStyle = 7
    $sc.Save()
    Write-Output 'ok'
  }

  'remove' {
    if (Test-Path -LiteralPath $Link) {
      Remove-Item -LiteralPath $Link -Force
      Write-Output 'ok'
    } else {
      Write-Output 'missing'
    }
  }

  'status' {
    if (Test-Path -LiteralPath $Link) { Write-Output 'ok' } else { Write-Output 'missing' }
  }

  default {
    Write-Error ("Mode nahi pata: " + $Mode)
    exit 1
  }
}