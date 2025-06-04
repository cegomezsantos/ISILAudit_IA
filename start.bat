@echo off
echo 🚀 Iniciando Analizador de Presentaciones...
echo.
echo 📌 Activando entorno virtual...
call .venv\Scripts\activate.bat

if errorlevel 1 (
    echo ❌ Error: No se pudo activar el entorno virtual
    echo 💡 Asegúrate de que el entorno virtual esté creado ejecutando: python -m venv .venv
    pause
    exit /b 1
)

echo ✅ Entorno virtual activado
echo.
echo 🌐 Iniciando aplicación web...
echo 📍 La aplicación se abrirá en: http://localhost:8501
echo.
echo 💡 Para detener la aplicación presiona Ctrl+C
echo.

streamlit run app.py

pause 