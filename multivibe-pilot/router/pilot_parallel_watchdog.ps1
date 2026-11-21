$ErrorActionPreference = 'Stop'
$mutex = New-Object System.Threading.Mutex($false, 'Local\MultiVibePilotGPT6Watchdog')
if (-not $mutex.WaitOne(0)) { exit 0 }
try {
    $script = Join-Path $PSScriptRoot 'pilot_parallel.py'
    $running = Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
        Where-Object { $_.CommandLine -and $_.CommandLine.Contains($script) } |
        Select-Object -First 1
    if ($running) { exit 0 }

    # A container without its supervisor cannot forward requests. Remove only
    # this instance's orphan; never touch the original pilot edge.
    $container = 'multivibe-pilot-gpt6'
    $existing = & docker ps -q --filter "name=^/${container}$" 2>$null
    if ($LASTEXITCODE -ne 0) { exit 1 }
    if ($existing) {
        & docker stop -t 3 $container *> $null
        if ($LASTEXITCODE -ne 0) { exit 1 }
    }
    $data = Join-Path $env:LOCALAPPDATA 'MultiVibe-Codex-Pilot'
    $out = Join-Path $data 'pilot-gpt6-service.log'
    $err = Join-Path $data 'pilot-gpt6-service.log.err'
    Start-Process -FilePath python -ArgumentList ('"' + $script + '"') `
        -RedirectStandardOutput $out -RedirectStandardError $err -WindowStyle Hidden
} finally {
    $mutex.ReleaseMutex()
    $mutex.Dispose()
}
