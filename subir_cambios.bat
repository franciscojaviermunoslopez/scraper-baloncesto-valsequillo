@echo off
chcp 65001 >nul
echo.
echo ========================================
echo 🚀 SUBIR CAMBIOS A GITHUB
echo ========================================
echo.

cd /d "c:\Users\fmunoz\Downloads\PRUEBA PDF"

echo [1/3] Añadiendo archivos...
git add .

echo [2/3] Creando commit...
git commit -m "🔧 Arreglar error SSL en GitHub Actions"

echo [3/3] Subiendo a GitHub...
git push

echo.
echo ========================================
echo ✅ ¡CAMBIOS SUBIDOS!
echo ========================================
echo.
echo Ahora puedes probar el workflow en GitHub Actions
echo.
pause
