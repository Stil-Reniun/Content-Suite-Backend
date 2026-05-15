# Deploy rápido - solo construye y actualiza Cloud Run
# Usar después de haber hecho el deploy inicial

$ErrorActionPreference = "Stop"

$PROJECT_ID = "gen-lang-client-0632595528"
$REGION = "us-central1"
$SERVICE_NAME = "backend-fastapi"
$IMAGE_NAME = "gcr.io/$PROJECT_ID/$SERVICE_NAME"
$ENV_FILE = ".env"

Write-Host "=== Deploy rápido a Cloud Run ===" -ForegroundColor Cyan

# Leer .env y generar YAML
$envVars = @{}
Get-Content $ENV_FILE | ForEach-Object {
    $line = $_.Trim()
    if ($line -and -not $line.StartsWith("#") -and $line -match "^(.+?)=(.+)$") {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim().Trim('"').Trim("'")
        $envVars[$key] = $value
    }
}

$yamlContent = @()
foreach ($key in $envVars.Keys) {
    $yamlContent += "$($key): '$($envVars[$key])'"
}
$yamlPath = Join-Path $PSScriptRoot "env-vars-deploy.yaml"
$yamlContent | Set-Content $yamlPath -Encoding UTF8

# Construir y subir imagen
Write-Host "`n[1/2] Construyendo imagen..." -ForegroundColor Yellow
gcloud builds submit --tag $IMAGE_NAME --quiet

# Actualizar Cloud Run
Write-Host "`n[2/2] Actualizando Cloud Run..." -ForegroundColor Yellow
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
gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)"
