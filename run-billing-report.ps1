param(
  [Parameter(Mandatory=$true)][string]$Root,
  [Parameter(Mandatory=$true)][string]$WatcherUrl,
  [Parameter(Mandatory=$true)][string]$WriterUrl
)
$ErrorActionPreference = "Stop"
$base = "http://127.0.0.1:8001"

Write-Host "Esperando a que arranque el analizador..."
$ready = $false
for ($i = 0; $i -lt 60; $i++) {
  try {
    Invoke-RestMethod -Uri "$base/health" -TimeoutSec 2 | Out-Null
    $ready = $true
    break
  } catch {
    Start-Sleep -Seconds 2
  }
}
if (-not $ready) { throw "El analizador no responde en $base. Comprueba su ventana." }

$payload = @{
  name = "Billing Watcher + Report Writer"
  repositories = @(
    @{ name = "rft-billing-watcher"; git_url = $WatcherUrl }
    @{ name = "rft-billing-report-writer"; git_url = $WriterUrl }
  )
} | ConvertTo-Json -Depth 5

Write-Host "Enviando los dos repositorios para analisis..."
$created = Invoke-RestMethod -Method Post -Uri "$base/api/analysis-groups" -ContentType "application/json" -Body $payload
$id = $created.analysis_group_id
if (-not $id) { throw "La API no devolvio analysis_group_id." }

Write-Host "Analisis iniciado: $id"
Write-Host "Esperando a que termine el analisis de ambos microservicios..."
$done = $false
for ($i = 0; $i -lt 360; $i++) {
  Start-Sleep -Seconds 5
  $status = Invoke-RestMethod -Uri "$base/api/analysis-groups/$id"
  Write-Host ("Estado: " + $status.status)
  if ($status.status -in @("ANALYSIS_COMPLETED", "PARTIAL_ANALYSIS_COMPLETED")) {
    $done = $true
    break
  }
  if ($status.status -eq "FAILED") {
    throw ("El analisis fallo: " + $status.last_error)
  }
}
if (-not $done) { throw "Tiempo de espera agotado. El analisis puede seguir ejecutandose; ID: $id" }

$out = Join-Path $Root ("billing-analysis-" + $id + ".html")
Invoke-WebRequest -Uri "$base/api/analysis-groups/$id/report.html" -OutFile $out
if (-not (Test-Path $out)) { throw "No se ha creado el HTML." }

Write-Host ""
Write-Host "Informe generado: $out" -ForegroundColor Green
Start-Process $out
