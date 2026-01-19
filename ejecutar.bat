@echo off
chcp 65001 >nul
echo ====================================
echo 🏀 Scraper de Partidos Valsequillo
echo ====================================
echo.

:menu
echo Selecciona una opción:
echo.
echo 1. Ejecutar prueba (PDF de ejemplo)
echo 2. Ejecutar scraper REAL (descarga de web)
echo 3. Ver último Excel generado
echo 4. Instalar/Actualizar dependencias
echo 5. Salir
echo.
set /p opcion="Opción (1-5): "

if "%opcion%"=="1" goto prueba
if "%opcion%"=="2" goto real
if "%opcion%"=="3" goto ver_excel
if "%opcion%"=="4" goto instalar
if "%opcion%"=="5" goto salir
echo Opción inválida
goto menu

:prueba
echo.
echo 📄 Ejecutando prueba con PDF de ejemplo...
echo.
python test_scraper.py
echo.
pause
goto menu

:real
echo.
echo 🌐 Ejecutando scraper REAL (esto descargará de Internet)...
echo.
python scraper_baloncesto.py
echo.
pause
goto menu

:ver_excel
echo.
echo 📊 Abriendo último Excel generado...
for /f "delims=" %%i in ('dir /b /od partidos*.xlsx 2^>nul') do set ultimo=%%i
if defined ultimo (
    start "" "%ultimo%"
    echo Abierto: %ultimo%
) else (
    echo No se encontraron archivos Excel
)
echo.
pause
goto menu

:instalar
echo.
echo 📦 Instalando/Actualizando dependencias...
echo.
pip install -r requirements.txt --upgrade
echo.
pause
goto menu

:salir
echo.
echo ¡Hasta luego! 👋
exit
