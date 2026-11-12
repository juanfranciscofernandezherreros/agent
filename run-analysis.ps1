[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $Root

function Read-DotEnv([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "No existe .env. Copia .env.example a .env y configura GITLAB_TOKEN y GITLAB_GROUP_ID."
    }
    foreach ($line in Get-Content -LiteralPath $Path) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#")) { continue }
        if ($trimmed -match '^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') {
            $key = $Matches[1]
            $value = $Matches[2].Trim()
            if (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) {
                $value = $value.Substring(1, $value.Length - 2)
            }
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
}

function Invoke-ApiJson([string]$Uri, [string]$Method = "GET", $Body = $null) {
    if ($null -ne $Body) {
        return Invoke-RestMethod -Uri $Uri -Method $Method -ContentType "application/json" -Body ($Body | ConvertTo-Json -Compress)
    }
    return Invoke-RestMethod -Uri $Uri -Method $Method
}

try {
    Write-Host ""
    Write-Host "=== Analizador de arquitectura y calidad de microservicios ===" -ForegroundColor Cyan
    Read-DotEnv (Join-Path $Root ".env")

    $Token = [Environment]::GetEnvironmentVariable("GITLAB_TOKEN", "Process")
    $GroupId = [Environment]::GetEnvironmentVariable("GITLAB_GROUP_ID", "Process")
    $BaseUrl = [Environment]::GetEnvironmentVariable("GITLAB_BASE_URL", "Process")
    if ([string]::IsNullOrWhiteSpace($Token)) { throw "GITLAB_TOKEN no está configurado en .env." }
    if ([string]::IsNullOrWhiteSpace($GroupId)) { throw "GITLAB_GROUP_ID no está configurado en .env." }
    if ([string]::IsNullOrWhiteSpace($BaseUrl)) { $BaseUrl = "https://gitlab.com" }

    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "Git no está instalado o no está disponible en PATH." }
    if (-not (Get-Command curl.exe -ErrorAction SilentlyContinue)) { throw "No se encuentra curl.exe." }

    $Python = Join-Path $Root ".venv\Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $Python)) {
        Write-Host "Preparando entorno Python e instalando dependencias..." -ForegroundColor Yellow
        & (Join-Path $Root "setup-windows.ps1")
        if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) { throw "Falló la preparación del entorno Python." }
    }
    if (-not (Test-Path -LiteralPath $Python)) { throw "No se ha podido crear el entorno .venv." }

    $Api = "http://127.0.0.1:8001"
    $Health = $false
    try { $null = Invoke-RestMethod -Uri "$Api/health" -TimeoutSec 3; $Health = $true } catch { $Health = $false }

    if (-not $Health) {
        Write-Host "Iniciando API local en el puerto 8001..." -ForegroundColor Yellow
        $Logs = Join-Path $Root "logs"
        New-Item -ItemType Directory -Force -Path $Logs | Out-Null
        Start-Process -FilePath $Python -ArgumentList @("-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8001") -WorkingDirectory $Root -WindowStyle Hidden -RedirectStandardOutput (Join-Path $Logs "api.stdout.log") -RedirectStandardError (Join-Path $Logs "api.stderr.log") | Out-Null
        $Ready = $false
        for ($i = 0; $i -lt 60; $i++) {
            Start-Sleep -Seconds 2
            try { $null = Invoke-RestMethod -Uri "$Api/health" -TimeoutSec 3; $Ready = $true; break } catch { }
        }
        if (-not $Ready) { throw "La API no respondió en 120 segundos. Revisa logs/api.stderr.log." }
    }

    $Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $AnalysisName = [Environment]::GetEnvironmentVariable("ANALYSIS_NAME", "Process")
    if ([string]::IsNullOrWhiteSpace($AnalysisName)) { $AnalysisName = "gitlab-group-$GroupId-$Timestamp" }
    if ($AnalysisName.Length -gt 120) { $AnalysisName = $AnalysisName.Substring(0,120) }

    Write-Host "Grupo GitLab: $GroupId" -ForegroundColor Cyan
    Write-Host "Nombre del análisis: $AnalysisName"
    $EncodedGroup = [uri]::EscapeDataString($GroupId)
    $Start = Invoke-ApiJson -Uri "$Api/api/gitlab/groups/$EncodedGroup/analysis" -Method "POST" -Body @{ name = $AnalysisName }
    $AnalysisGroupId = $Start.analysis_group_id
    if ([string]::IsNullOrWhiteSpace([string]$AnalysisGroupId)) { throw "La API no devolvió analysis_group_id." }

    Write-Host "Trabajo: $AnalysisGroupId"
    Write-Host "Repositorios descubiertos: $($Start.repository_count)"
    $FinalStatus = $null
    $Deadline = (Get-Date).AddHours(6)
    while ((Get-Date) -lt $Deadline) {
        Start-Sleep -Seconds 5
        $Status = Invoke-ApiJson -Uri "$Api/api/analysis-groups/$AnalysisGroupId"
        $FinalStatus = $Status.status
        if ($FinalStatus -in @("ANALYSIS_COMPLETED","PARTIAL_ANALYSIS_COMPLETED","FAILED")) { break }
        Write-Host ("Estado: {0}" -f $FinalStatus)
    }
    if ($FinalStatus -notin @("ANALYSIS_COMPLETED","PARTIAL_ANALYSIS_COMPLETED","FAILED")) { throw "El análisis superó el tiempo máximo de seis horas. ID: $AnalysisGroupId" }
    if ($FinalStatus -eq "FAILED") {
        $Reason = $Status.last_error
        if (-not $Reason) { $Reason = "El servidor marcó el análisis como FAILED." }
        throw $Reason
    }

    $ReportDirValue = [Environment]::GetEnvironmentVariable("REPORT_DIR", "Process")
    if ([string]::IsNullOrWhiteSpace($ReportDirValue)) { $ReportDirValue = "reports" }
    $ReportDir = Join-Path $Root $ReportDirValue
    New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
    $SafeName = ($AnalysisName -replace '[^A-Za-z0-9._-]+','-').Trim('-')
    if ([string]::IsNullOrWhiteSpace($SafeName)) { $SafeName = "analysis" }
    $ReportPath = Join-Path $ReportDir "$SafeName-$Timestamp.html"

    Write-Host "Descargando informe HTML principal..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri "$Api/api/analysis-groups/$AnalysisGroupId/report.html" -OutFile $ReportPath -UseBasicParsing

    Write-Host "Descargando informes individuales de posibles bugs..." -ForegroundColor Cyan
    $BugReportsDir = Join-Path $ReportDir "$SafeName-bug-reports"
    $AnalysisData = Invoke-ApiJson -Uri "$Api/api/analysis-groups/$AnalysisGroupId/analysis"
    $BugReports = @($AnalysisData.bug_reports)
    if ($BugReports.Count -gt 0) {
        New-Item -ItemType Directory -Force -Path $BugReportsDir | Out-Null
        foreach ($BugReport in $BugReports) {
            $BugFile = [string]$BugReport.file
            if ($BugFile -notmatch '^[A-Za-z0-9_-]+[.]html$') { continue }
            $BugUrl = "$Api/api/analysis-groups/$AnalysisGroupId/bug-reports/$BugFile"
            Invoke-WebRequest -Uri $BugUrl -OutFile (Join-Path $BugReportsDir $BugFile) -UseBasicParsing
        }
        Invoke-WebRequest -Uri "$Api/api/analysis-groups/$AnalysisGroupId/bug-reports/index.html" -OutFile (Join-Path $BugReportsDir "index.html") -UseBasicParsing
        Write-Host "Índice de informes individuales: $(Join-Path $BugReportsDir 'index.html')" -ForegroundColor Green
    } else {
        Write-Host "No se han detectado candidatos a bugs; no hay informes individuales." -ForegroundColor Green
    }

    if ($FinalStatus -eq "PARTIAL_ANALYSIS_COMPLETED") {
        Write-Host "Análisis parcial: uno o varios repositorios no pudieron analizarse." -ForegroundColor Yellow
    } else {
        Write-Host "Análisis completado correctamente." -ForegroundColor Green
    }
    Write-Host "Informe principal: $ReportPath" -ForegroundColor Green
    Start-Process -FilePath $ReportPath
    exit 0
}
catch {
    Write-Host ""
    Write-Host ("ERROR: " + $_.Exception.Message) -ForegroundColor Red
    Write-Host "Comprueba .env y, si falla el arranque de la API, revisa logs/api.stderr.log."
    exit 1
}
