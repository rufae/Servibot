# Script para limpiar archivos duplicados y reindexar
# Ejecutar desde: backend/

Write-Host "=== ServiBot: Limpieza y Reindexación ===" -ForegroundColor Cyan

# 1. Limpiar duplicados
Write-Host "`n1. Limpiando archivos duplicados..." -ForegroundColor Yellow
try {
    $cleanupResponse = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/upload/cleanup-duplicates" -ContentType 'application/json; charset=utf-8'
    Write-Host "   ✓ Eliminados: $($cleanupResponse.removed_count) archivos" -ForegroundColor Green
    Write-Host "   ✓ Mantenidos: $($cleanupResponse.kept_count) archivos únicos" -ForegroundColor Green
    
    if ($cleanupResponse.removed_files.Count -gt 0) {
        Write-Host "`n   Archivos eliminados:" -ForegroundColor Gray
        $cleanupResponse.removed_files | ForEach-Object { Write-Host "     - $_" -ForegroundColor DarkGray }
    }
} catch {
    Write-Host "   ✗ Error al limpiar duplicados: $_" -ForegroundColor Red
    exit 1
}

# 2. Listar archivos únicos restantes
Write-Host "`n2. Listando archivos únicos..." -ForegroundColor Yellow
try {
    $listResponse = Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/api/upload/list"
    Write-Host "   ✓ Total de archivos: $($listResponse.count)" -ForegroundColor Green
    
    if ($listResponse.files.Count -gt 0) {
        Write-Host "`n   Archivos disponibles:" -ForegroundColor Gray
        $listResponse.files | ForEach-Object { 
            Write-Host "     - $($_.filename) ($([Math]::Round($_.size_bytes/1024, 2)) KB)" -ForegroundColor DarkGray 
        }
    }
} catch {
    Write-Host "   ✗ Error al listar archivos: $_" -ForegroundColor Red
    exit 1
}

# 3. Reindexar todos los archivos
Write-Host "`n3. Reindexando archivos en la base vectorial..." -ForegroundColor Yellow
$indexed = 0
$failed = 0

foreach ($file in $listResponse.files) {
    $filename = $file.filename
    Write-Host "   Indexando: $filename" -ForegroundColor Gray
    
    try {
        $body = @{ filename = $filename } | ConvertTo-Json
        $indexResponse = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/rag/index" -Body $body -ContentType 'application/json; charset=utf-8'
        
        if ($indexResponse.status -eq "success") {
            $indexed++
            Write-Host "     ✓ Indexado correctamente ($($indexResponse.indexed) chunks)" -ForegroundColor Green
        } else {
            $failed++
            Write-Host "     ✗ Falló: $($indexResponse.message)" -ForegroundColor Red
        }
    } catch {
        $failed++
        Write-Host "     ✗ Error: $_" -ForegroundColor Red
    }
    
    Start-Sleep -Milliseconds 100
}

# 4. Verificar estado de la base vectorial
Write-Host "`n4. Verificando base vectorial..." -ForegroundColor Yellow
try {
    $debugResponse = Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/api/debug/vectors"
    
    Write-Host "   Directorio: $($debugResponse.persist_directory)" -ForegroundColor Gray
    
    foreach ($collection in $debugResponse.collections) {
        Write-Host "   Colección: $($collection.name)" -ForegroundColor Cyan
        Write-Host "     - Documentos: $($collection.count)" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ✗ Error al verificar base vectorial: $_" -ForegroundColor Red
}

# Resumen
Write-Host "`n=== Resumen ===" -ForegroundColor Cyan
Write-Host "✓ Archivos indexados: $indexed" -ForegroundColor Green
if ($failed -gt 0) {
    Write-Host "✗ Archivos fallidos: $failed" -ForegroundColor Red
}
Write-Host "`n¡Proceso completado!" -ForegroundColor Green
