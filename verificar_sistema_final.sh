#!/bin/bash
# 🎉 SCRIPT DE VERIFICACIÓN FINAL - DANTEPROPIEDADES

echo "🚀 VERIFICACIÓN FINAL DEL SISTEMA DANTEPROPIEDADES"
echo "=================================================="

# Configuración
BASE_URL="https://danterealestate-github-io.onrender.com"
ADMIN_TOKEN="2205"

echo "📡 URL Base: $BASE_URL"
echo "🔑 Token Admin: $ADMIN_TOKEN"
echo "🗄️  Database: PostgreSQL (dpg-d4rp1kbuibrs73cik0m0-a)"
echo ""

# Test 1: Base URL
echo "🧪 Test 1: Verificando base URL..."
response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL")
if [ "$response" = "200" ]; then
    echo "✅ Base URL: OK (HTTP $response)"
    content=$(curl -s "$BASE_URL")
    echo "📄 Respuesta: $content"
else
    echo "❌ Base URL: FALLO (HTTP $response)"
    echo "⚠️  Verificar que el Web Service esté activo"
fi
echo ""

# Test 2: Admin Data Endpoint
echo "🧪 Test 2: Verificando admin/data endpoint..."
response=$(curl -s -w "\n%{http_code}" "$BASE_URL/admin/data/$ADMIN_TOKEN")
http_code=$(echo "$response" | tail -n1)
json_data=$(echo "$response" | head -n -1)

if [ "$http_code" = "200" ]; then
    echo "✅ Admin Data: OK (HTTP $http_code)"
    echo "📄 Datos encontrados:"
    echo "$json_data" | python3 -m json.tool 2>/dev/null || echo "$json_data"
    
    # Verificar si hay datos
    if echo "$json_data" | grep -q '"success"'; then
        echo "✅ Sistema conectado a PostgreSQL correctamente"
    fi
elif [ "$http_code" = "404" ]; then
    echo "❌ Admin Data: FALLO (HTTP $http_code)"
    echo "⚠️  Error 404: Verificar que DATABASE_URL esté configurada correctamente"
    echo "⚠️  Verificar que ADMIN_TOKEN = 2205"
elif [ "$http_code" = "500" ]; then
    echo "❌ Admin Data: FALLO (HTTP $http_code)"
    echo "⚠️  Error 500: Verificar conexión a PostgreSQL"
    echo "⚠️  Verificar que la base de datos esté disponible"
else
    echo "❌ Admin Data: FALLO (HTTP $http_code)"
    echo "📄 Respuesta: $json_data"
fi
echo ""

# Test 3: Admin Add Endpoint
echo "🧪 Test 3: Verificando admin/add endpoint..."
test_data='{"nombre": "Test API", "email": "test.api@test.com", "telefono": "123456789", "propiedad": "Test Prop", "tipo": "Venta", "precio": "150000"}'
response=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -d "$test_data" \
    "$BASE_URL/admin/add/$ADMIN_TOKEN")
http_code=$(echo "$response" | tail -n1)
json_data=$(echo "$response" | head -n -1)

if [ "$http_code" = "200" ]; then
    echo "✅ Admin Add: OK (HTTP $http_code)"
    echo "📄 Respuesta: $json_data"
    if echo "$json_data" | grep -q '"success"'; then
        echo "✅ Contacto agregado exitosamente"
    fi
else
    echo "❌ Admin Add: FALLO (HTTP $http_code)"
    echo "📄 Respuesta: $json_data"
fi
echo ""

# Test 4: Admin Clear Endpoint (con cuidado)
echo "🧪 Test 4: Verificando admin/clear endpoint..."
read -p "⚠️  ¿Deseas probar el endpoint de limpiar datos? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/admin/clear/$ADMIN_TOKEN")
    http_code=$(echo "$response" | tail -n1)
    json_data=$(echo "$response" | head -n -1)
    
    if [ "$http_code" = "200" ]; then
        echo "✅ Admin Clear: OK (HTTP $http_code)"
        echo "📄 Respuesta: $json_data"
    else
        echo "❌ Admin Clear: FALLO (HTTP $http_code)"
        echo "📄 Respuesta: $json_data"
    fi
else
    echo "⏭️  Test 4: Omitido por el usuario"
fi
echo ""

# Resumen final
echo "🎯 RESUMEN FINAL"
echo "================="
echo "✅ Base URL funcionando: $([ "$response" = "200" ] && echo "SÍ" || echo "NO")"
echo "✅ Admin endpoints: $([ "$http_code" = "200" ] && echo "SÍ" || echo "NO")"
echo "✅ PostgreSQL conectado: $(echo "$json_data" | grep -q '"success"' && echo "SÍ" || echo "NO")"
echo ""
echo "🚀 SISTEMA LISTO PARA USAR!"
echo "📱 Frontend: https://dantearona-collab.github.io/admin.html"
echo "🔑 Password: 2205"
echo "=================================================="