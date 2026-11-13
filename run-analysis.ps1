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

    function Start-LocalApi {
        Write-Host "Iniciando API local en el puerto 8001..." -ForegroundColor Yellow
        $Logs = Join-Path $Root "logs"
        New-Item -ItemType Directory -Force -Path $Logs | Out-Null
        $StdoutLog = Join-Path $Logs "api.stdout.log"
        $StderrLog = Join-Path $Logs "api.stderr.log"
        Remove-Item -LiteralPath $StdoutLog, $StderrLog -Force -ErrorAction SilentlyContinue
        $ApiProcess = Start-Process -FilePath $Python -ArgumentList @("-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8001") -WorkingDirectory $Root -WindowStyle Hidden -RedirectStandardOutput $StdoutLog -RedirectStandardError $StderrLog -PassThru
        $Ready = $false
        for ($i = 0; $i -lt 60; $i++) {
            Start-Sleep -Seconds 2
            if ($ApiProcess.HasExited) {
                $Details = if (Test-Path -LiteralPath $StderrLog) { (Get-Content -LiteralPath $StderrLog -Tail 40) -join [Environment]::NewLine } else { "Sin salida de error." }
                throw "La API terminó durante el arranque (código $($ApiProcess.ExitCode)). Detalle: $Details"
            }
            try { $null = Invoke-RestMethod -Uri "$Api/health" -TimeoutSec 3; $Ready = $true; break } catch { }
            if (($i + 1) % 5 -eq 0) { Write-Host ("Esperando a que responda la API... {0}/120 segundos" -f (($i + 1) * 2)) -ForegroundColor DarkYellow }
        }
        if (-not $Ready) {
            $Details = if (Test-Path -LiteralPath $StderrLog) { (Get-Content -LiteralPath $StderrLog -Tail 40) -join [Environment]::NewLine } else { "Sin salida de error." }
            throw "La API no respondió en 120 segundos. Detalle: $Details"
        }
    }

    $Health = $false
    try { $null = Invoke-RestMethod -Uri "$Api/health" -TimeoutSec 3; $Health = $true } catch { $Health = $false }
    if (-not $Health) {
        Start-LocalApi
    }

    # A health check alone is insufficient: an older uvicorn process may still
    # be serving code without the individual bug-report endpoints.
    $HasDocumentationRoutes = $false
    try {
        $ApiSpec = Invoke-RestMethod -Uri "$Api/openapi.json" -TimeoutSec 5
        $RouteNames = @($ApiSpec.paths.PSObject.Properties.Name)
        $HasDocumentationRoutes = ($RouteNames -contains "/api/analysis-groups/{group_id}/bug-reports/{report_name}") -and ($RouteNames -contains "/api/analysis-groups/{group_id}/repositories/{repository_slug}/report.html") -and ($RouteNames -contains "/api/analysis-groups/{group_id}/documentation/index.html") -and ($RouteNames -contains "/api/analysis-groups/{group_id}/progress")
    } catch { $HasDocumentationRoutes = $false }

    if (-not $HasDocumentationRoutes) {
        $Listener = Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 8001 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($null -eq $Listener) {
            throw "La API responde, pero no publica las rutas de informes individuales. Cierra la API antigua y vuelve a ejecutar este launcher."
        }
        $ApiProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $($Listener.OwningProcess)" -ErrorAction SilentlyContinue
        if ($null -eq $ApiProcess -or $ApiProcess.CommandLine -notmatch "uvicorn.*app\.main:app") {
            throw "El puerto 8001 está ocupado por un proceso que no parece ser esta API. Libera el puerto y vuelve a ejecutar el launcher."
        }
        Write-Host "Se ha detectado una API antigua; reiniciándola para cargar las rutas nuevas..." -ForegroundColor Yellow
        Stop-Process -Id $Listener.OwningProcess -Force
        Start-Sleep -Seconds 2
        Start-LocalApi
        $ApiSpec = Invoke-RestMethod -Uri "$Api/openapi.json" -TimeoutSec 10
        $RouteNames = @($ApiSpec.paths.PSObject.Properties.Name)
        if (-not (($RouteNames -contains "/api/analysis-groups/{group_id}/bug-reports/{report_name}") -and ($RouteNames -contains "/api/analysis-groups/{group_id}/repositories/{repository_slug}/report.html") -and ($RouteNames -contains "/api/analysis-groups/{group_id}/documentation/index.html") -and ($RouteNames -contains "/api/analysis-groups/{group_id}/progress"))) {
            throw "La API reiniciada sigue sin publicar las rutas de informes. Revisa logs/api.stderr.log."
        }
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
    $ReportDirValue = [Environment]::GetEnvironmentVariable("REPORT_DIR", "Process")
    if ([string]::IsNullOrWhiteSpace($ReportDirValue)) { $ReportDirValue = "reports" }
    $ReportDir = Join-Path $Root $ReportDirValue
    New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
    $SafeName = ($AnalysisName -replace '[^A-Za-z0-9._-]+','-').Trim('-')
    if ([string]::IsNullOrWhiteSpace($SafeName)) { $SafeName = "analysis" }
    $BundleDir = Join-Path $ReportDir "$SafeName-$Timestamp-documentacion"
    New-Item -ItemType Directory -Force -Path $BundleDir | Out-Null
    $ReportPath = Join-Path $BundleDir "analysis.html"
    Write-Host "Los informes se guardan uno a uno en: $BundleDir" -ForegroundColor Cyan

    function Get-Bar([int]$Done, [int]$Total) {
        $Width = 30
        $Filled = if ($Total -gt 0) { [int][math]::Floor($Width * $Done / $Total) } else { 0 }
        $Percent = if ($Total -gt 0) { [int][math]::Floor(100 * $Done / $Total) } else { 0 }
        return ("[{0}{1}] {2,3}%  {3}/{4}" -f ("#" * $Filled), ("-" * ($Width - $Filled)), $Percent, $Done, $Total)
    }

    # Descarga los HTML de un microservicio en cuanto termina; no repite los que ya existen.
    function Save-RepositoryReports($Item) {
        $ArtifactDir = ([string]$Item.artifact_dir) -replace '\\', '/'
        if ($ArtifactDir -notmatch '^repositories/[A-Za-z0-9_-]+$') { return }
        $RepositorySlug = ($ArtifactDir -split '/')[-1]
        $ServiceDir = Join-Path $BundleDir $ArtifactDir
        New-Item -ItemType Directory -Force -Path $ServiceDir | Out-Null
        $Target = Join-Path $ServiceDir "analysis.html"
        if (-not (Test-Path -LiteralPath $Target)) {
            Invoke-WebRequest -Uri "$Api/api/analysis-groups/$AnalysisGroupId/repositories/$RepositorySlug/report.html" -OutFile $Target -UseBasicParsing
        }
        $AgentsTarget = Join-Path $ServiceDir "agents.html"
        if (-not (Test-Path -LiteralPath $AgentsTarget)) {
            try { Invoke-WebRequest -Uri "$Api/api/analysis-groups/$AnalysisGroupId/repositories/$RepositorySlug/agents.html" -OutFile $AgentsTarget -UseBasicParsing } catch { }
        }
        $ActivityTarget = Join-Path $ServiceDir "activity.html"
        if (-not (Test-Path -LiteralPath $ActivityTarget)) {
            try { Invoke-WebRequest -Uri "$Api/api/analysis-groups/$AnalysisGroupId/repositories/$RepositorySlug/activity.html" -OutFile $ActivityTarget -UseBasicParsing } catch { }
        }
        $BugPath = [string]$Item.bug_report
        if ($BugPath -match '^bug-reports/([A-Za-z0-9_-]+[.]html)$') {
            $BugDir = Join-Path $BundleDir "bug-reports"
            New-Item -ItemType Directory -Force -Path $BugDir | Out-Null
            $BugTarget = Join-Path $BugDir $Matches[1]
            if (-not (Test-Path -LiteralPath $BugTarget)) {
                try { Invoke-WebRequest -Uri "$Api/api/analysis-groups/$AnalysisGroupId/bug-reports/$($Matches[1])" -OutFile $BugTarget -UseBasicParsing } catch { }
            }
        }
    }

    $FinalStatus = $null
    $Status = $null
    $Shown = 0
    $Total = [int]$Start.repository_count
    $Deadline = (Get-Date).AddHours(6)
    while ((Get-Date) -lt $Deadline) {
        Start-Sleep -Seconds 3
        $Status = Invoke-ApiJson -Uri "$Api/api/analysis-groups/$AnalysisGroupId/progress"
        $FinalStatus = $Status.status
        $Progress = $Status.progress
        if ($null -ne $Progress) {
            $Items = @($Progress.items)
            if ([int]$Progress.total -gt 0) { $Total = [int]$Progress.total }
            while ($Shown -lt $Items.Count) {
                $Item = $Items[$Shown]
                $Shown++
                $Bar = Get-Bar $Shown $Total
                if ($Item.status -eq "failed") {
                    Write-Host ("{0}  ERROR        {1}: {2}" -f $Bar, $Item.name, $Item.error) -ForegroundColor Red
                } else {
                    $Label = if ($Item.status -eq "reused") { "REUTILIZADO " } else { "ANALIZADO   " }
                    $Color = if ($Item.status -eq "reused") { "DarkGray" } else { "Green" }
                    Write-Host ("{0}  {1} {2}" -f $Bar, $Label, $Item.name) -ForegroundColor $Color
                    try { Save-RepositoryReports $Item } catch { Write-Host ("   No se pudo descargar todavia el informe de {0}" -f $Item.name) -ForegroundColor Yellow }
                }
            }
            $Percent = if ($Total -gt 0) { [int][math]::Min(100, [math]::Floor(100 * $Shown / $Total)) } else { 0 }
            $Doing = if ($Progress.phase -eq "repositories" -and $Progress.current) { "Analizando: $($Progress.current)" } elseif ($Progress.phase -eq "global") { "Generando informes globales..." } else { "Finalizando..." }
            Write-Progress -Activity "Analisis del grupo $GroupId" -Status ("{0}/{1} repositorios ({2} reutilizados, {3} con error)" -f $Shown, $Total, [int]$Progress.reused, [int]$Progress.failed) -CurrentOperation $Doing -PercentComplete $Percent
        } else {
            Write-Progress -Activity "Analisis del grupo $GroupId" -Status "Preparando..." -PercentComplete 0
        }
        if ($FinalStatus -in @("ANALYSIS_COMPLETED","PARTIAL_ANALYSIS_COMPLETED","FAILED")) { break }
    }
    Write-Progress -Activity "Analisis del grupo $GroupId" -Completed
    if ($FinalStatus -notin @("ANALYSIS_COMPLETED","PARTIAL_ANALYSIS_COMPLETED","FAILED")) { throw "El análisis superó el tiempo máximo de seis horas. ID: $AnalysisGroupId" }
    if ($FinalStatus -eq "FAILED") {
        $Reason = $Status.last_error
        if (-not $Reason) { $Reason = "El servidor marcó el análisis como FAILED." }
        throw $Reason
    }

    Write-Host "Descargando documentación HTML completa..." -ForegroundColor Cyan
    $AnalysisData = Invoke-ApiJson -Uri "$Api/api/analysis-groups/$AnalysisGroupId/analysis"
    Invoke-WebRequest -Uri "$Api/api/analysis-groups/$AnalysisGroupId/report.html" -OutFile $ReportPath -UseBasicParsing

    # Preserve the server workspace's relative layout so links work offline.
    foreach ($Repository in @($AnalysisData.repositories)) {
        Save-RepositoryReports $Repository
    }

    $BugReportsDir = Join-Path $BundleDir "bug-reports"
    New-Item -ItemType Directory -Force -Path $BugReportsDir | Out-Null
    foreach ($BugReport in @($AnalysisData.bug_reports)) {
        $BugFile = [string]$BugReport.file
        if ($BugFile -notmatch '^[A-Za-z0-9_-]+[.]html$') { continue }
        if (Test-Path -LiteralPath (Join-Path $BugReportsDir $BugFile)) { continue }
        Invoke-WebRequest -Uri "$Api/api/analysis-groups/$AnalysisGroupId/bug-reports/$BugFile" -OutFile (Join-Path $BugReportsDir $BugFile) -UseBasicParsing
    }
    Invoke-WebRequest -Uri "$Api/api/analysis-groups/$AnalysisGroupId/bug-reports/index.html" -OutFile (Join-Path $BugReportsDir "index.html") -UseBasicParsing
    try { Invoke-WebRequest -Uri "$Api/api/analysis-groups/$AnalysisGroupId/activity.html" -OutFile (Join-Path $BundleDir "activity.html") -UseBasicParsing } catch { Write-Host "Histórico de actividad no disponible" -ForegroundColor Yellow }
    try { Invoke-WebRequest -Uri "$Api/api/analysis-groups/$AnalysisGroupId/agents.html" -OutFile (Join-Path $BundleDir "agents.html") -UseBasicParsing } catch { Write-Host "Informe multiagente global no disponible" -ForegroundColor Yellow }
    Invoke-WebRequest -Uri "$Api/api/analysis-groups/$AnalysisGroupId/documentation/index.html" -OutFile (Join-Path $BundleDir "index.html") -UseBasicParsing

    if ($FinalStatus -eq "PARTIAL_ANALYSIS_COMPLETED") {
        Write-Host "Análisis parcial: uno o varios repositorios no pudieron analizarse." -ForegroundColor Yellow
    } else {
        Write-Host "Análisis completado correctamente." -ForegroundColor Green
    }
    Write-Host "Documentación completa: $BundleDir" -ForegroundColor Green
    Write-Host "Índice de documentación: $(Join-Path $BundleDir 'index.html')" -ForegroundColor Green
    # Índice raíz que enlaza todos los análisis descargados y sus documentos.
    $RootIndex = Join-Path $ReportDir "index.html"
    try {
        Push-Location $Root
        & $Python -m app.reports_index $ReportDir | Out-Null
        Pop-Location
        if (Test-Path -LiteralPath $RootIndex) { Write-Host "Índice general de todos los análisis: $RootIndex" -ForegroundColor Green }
    } catch { Pop-Location; Write-Host "No se pudo generar el índice general." -ForegroundColor Yellow }
    Start-Process -FilePath (Join-Path $BundleDir "index.html")
    exit 0
}
catch {
    Write-Host ""
    Write-Host ("ERROR: " + $_.Exception.Message) -ForegroundColor Red
    Write-Host "Comprueba .env y, si falla el arranque de la API, revisa logs/api.stderr.log."
    exit 1
}
