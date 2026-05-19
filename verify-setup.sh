#!/bin/bash
# verify-setup.sh
# Script para verificar que el proyecto está correctamente configurado

echo "================================"
echo "AI Recruitment Platform - Verificación"
echo "================================"
echo ""

# Verificar estructura frontend
echo "✓ Verificando estructura del frontend..."
if [ -f "frontend/index.html" ] && [ -f "frontend/styles.css" ] && [ -f "frontend/js/app.js" ]; then
    echo "  ✓ Archivos principales del frontend presentes"
else
    echo "  ✗ Falta archivos del frontend"
    exit 1
fi

# Verificar archivos JS
echo ""
echo "✓ Verificando módulos JavaScript..."
required_files=(
    "frontend/js/config.js"
    "frontend/js/mock-auth.js"
    "frontend/js/api-client.js"
    "frontend/js/router.js"
    "frontend/js/utils.js"
    "frontend/js/pages/home.js"
    "frontend/js/pages/job-detail.js"
    "frontend/js/pages/apply.js"
    "frontend/js/pages/hr-dashboard.js"
    "frontend/js/pages/admin-dashboard.js"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ Falta: $file"
        exit 1
    fi
done

# Verificar estructura backend
echo ""
echo "✓ Verificando estructura del backend..."
if [ -f "backend/app/main.py" ]; then
    echo "  ✓ Backend main.py presente"
else
    echo "  ✗ Falta backend/app/main.py"
    exit 1
fi

# Verificar documentación
echo ""
echo "✓ Verificando documentación..."
docs=(
    "QUICKSTART.md"
    "frontend/README.md"
    "backend/README.md"
)

for doc in "${docs[@]}"; do
    if [ -f "$doc" ]; then
        echo "  ✓ $doc"
    else
        echo "  ! Documento no encontrado: $doc (no crítico)"
    fi
done

echo ""
echo "================================"
echo "✓ Verificación completada exitosamente"
echo "================================"
echo ""
echo "Próximos pasos:"
echo "1. Backend:  cd backend && python -m uvicorn app.main:app --reload"
echo "2. Frontend: cd frontend && python -m http.server 5500"
echo "3. Abre:     http://localhost:5500"
echo ""
echo "Usuarios de prueba:"
echo "  - admin@example.com / admin123"
echo "  - hr@example.com / hr123"
echo "  - candidate@example.com / candidate123"
echo ""
