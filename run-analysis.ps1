[CmdletBinding()]
param(
    # Identificador del grupo GitLab. Si se indica, tiene prioridad sobre GITLAB_GROUP_ID de .env.
    [Parameter(Position = 0)][string]$GroupIdArgument = "",
    # Activa los agentes LLM con este proveedor: openai, claude, gemini u ollama (prioridad sobre .env).
    [Alias("Llm")][string]$LlmProvider = "",
    # Modelo a usar con ese proveedor (prioridad sobre LLM_MODEL de .env).
    [Alias("Model")][string]$LlmModel = "",
    # Muestra la configuración LLM y los modelos que ofrece el proveedor, y termina sin analizar.
    [switch]$ListModels
)

$ErrorActionPreference = "Stop"
# Silencia la barra propia de Invoke-WebRequest (ralentiza las descargas); la barra del análisis se activa aparte.
$ProgressPreference = "SilentlyContinue"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $Root

function Read-DotEnv([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) {
        # Primera ejecución: se crea .env desde la plantilla y se abre para rellenarlo.
        $Example = Join-Path (Split-Path -Parent $Path) ".env.example"
        if (-not (Test-Path -LiteralPath $Example)) { throw "No existe .env ni .env.example." }
        Copy-Item -LiteralPath $Example -Destination $Path
        Write-Host "Se ha creado .env. Rellena GITLAB_TOKEN (y GITLAB_BASE_URL si no usas gitlab.com), guarda y cierra el Bloc de notas." -ForegroundColor Yellow
        try { Start-Process -FilePath "notepad.exe" -ArgumentList "`"$Path`"" -Wait } catch { throw "Se ha creado .env. Edítalo, configura GITLAB_TOKEN y vuelve a ejecutar el lanzador." }
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

    # Selección de proveedor y modelo LLM desde la línea de órdenes.
    if (-not [string]::IsNullOrWhiteSpace($LlmProvider)) {
        $LlmProvider = $LlmProvider.Trim().ToLower()
        if ($LlmProvider -notin @("openai","claude","anthropic","gemini","google","ollama")) { throw "Proveedor LLM no válido: $LlmProvider. Opciones: openai, claude, gemini, ollama." }
        [Environment]::SetEnvironmentVariable("LLM_PROVIDER", $LlmProvider, "Process")
        [Environment]::SetEnvironmentVariable("LLM_AGENTS_ENABLED", "true", "Process")
    }
    if (-not [string]::IsNullOrWhiteSpace($LlmModel)) {
        [Environment]::SetEnvironmentVariable("LLM_MODEL", $LlmModel.Trim(), "Process")
        [Environment]::SetEnvironmentVariable("LLM_AGENTS_ENABLED", "true", "Process")
    }

    $Token = [Environment]::GetEnvironmentVariable("GITLAB_TOKEN", "Process")
    $GroupId = [Environment]::GetEnvironmentVariable("GITLAB_GROUP_ID", "Process")
    $BaseUrl = [Environment]::GetEnvironmentVariable("GITLAB_BASE_URL", "Process")
    # Para listar modelos no hacen falta ni el token de GitLab ni el grupo.
    if (-not $ListModels) {
        if ([string]::IsNullOrWhiteSpace($Token) -or $Token -match '^<.*>$') { throw "GITLAB_TOKEN no está configurado en .env." }
        if (-not [string]::IsNullOrWhiteSpace($GroupIdArgument)) { $GroupId = $GroupIdArgument.Trim() }
        if ([string]::IsNullOrWhiteSpace($GroupId) -or $GroupId -match '^<.*>$') {
            $GroupId = ""
        }
    }
    if ([string]::IsNullOrWhiteSpace($BaseUrl)) { $BaseUrl = "https://gitlab.com" }

    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "Git no está instalado o no está disponible en PATH." }

    $Python = Join-Path $Root ".venv\Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $Python)) {
        Write-Host "Preparando entorno Python e instalando dependencias..." -ForegroundColor Yellow
        & (Join-Path $Root "setup-windows.ps1")
        if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) { throw "Falló la preparación del entorno Python." }
    }
    if (-not (Test-Path -LiteralPath $Python)) { throw "No se ha podido crear el entorno .venv." }

    # Si requirements.txt ha cambiado desde la última instalación, se actualizan las dependencias.
    $Requirements = Join-Path $Root "requirements.txt"
    $Stamp = Join-Path $Root ".venv\requirements.sha256"
    $Wanted = (Get-FileHash -LiteralPath $Requirements -Algorithm SHA256).Hash
    $Installed = if (Test-Path -LiteralPath $Stamp) { (Get-Content -LiteralPath $Stamp -Raw).Trim() } else { "" }
    if ($Wanted -ne $Installed) {
        Write-Host "Actualizando dependencias de Python..." -ForegroundColor Yellow
        & $Python -m pip install --quiet --disable-pip-version-check -r $Requirements
        if ($LASTEXITCODE -ne 0) { throw "No se pudieron instalar las dependencias de requirements.txt." }
        Set-Content -LiteralPath $Stamp -Value $Wanted -Encoding ASCII
    }

    if ($ListModels) {
        & $Python -m app.llm --models
        exit $LASTEXITCODE
    }

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

    # Una API arrancada antes de la última actualización del código sigue ejecutando la versión antigua.
    $ApiIsStale = $false
    try {
        $HealthInfo = Invoke-RestMethod -Uri "$Api/health" -TimeoutSec 5
        $NewestCode = (Get-ChildItem -LiteralPath (Join-Path $Root "app") -Recurse -File | Where-Object { $_.Extension -eq ".py" } | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1).LastWriteTimeUtc
        $NewestEpoch = [DateTimeOffset]::new([DateTime]::SpecifyKind($NewestCode, [DateTimeKind]::Utc)).ToUnixTimeSeconds()
        # Se compara en segundos Unix para no depender de cómo cada versión de PowerShell interpreta las fechas JSON.
        $StartedEpoch = [long]$HealthInfo.started_epoch
        $ApiIsStale = ($StartedEpoch -le 0) -or ($NewestEpoch -gt $StartedEpoch)
        # También está obsoleta si .env cambió después de arrancarla, o si usa otro proveedor o modelo LLM.
        $EnvFile = Get-Item -LiteralPath (Join-Path $Root ".env")
        $EnvEpoch = [DateTimeOffset]::new([DateTime]::SpecifyKind($EnvFile.LastWriteTimeUtc, [DateTimeKind]::Utc)).ToUnixTimeSeconds()
        if ($EnvEpoch -gt $StartedEpoch) { $ApiIsStale = $true }
        $WantedEnabled = ([string][Environment]::GetEnvironmentVariable("LLM_AGENTS_ENABLED", "Process")).Trim().ToLower() -in @("1","true","yes","si","on")
        $WantedProvider = ([string][Environment]::GetEnvironmentVariable("LLM_PROVIDER", "Process")).Trim().ToLower()
        if ($WantedProvider -eq "anthropic") { $WantedProvider = "claude" }
        if ($WantedProvider -eq "google") { $WantedProvider = "gemini" }
        if ([string]::IsNullOrWhiteSpace($WantedProvider)) { $WantedProvider = "openai" }
        $WantedModel = ([string][Environment]::GetEnvironmentVariable("LLM_MODEL", "Process")).Trim()
        if ($null -eq $HealthInfo.llm) { $ApiIsStale = $true }
        elseif ([bool]$HealthInfo.llm.enabled -ne $WantedEnabled) { $ApiIsStale = $true }
        elseif ($WantedEnabled -and (([string]$HealthInfo.llm.provider -ne $WantedProvider) -or ([string]$HealthInfo.llm.model -ne $WantedModel))) { $ApiIsStale = $true }
    } catch { $ApiIsStale = $false }

    if ((-not $HasDocumentationRoutes) -or $ApiIsStale) {
        $Listener = Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 8001 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($null -eq $Listener) {
            throw "Hay una API antigua en el puerto 8001 que no se puede reiniciar automáticamente. Ciérrala y vuelve a ejecutar este launcher."
        }
        $ApiProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $($Listener.OwningProcess)" -ErrorAction SilentlyContinue
        if ($null -eq $ApiProcess -or $ApiProcess.CommandLine -notmatch "uvicorn.*app\.main:app") {
            throw "El puerto 8001 está ocupado por un proceso que no parece ser esta API. Libera el puerto y vuelve a ejecutar el launcher."
        }
        Write-Host "Se ha detectado una API con código anterior; reiniciándola para cargar la versión actual..." -ForegroundColor Yellow
        Stop-Process -Id $Listener.OwningProcess -Force
        Start-Sleep -Seconds 2
        Start-LocalApi
        $ApiSpec = Invoke-RestMethod -Uri "$Api/openapi.json" -TimeoutSec 10
        $RouteNames = @($ApiSpec.paths.PSObject.Properties.Name)
        if (-not (($RouteNames -contains "/api/analysis-groups/{group_id}/bug-reports/{report_name}") -and ($RouteNames -contains "/api/analysis-groups/{group_id}/repositories/{repository_slug}/report.html") -and ($RouteNames -contains "/api/analysis-groups/{group_id}/documentation/index.html") -and ($RouteNames -contains "/api/analysis-groups/{group_id}/progress"))) {
            throw "La API reiniciada sigue sin publicar las rutas de informes. Revisa logs/api.stderr.log."
        }
    }

    # Selección interactiva de grupo y repositorios. Un repositorio es la unidad de análisis
    # del supervisor en esta versión; los monorepos se analizan como una única unidad.
    function Select-NumberedItems($Items, [string]$Prompt, [string]$DisplayProperty) {
        $Items = @($Items)
        if ($Items.Count -eq 0) { throw "No hay elementos disponibles para seleccionar." }
        Write-Host ""
        Write-Host $Prompt -ForegroundColor Cyan
        for ($i = 0; $i -lt $Items.Count; $i++) {
            $displayValue = $Items[$i].PSObject.Properties[$DisplayProperty].Value
            Write-Host ("  {0}. {1}" -f ($i + 1), [string]$displayValue)
        }
        $raw = (Read-Host "Números separados por comas, o A para todos").Trim()
        if ([string]::IsNullOrWhiteSpace($raw) -or $raw.ToLower() -in @("a", "todos")) { return ,$Items }
        $selected = @()
        foreach ($part in ($raw -split '[,; ]+' | Where-Object { $_ })) {
            $number = 0
            if (-not [int]::TryParse($part, [ref]$number) -or $number -lt 1 -or $number -gt $Items.Count) {
                throw "Selección no válida: $part. Usa números entre 1 y $($Items.Count), o A."
            }
            $selected += $Items[$number - 1]
        }
        if ($selected.Count -eq 0) { throw "No se ha seleccionado ningún elemento." }
        return ,$selected
    }

    if ([string]::IsNullOrWhiteSpace($GroupId)) {
        $Groups = @(Invoke-ApiJson -Uri "$Api/api/gitlab/groups")
        if ($Groups.Count -eq 0) { throw "El token no tiene grupos GitLab visibles." }
        Write-Host ""
        Write-Host "Grupos GitLab disponibles:" -ForegroundColor Cyan
        for ($i = 0; $i -lt $Groups.Count; $i++) {
            Write-Host ("  {0}. {1}" -f ($i + 1), $Groups[$i].full_path)
        }
        $GroupChoice = (Read-Host "Número del grupo que quieres analizar").Trim()
        $GroupIndex = 0
        if (-not [int]::TryParse($GroupChoice, [ref]$GroupIndex) -or $GroupIndex -lt 1 -or $GroupIndex -gt $Groups.Count) { throw "Número de grupo no válido." }
        $GroupId = [string]$Groups[$GroupIndex - 1].id
    }
    $EncodedGroup = [uri]::EscapeDataString($GroupId)
    $Projects = @(Invoke-ApiJson -Uri "$Api/api/gitlab/groups/$EncodedGroup/projects")
    if ($Projects.Count -eq 0) { throw "El grupo seleccionado no contiene repositorios clonables." }
    $ChosenProjects = Select-NumberedItems $Projects "Repositorios / microservicios del grupo (cada repositorio es una unidad de análisis):" "name"
    $SelectedProjectIds = @($ChosenProjects | ForEach-Object { [int]$_.gitlab_project_id })
    if ($SelectedProjectIds.Count -eq 0) { throw "No se ha seleccionado ningún repositorio." }

    $AnalysisName = [Environment]::GetEnvironmentVariable("ANALYSIS_NAME", "Process")
    if ([string]::IsNullOrWhiteSpace($AnalysisName)) { $AnalysisName = "gitlab-group-$GroupId-$Timestamp" }
    if ($AnalysisName.Length -gt 120) { $AnalysisName = $AnalysisName.Substring(0,120) }

    Write-Host "Grupo GitLab: $GroupId" -ForegroundColor Cyan
    try {
        $Llm = (Invoke-RestMethod -Uri "$Api/health" -TimeoutSec 5).llm
        if ($Llm.active) { Write-Host ("Agentes LLM: {0} · {1}" -f $Llm.provider_label, $Llm.model) -ForegroundColor Cyan }
        elseif ($Llm.enabled) { Write-Host ("Agentes LLM activados pero sin configurar: {0}" -f $Llm.problem) -ForegroundColor Yellow }
        else { Write-Host "Agentes LLM: desactivados (solo análisis estático)" }
    } catch { }
    Write-Host "Nombre del análisis: $AnalysisName"
    $EncodedGroup = [uri]::EscapeDataString($GroupId)
    $Start = Invoke-ApiJson -Uri "$Api/api/gitlab/groups/$EncodedGroup/analysis" -Method "POST" -Body @{ name = $AnalysisName; project_ids = $SelectedProjectIds }
    $AnalysisGroupId = $Start.analysis_group_id
    if ([string]::IsNullOrWhiteSpace([string]$AnalysisGroupId)) { throw "La API no devolvió analysis_group_id." }

    Write-Host "Trabajo: $AnalysisGroupId"
    Write-Host "Microservicios / repositorios seleccionados: $($Start.repository_count)"
    $ReportDirValue = [Environment]::GetEnvironmentVariable("REPORT_DIR", "Process")
    if ([string]::IsNullOrWhiteSpace($ReportDirValue)) { $ReportDirValue = "reports" }
    $ReportDir = Join-Path $Root $ReportDirValue
    New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
    $SafeName = ($AnalysisName -replace '[^A-Za-z0-9._-]+','-').Trim('-')
    if ([string]::IsNullOrWhiteSpace($SafeName)) { $SafeName = "analysis" }
    # El nombre automático ya incluye la fecha y hora; no se repite en la carpeta.
    $BundleName = if ($SafeName.EndsWith($Timestamp)) { "$SafeName-documentacion" } else { "$SafeName-$Timestamp-documentacion" }
    $BundleDir = Join-Path $ReportDir $BundleName
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
            $ProgressPreference = "Continue"
            $Doing = if ($Progress.phase -eq "repositories" -and $Progress.current) { "Analizando: $($Progress.current)" } elseif ($Progress.phase -eq "global") { "Generando informes globales..." } else { "Finalizando..." }
            Write-Progress -Activity "Analisis del grupo $GroupId" -Status ("{0}/{1} repositorios ({2} reutilizados, {3} con error)" -f $Shown, $Total, [int]$Progress.reused, [int]$Progress.failed) -CurrentOperation $Doing -PercentComplete $Percent
        } else {
            $ProgressPreference = "Continue"
            Write-Progress -Activity "Analisis del grupo $GroupId" -Status "Preparando..." -PercentComplete 0
        }
        $ProgressPreference = "SilentlyContinue"
        if ($FinalStatus -in @("ANALYSIS_COMPLETED","PARTIAL_ANALYSIS_COMPLETED","FAILED")) { break }
    }
    $ProgressPreference = "Continue"
    Write-Progress -Activity "Analisis del grupo $GroupId" -Completed
    $ProgressPreference = "SilentlyContinue"
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
    try { Start-Process -FilePath (Join-Path $BundleDir "index.html") } catch { Write-Host "Abre el índice manualmente en el navegador." -ForegroundColor Yellow }
    exit 0
}
catch {
    Write-Host ""
    Write-Host ("ERROR: " + $_.Exception.Message) -ForegroundColor Red
    Write-Host "Comprueba .env y, si falla el arranque de la API, revisa logs/api.stderr.log."
    exit 1
}