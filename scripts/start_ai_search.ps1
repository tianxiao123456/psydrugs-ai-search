# 启动 AI 搜索 Web 服务（需已 index 且配置 .env）
param(
    [string]$ListenHost = "127.0.0.1",
    [int]$Port = 8000
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command py -ErrorAction SilentlyContinue }
if (-not $py) { Write-Error "未找到 python"; exit 1 }
Write-Host "Open http://${ListenHost}:${Port}/ in browser"
& $py.Path -m ai_search serve --host $ListenHost --port $Port
