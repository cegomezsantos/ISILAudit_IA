# Script de inicio para Analizador de Presentaciones
Write-Host "🚀 Iniciando Analizador de Presentaciones..." -ForegroundColor Green
Write-Host ""

Write-Host "📌 Activando entorno virtual..." -ForegroundColor Yellow

try {
    # Activar entorno virtual
    & ".\.venv\Scripts\Activate.ps1"
    Write-Host "✅ Entorno virtual activado" -ForegroundColor Green
}
catch {
    Write-Host "❌ Error: No se pudo activar el entorno virtual" -ForegroundColor Red
    Write-Host "💡 Asegúrate de que el entorno virtual esté creado ejecutando: python -m venv .venv" -ForegroundColor Yellow
    Read-Host "Presiona Enter para salir"
    exit 1
}

Write-Host ""
Write-Host "🌐 Iniciando aplicación web..." -ForegroundColor Green
Write-Host "📍 La aplicación se abrirá en: http://localhost:8501" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 Para detener la aplicación presiona Ctrl+C" -ForegroundColor Yellow
Write-Host ""

# Ejecutar Streamlit
try {
    streamlit run app.py
}
catch {
    Write-Host "❌ Error al ejecutar la aplicación" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Read-Host "Presiona Enter para salir" 