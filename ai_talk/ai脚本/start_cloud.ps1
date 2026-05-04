# 一键启动：加载 cloud.env 后运行 Cloud Agent 生成流水线
# 用法：右键「使用 PowerShell 运行」或在终端执行:
#   .\start_cloud.ps1
# 传递参数给生成脚本:
#   .\start_cloud.ps1 --max-batches 1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$envFile = Join-Path $PSScriptRoot "cloud.env"
if (-not (Test-Path $envFile)) {
    Write-Host "ERROR: cloud.env missing. Copy cloud.env.example to cloud.env and set CURSOR_API_KEY." -ForegroundColor Red
    exit 1
}

Get-Content $envFile | ForEach-Object {
    $line = $_.Trim()
    if ($line -match '^\s*#' -or $line -eq "") { return }
    $eq = $line.IndexOf("=")
    if ($eq -lt 1) { return }
    $name = $line.Substring(0, $eq).Trim()
    $val = $line.Substring($eq + 1).Trim()
    Set-Item -Path "env:$name" -Value $val
}

if (-not $env:CURSOR_API_KEY) {
    Write-Host "ERROR: CURSOR_API_KEY not set in cloud.env." -ForegroundColor Red
    exit 1
}
if (-not $env:CURSOR_CLOUD_REPO_URL) {
    Write-Host "ERROR: CURSOR_CLOUD_REPO_URL not set in cloud.env." -ForegroundColor Red
    exit 1
}

Write-Host ("INFO: Cloud mode  branch={0}  repo={1}" -f $env:CURSOR_CLOUD_REF, $env:CURSOR_CLOUD_REPO_URL) -ForegroundColor Cyan
Write-Host "INFO: Stop with STOP file in this folder, or Ctrl+C" -ForegroundColor Gray

$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command py -ErrorAction SilentlyContinue }
if (-not $py) {
    Write-Host "ERROR: python/py not found. Install Python." -ForegroundColor Red
    exit 1
}

& $py.Path "$PSScriptRoot\generate_dataset.py" @args
