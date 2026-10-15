---
name: busybox-on-windows
description: "How to use a Win32 build of BusyBox to run many of the standard UNIX command line tools on Windows."
risk: critical
source: community
date_added: "2026-02-27"
---

BusyBox is a single binary that implements many common Unix tools.

Use this skill only on Windows. If you are on UNIX, then stop here.

Run the following steps only if you cannot find a `busybox.exe` file in the same directory as this document is. 
These are PowerShell commands, if you have a classic `cmd.exe` terminal, then you must use `powershell -Command "..."` to run them.
1. Print the type of CPU: `Get-CimInstance -ClassName Win32_Processor | Select-Object Name, NumberOfCores, MaxClockSpeed`
2. Print the OS versions: `Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion" | Select-Object ProductName, DisplayVersion, CurrentBuild`
3. Download a suitable build of BusyBox by running one of these PowerShell commands:
   - 32-bit x86 (ANSI): `$ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri https://frippery.org/files/busybox/busybox.exe -OutFile busybox.exe`
   - 64-bit x86 (ANSI): `$ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri https://frippery.org/files/busybox/busybox64.exe -OutFile busybox.exe`
   - 64-bit x86 (Unicode): `$ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri https://frippery.org/files/busybox/busybox64u.exe -OutFile busybox.exe`
   - 64-bit ARM (Unicode): `$ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri https://frippery.org/files/busybox/busybox64a.exe -OutFile busybox.exe`

Before executing a downloaded binary, obtain the expected release digest from an independently verified publisher channel and compare `Get-FileHash -Algorithm SHA256`. A computed hash alone does not authenticate the download. If the publisher evidence cannot be checked, report that installation is unverified and do not execute it. Save outside the immutable skill bundle and do not overwrite an existing binary.

PowerShell does not implicitly execute a file in the current directory; use `./busybox.exe` or `& "C:\approved\path\busybox.exe"`. Review the applet's filesystem effects before running it.

Useful commands:
- Help: `./busybox.exe --list`
- Available UNIX commands: `./busybox.exe --list`

Usage: Prefix the UNIX command with `busybox.exe`, for example: `./busybox.exe ls -1`

If you need to run a UNIX command under another CWD, then use the absolute path to `busybox.exe`.

Documentation: https://frippery.org/busybox/
Original BusyBox: https://busybox.net/

## When to Use
Use when an authorized Windows task needs Unix-style applets without WSL, and an architecture-compatible reviewed BusyBox binary is available.

## Example

**User request:**

> Use @busybox-on-windows for this task: How to use a Win32 build of BusyBox to run many of the standard UNIX command line tools on Windows.

## Limitations
- Use this skill only when the task clearly matches the scope described above.
- Do not treat the output as a substitute for environment-specific validation, testing, or expert review.
- Stop and ask for clarification if required inputs, permissions, safety boundaries, or success criteria are missing.
