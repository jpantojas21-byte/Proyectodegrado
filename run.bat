@echo off
chcp 65001 >nul
title Dashboard Financiero - Supersociedades

echo.
echo  ============================================================
echo    Dashboard Financiero - Superintendencia de Sociedades
echo    Analisis Comparativo Estado de Resultado Integral
echo  ============================================================
echo.

:: Verificar que Python este instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no esta instalado o no esta en el PATH.
    echo  Descargalo desde: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] Verificando e instalando dependencias...
pip install -r "%~dp0requirements.txt" --quiet --disable-pip-version-check
if errorlevel 1 (
    echo [ERROR] Fallo la instalacion de dependencias.
    pause
    exit /b 1
)

echo [2/3] Dependencias listas.
echo [3/3] Iniciando la aplicacion en http://localhost:8501
echo.
echo  Presiona Ctrl+C para detener el servidor.
echo.

:: Ejecutar Streamlit desde la carpeta del script
cd /d "%~dp0"
python -m streamlit run dashboard_app.py --server.port 8501 --server.headless false

pause
