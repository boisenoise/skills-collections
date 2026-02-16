# Prevent Windows sleep while pipeline is active
# Uses SetThreadExecutionState (kernel32.dll) — official Windows Power API
# https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate
#
# Lifecycle:
#   Phase 3 starts this script as background process
#   Script polls .pipeline/state.json every 30s
#   When complete=true or file disappears -> releases sleep block and exits
#   If script crashes -> Windows auto-releases execution state (tied to process)
#
# Verify: powercfg /requests (shows SYSTEM request while running)

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class SleepPreventer {
    [DllImport("kernel32.dll")]
    public static extern uint SetThreadExecutionState(uint esFlags);
    public const uint ES_CONTINUOUS = 0x80000000;
    public const uint ES_SYSTEM_REQUIRED = 0x00000001;
}
"@

# Block sleep: ES_CONTINUOUS | ES_SYSTEM_REQUIRED
[SleepPreventer]::SetThreadExecutionState(
    [SleepPreventer]::ES_CONTINUOUS -bor [SleepPreventer]::ES_SYSTEM_REQUIRED
) | Out-Null

# Poll .pipeline/state.json until complete=true or file disappears
$stateFile = ".pipeline/state.json"
while ($true) {
    Start-Sleep -Seconds 30
    if (-not (Test-Path $stateFile)) { break }
    try {
        $state = Get-Content $stateFile -Raw | ConvertFrom-Json
        if ($state.complete -eq $true) { break }
    } catch {
        # JSON parse error (file being written) — retry next cycle
        continue
    }
}

# Release: ES_CONTINUOUS only (clears SYSTEM_REQUIRED)
[SleepPreventer]::SetThreadExecutionState(
    [SleepPreventer]::ES_CONTINUOUS
) | Out-Null
