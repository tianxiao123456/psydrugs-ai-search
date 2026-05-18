# 单次或定时同步 KrvyFT/psydrugs.org -> 本地 psydrugs/
# 用法:
#   .\scripts\sync_psydrugs_upstream.ps1
#   .\scripts\sync_psydrugs_upstream.ps1 -IntervalHours 6

param(
    [double]$IntervalHours = 0,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command py -ErrorAction SilentlyContinue }
if (-not $py) {
    Write-Error "未找到 python/py"
    exit 1
}

$argsList = @("$PSScriptRoot\sync_psydrugs_upstream.py")
if ($IntervalHours -gt 0) {
    $argsList += @("--interval", "$IntervalHours")
}
if ($DryRun) {
    $argsList += "--dry-run"
}

& $py.Path @argsList
