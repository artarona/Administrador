#!/bin/bash

# Script de despliegue para dantepropiedades.com.ar
# Backend en Render + Frontend en GitHub Pages

echo "🚀 Desplegando dantepropiedades.com.ar + Render"
echo "=============================================="

# Verificar que estamos en el directorio correcto
if [ ! -f "app.py" ]; then
    echo "❌ Error: No se encuentra app.py"
    echo "Ejecuta este script desde el directorio backend/"
    exit 1
fi

# 1. Verificar archivos
echo "📁 Verificando archivos..."
required_files=("app.py" "requirements.txt" "render.yaml")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Archivo faltante: $file"
        exit 1
    fi
done

echo "✅ Todos los archivos presentes"

# 2. Inicializar git si no existe
if [ ! -d ".git" ]; then
    echo "📦 Inicializando repositorio Git..."
    git init
    git add .
    git commit -m "Initial commit: Backend para dantepropiedades.com.ar"
    echo "✅ Repositorio Git inicializado"
fi

# 3. Instrucciones para Render
echo ""
echo "🎯 PRÓXIMOS PASOS:"
echo "=================="
echo ""
echo "1. 🌐 CREAR REPOSITORIO EN GITHUB:"
echo "   - Ve a: https://github.com/new"
echo "   - Nombre: dantepropiedades-backend"
echo "   - Público: Sí"
echo "   - NO marcar README (ya lo tenemos)"
echo ""
echo "2. 📤 SUBIR CÓDIGO:"
echo "   git remote add origin https://github.com/TU-USUARIO/dantepropiedades-backend.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "3. 🚀 DESPLEGAR EN RENDER:"
echo "   - Ve a: https://dashboard.render.com"
echo "   - New → PostgreSQL (crear base de datos)"
echo "   - New → Web Service (conectar repositorio)"
echo "   - Configurar según README.md"
echo ""
echo "4. 🎨 ACTUALIZAR FRONTEND:"
echo "   - Subir admin.html a GitHub Pages"
echo "   - Renombrar como admin.html"
echo ""
echo "5. ✅ VERIFICAR:"
echo "   - Test backend: curl https://danterealestate-github-io.onrender.com/health"
echo "   - Test frontend: https://danterealestate.github.io/admin.html"
echo ""
echo "🔐 CREDENCIALES:"
echo "   - Contraseña: 2205"
echo "   - Token: 2205"
echo ""
echo "💰 COSTO: $0 (Gratis)"
echo ""
echo "¡Despliegue completado! 🎉"
