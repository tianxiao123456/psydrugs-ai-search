# 构建 Chroma 向量索引（需已配置 .env 中的 EMBEDDING_API_KEY）
param([switch]$Force)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command py -ErrorAction SilentlyContinue }
if (-not $py) { Write-Error "未找到 python"; exit 1 }
$argsList = @("-m", "ai_search", "index")
if ($Force) { $argsList += "--force" }
& $py.Path @argsList
