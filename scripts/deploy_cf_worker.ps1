# 部署 Cloudflare Worker + Vectorize 索引（需已安装 Node、已登录 wrangler）
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Worker = Join-Path $Root "cf-worker"

if (-not (Test-Path (Join-Path $Root ".env"))) {
    Write-Host "请先在仓库根目录创建 .env（可参考 .env.example）" -ForegroundColor Yellow
    exit 1
}

Get-Content (Join-Path $Root ".env") | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
        [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim().Trim('"'), "Process")
    }
}

if (-not $env:OPENAI_API_KEY) {
    Write-Host "请在 .env 中设置 OPENAI_API_KEY" -ForegroundColor Red
    exit 1
}

Push-Location $Worker
try {
    if (-not (Test-Path "node_modules")) { npm install }

    Write-Host "构建向量索引（可能较久）…"
    npm run build-index

    Write-Host "写入 Vectorize（若索引不存在请先: npx wrangler vectorize create psydrugs-wiki --dimensions=1536 --metric=cosine）"
    npm run insert-vectors

    Write-Host "上传 OPENAI_API_KEY 到 Worker Secrets…"
    $env:OPENAI_API_KEY | npx wrangler secret put OPENAI_API_KEY

    Write-Host "部署 Worker…"
    npm run deploy
    Write-Host "完成。将 psydrugs/source/search/index.md 中 data-rag-api 改为 workers.dev 地址。" -ForegroundColor Green
}
finally {
    Pop-Location
}
