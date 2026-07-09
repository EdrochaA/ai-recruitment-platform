# Script para sincronizar frontend con S3 y invalidar CloudFront
# Uso: .\update-frontend.ps1

param(
    [string]$BucketName = "ai-recruitment-bucket",
    [string]$DistributionId = "E1JBWCGV5H0BXY",  # Reemplaza con tu Distribution ID
    [switch]$Delete,  # Usar --delete para eliminar archivos de S3 no locales
    [switch]$Help
)

if ($Help) {
    Write-Host @"
╔════════════════════════════════════════════════════════════════╗
║        AWS S3 Frontend Sync Script                             ║
╚════════════════════════════════════════════════════════════════╝

Uso:
    .\update-frontend.ps1 [opciones]

Opciones:
    -BucketName <string>      Nombre del bucket S3 
                             (default: ai-recruitment-bucket)
    -DistributionId <string> CloudFront Distribution ID
                             (default: E1JBWCGV5H0BXY)
    -Delete                   Eliminar archivos de S3 que no existen localmente
    -Help                     Mostrar esta ayuda

Ejemplos:
    # Sync básico (recomendado)
    .\update-frontend.ps1

    # Con parámetros personalizados
    .\update-frontend.ps1 -BucketName "mi-bucket" -DistributionId "ABC123XYZ"

    # Eliminar archivos de S3 que fueron borrados localmente
    .\update-frontend.ps1 -Delete

Nota:
    - Asegúrate de tener AWS CLI instalado y configurado (aws configure)
    - Este script debe ejecutarse desde la carpeta raíz del proyecto
    - Los cambios serán visibles en 1-2 minutos después de ejecutar

"@
    exit
}

Write-Host @"
╔════════════════════════════════════════════════════════════════╗
║        🚀 AWS S3 Frontend Sync                                 ║
╚════════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

# Verificar que AWS CLI está instalado
Write-Host "✔️ Verificando AWS CLI..." -ForegroundColor Gray
try {
    $awsVersion = aws --version
    Write-Host "   AWS CLI: $awsVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ AWS CLI no encontrado. Instálalo con: npm install -g aws-cli" -ForegroundColor Red
    exit 1
}

# Verificar configuración AWS
Write-Host "✔️ Verificando configuración AWS..." -ForegroundColor Gray
try {
    aws sts get-caller-identity | Out-Null
    Write-Host "   ✅ AWS está configurado correctamente" -ForegroundColor Green
} catch {
    Write-Host "❌ AWS no está configurado. Ejecuta: aws configure" -ForegroundColor Red
    exit 1
}

# Construir comando sync
$syncArgs = @(
    "./frontend",
    "s3://$BucketName",
    "--exclude", ".git/*",
    "--exclude", "node_modules/*",
    "--exclude", "*.md",
    "--exclude", ".gitignore",
    "--exclude", "update-frontend.ps1",
    "--region", "us-east-1"
)

if ($Delete) {
    $syncArgs += "--delete"
    Write-Host "⚠️ Modo DELETE habilitado: Se borrarán archivos de S3 que no existen localmente" -ForegroundColor Yellow
}

# Sincronizar archivos
Write-Host ""
Write-Host "📤 Sincronizando archivos con S3 ($BucketName)..." -ForegroundColor Cyan
Write-Host "   Comando: aws s3 sync" -ForegroundColor Gray

try {
    aws s3 sync @syncArgs
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Error sincronizando con S3" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "✅ Archivos sincronizados correctamente" -ForegroundColor Green
} catch {
    Write-Host "❌ Error durante sync: $_" -ForegroundColor Red
    exit 1
}

# Invalidar CloudFront
Write-Host ""
Write-Host "🔄 Invalidando CloudFront cache ($DistributionId)..." -ForegroundColor Cyan

try {
    $invalidation = aws cloudfront create-invalidation `
        --distribution-id $DistributionId `
        --paths "/*" `
        --region us-east-1 | ConvertFrom-Json
    
    $invalidationId = $invalidation.Invalidation.Id
    $status = $invalidation.Invalidation.Status
    
    Write-Host ""
    Write-Host "✅ CloudFront invalidation creada" -ForegroundColor Green
    Write-Host "   ID: $invalidationId" -ForegroundColor Gray
    Write-Host "   Status: $status" -ForegroundColor Gray
} catch {
    Write-Host "❌ Error invalidando CloudFront: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host @"
╔════════════════════════════════════════════════════════════════╗
║        ✨ Actualización completada                             ║
╚════════════════════════════════════════════════════════════════╝

📊 Resumen:
  • Archivos: Sincronizados con S3
  • CloudFront: Invalidation $status
  • Invalidation ID: $invalidationId

⏳ Próximos pasos:
  1. Los cambios se propagarán en 1-2 minutos
  2. Recarga tu navegador (Ctrl+F5 para hard refresh)
  3. Verifica que la URL sea: https://d[hash].cloudfront.net

💡 Consejo:
  • Puedes ver el progreso de invalidation en AWS CloudFront Console
  • Busca el ID de invalidation: $invalidationId
  • Una vez que el estado sea "Completed", los cambios están listos

🚀 ¡Listo! Tu frontend ha sido actualizado.

"@ -ForegroundColor Cyan
