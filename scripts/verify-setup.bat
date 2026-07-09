@echo off
REM verify-setup.bat
REM Script para verificar que el proyecto está correctamente configurado (Windows)

echo ==================================
echo AI Recruitment Platform - Verificacion
echo ==================================
echo.

REM Verificar estructura frontend
echo Verificando estructura del frontend...
if exist "frontend\index.html" (
    if exist "frontend\styles.css" (
        if exist "frontend\js\app.js" (
            echo   [OK] Archivos principales del frontend presentes
        ) else (
            echo   [ERROR] Falta frontend\js\app.js
            exit /b 1
        )
    ) else (
        echo   [ERROR] Falta frontend\styles.css
        exit /b 1
    )
) else (
    echo   [ERROR] Falta frontend\index.html
    exit /b 1
)

REM Verificar archivos JS
echo.
echo Verificando modulos JavaScript...

set "files[0]=frontend\js\config.js"
set "files[1]=frontend\js\mock-auth.js"
set "files[2]=frontend\js\api-client.js"
set "files[3]=frontend\js\router.js"
set "files[4]=frontend\js\utils.js"
set "files[5]=frontend\js\pages\home.js"
set "files[6]=frontend\js\pages\job-detail.js"
set "files[7]=frontend\js\pages\apply.js"
set "files[8]=frontend\js\pages\hr-dashboard.js"
set "files[9]=frontend\js\pages\admin-dashboard.js"

for /L %%i in (0,1,9) do (
    if exist "!files[%%i]!" (
        echo   [OK] !files[%%i]!
    ) else (
        echo   [ERROR] Falta !files[%%i]!
        exit /b 1
    )
)

REM Verificar estructura backend
echo.
echo Verificando estructura del backend...
if exist "backend\app\main.py" (
    echo   [OK] Backend main.py presente
) else (
    echo   [ERROR] Falta backend\app\main.py
    exit /b 1
)

REM Verificar documentación
echo.
echo Verificando documentacion...
if exist "QUICKSTART.md" (
    echo   [OK] QUICKSTART.md
) else (
    echo   [!] QUICKSTART.md no encontrado
)

if exist "frontend\README.md" (
    echo   [OK] frontend\README.md
) else (
    echo   [!] frontend\README.md no encontrado
)

echo.
echo ==================================
echo [OK] Verificacion completada exitosamente
echo ==================================
echo.
echo Proximos pasos:
echo 1. Backend:  cd backend ^& python -m uvicorn app.main:app --reload
echo 2. Frontend: cd frontend ^& python -m http.server 5500
echo 3. Abre:     http://localhost:5500
echo.
echo Usuarios de prueba:
echo   - admin@example.com / admin123
echo   - hr@example.com / hr123
echo   - candidate@example.com / candidate123
echo.
