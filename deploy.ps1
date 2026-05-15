# Deploy script for Google Cloud Run
# Lee variables del .env y despliega/actualiza Cloud Run

$ErrorActionPreference = "Stop"

# Configuración
$PROJECT_ID = "gen-lang-client-0632595528"
$REGION = "us-central1"
$SERVICE_NAME = "backend-fastapi"
$IMAGE_NAME = "gcr.io/$PROJECT_ID/$SERVICE_NAME"
$ENV_FILE = ".env"

Write-Host "=== Deploy a Cloud Run ===" -ForegroundColor Cyan

# Verificar gcloud
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: gcloud no esta instalado. Descargalo de: https://cloud.google.com/sdk/docs/install" -ForegroundColor Red
    exit 1
}

# Verificar archivo .env
if (-not (Test-Path $ENV_FILE)) {
    Write-Host "ERROR: No se encontro el archivo $ENV_FILE" -ForegroundColor Red
    exit 1
}

# Leer y parsear variables de entorno del .env
Write-Host "`n[1/5] Leyendo variables de entorno..." -ForegroundColor Yellow
$envVars = @{}
Get-Content $ENV_FILE | ForEach-Object {
    $line = $_.Trim()
    if ($line -and -not $line.StartsWith("#") -and $line -match "^(.+?)=(.+)$") {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim().Trim('"').Trim("'")
        $envVars[$key] = $value
    }
}

Write-Host "  Variables encontradas: $($envVars.Count)" -ForegroundColor Green

# Generar archivo YAML para env-vars-file
$yamlContent = @()
foreach ($key in $envVars.Keys) {
    $value = $envVars[$key]
    $yamlContent += "$($key): '$value'"
}
$yamlPath = Join-Path $PSScriptRoot "env-vars-deploy.yaml"
$yamlContent | Set-Content $yamlPath -Encoding UTF8
Write-Host "  Archivo YAML generado: $yamlPath" -ForegroundColor Green

# Configurar proyecto
Write-Host "`n[2/5] Configurando proyecto $PROJECT_ID..." -ForegroundColor Yellow
gcloud config set project $PROJECT_ID

# Habilitar APIs
Write-Host "`n[3/5] Habilitando APIs necesarias..." -ForegroundColor Yellow
gcloud services enable run.googleapis.com containerregistry.googleapis.com cloudbuild.googleapis.com --quiet

# Construir y subir imagen
Write-Host "`n[4/5] Construyendo y subiendo imagen a Container Registry..." -ForegroundColor Yellow
gcloud builds submit --tag $IMAGE_NAME --quiet

# Desplegar a Cloud Run
Write-Host "`n[5/5] Desplegando a Cloud Run ($REGION)..." -ForegroundColor Yellow
gcloud run deploy $SERVICE_NAME `
    --image $IMAGE_NAME `
    --region $REGION `
    --platform managed `
    --allow-unauthenticated `
    --env-vars-file $yamlPath `
    --memory 1Gi `
    --timeout 300 `
    --quiet

Write-Host "`n=== Deploy completado ===" -ForegroundColor Green
Write-Host "URL del servicio:" -ForegroundColor Cyan
gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)"
