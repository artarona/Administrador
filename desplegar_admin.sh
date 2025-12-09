#!/bin/bash

# ============================================================================
# SCRIPT DE DESPLIEGUE AUTOMATIZADO - ADMIN PANEL CORREGIDO
# ============================================================================
# Uso: ./desplegar_admin.sh
# 
# Este script automatiza la corrección de los botones admin que no funcionan
# Reemplaza admin.html y actualiza app.py con los endpoints faltantes
# ============================================================================

set -e  # Salir en caso de error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir con color
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE} $1 ${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Verificar si se ejecuta como root (no recomendado)
if [[ $EUID -eq 0 ]]; then
   print_warning "No se recomienda ejecutar como root. ¿Continuar? (y/n)"
   read -r response
   if [[ "$response" != "y" ]]; then
       exit 1
   fi
fi

print_header "DESPLIEGUE AUTOMATIZADO - ADMIN PANEL CORREGIDO"

# PASO 1: Verificar archivos necesarios
print_status "Verificando archivos necesarios..."

if [[ ! -f "admin_corregido.html" ]]; then
    print_error "admin_corregido.html no encontrado en directorio actual"
    print_error "Asegúrate de estar en el directorio correcto"
    exit 1
fi

if [[ ! -f "app.py" ]]; then
    print_error "app.py no encontrado en directorio actual"
    print_error "Asegúrate de estar en el directorio correcto"
    exit 1
fi

print_status "✅ Archivos necesarios encontrados"

# PASO 2: Crear backup
print_header "CREANDO BACKUP DE SEGURIDAD"

BACKUP_DIR="backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Buscar ubicaciones comunes de admin.html
ADMIN_PATHS=(
    "/var/www/html/admin.html"
    "/var/www/dantepropiedades/admin.html"
    "/home/*/public_html/admin.html"
    "/var/www/*/admin.html"
    "./admin.html"
)

ADMIN_FOUND=false
ADMIN_PATH=""

for path in "${ADMIN_PATHS[@]}"; do
    # Expandir wildcards
    for expanded_path in $path; do
        if [[ -f "$expanded_path" ]]; then
            ADMIN_PATH="$expanded_path"
            ADMIN_FOUND=true
            break 2
        fi
    done
done

if [[ "$ADMIN_FOUND" = true ]]; then
    print_status "Encontrado admin.html en: $ADMIN_PATH"
    cp "$ADMIN_PATH" "$BACKUP_DIR/admin_backup_original.html"
    print_status "✅ Backup de admin.html creado"
else
    print_warning "admin.html no encontrado en ubicaciones estándar"
    ADMIN_PATH="./admin.html"
fi

# Buscar app.py
APP_PATHS=(
    "/var/www/dantepropiedades/app.py"
    "/home/*/app.py"
    "/var/www/*/app.py"
    "./app.py"
)

APP_FOUND=false
APP_PATH=""

for path in "${APP_PATHS[@]}"; do
    for expanded_path in $path; do
        if [[ -f "$expanded_path" ]]; then
            APP_PATH="$expanded_path"
            APP_FOUND=true
            break 2
        fi
    done
done

if [[ "$APP_FOUND" = true ]]; then
    print_status "Encontrado app.py en: $APP_PATH"
    cp "$APP_PATH" "$BACKUP_DIR/app_backup_original.py"
    print_status "✅ Backup de app.py creado"
else
    print_warning "app.py no encontrado en ubicaciones estándar"
    APP_PATH="./app.py"
fi

print_status "📁 Backup creado en: $BACKUP_DIR"

# PASO 3: Desplegar archivos
print_header "DESPLEGANDO ARCHIVOS CORREGIDOS"

# Desplegar admin.html
print_status "Desplegando admin.html corregido..."
cp admin_corregido.html "$ADMIN_PATH"
print_status "✅ admin.html desplegado en: $ADMIN_PATH"

# Desplegar app.py
print_status "Desplegando app.py actualizado..."
cp app.py "$APP_PATH"
print_status "✅ app.py desplegado en: $APP_PATH"

# PASO 4: Establecer permisos correctos
print_status "Estableciendo permisos correctos..."

if [[ -w "$(dirname "$ADMIN_PATH")" ]]; then
    chmod 644 "$ADMIN_PATH"
    print_status "✅ Permisos de admin.html establecidos"
else
    print_warning "No se pueden establecer permisos de admin.html (requiere sudo)"
fi

if [[ -w "$(dirname "$APP_PATH")" ]]; then
    chmod 644 "$APP_PATH"
    print_status "✅ Permisos de app.py establecidos"
else
    print_warning "No se pueden establecer permisos de app.py (requiere sudo)"
fi

# PASO 5: Reiniciar servicios
print_header "REINICIANDO SERVICIOS FLASK"

# Intentar diferentes métodos de reinicio
SERVICE_RESTARTED=false

# Método 1: systemd
if command -v systemctl &> /dev/null; then
    # Buscar servicios Flask/Gunicorn
    SERVICES=$(systemctl list-units --type=service --state=running | grep -E "(flask|gunicorn|python)" | awk '{print $1}')
    
    if [[ -n "$SERVICES" ]]; then
        print_status "Reiniciando servicios encontrados..."
        for service in $SERVICES; do
            print_status "Reiniciando $service..."
            sudo systemctl restart "$service" 2>/dev/null || true
        done
        SERVICE_RESTARTED=true
    fi
fi

# Método 2: PM2
if command -v pm2 &> /dev/null && [[ "$SERVICE_RESTARTED" = false ]]; then
    print_status "Reiniciando aplicaciones PM2..."
    pm2 restart all 2>/dev/null || true
    SERVICE_RESTARTED=true
fi

# Método 3: Procesos Python/Gunicorn
if [[ "$SERVICE_RESTARTED" = false ]]; then
    print_status "Reiniciando procesos Python/Gunicorn..."
    
    # Matar procesos antiguos
    pkill -f gunicorn 2>/dev/null || true
    pkill -f "python.*app.py" 2>/dev/null || true
    sleep 2
    
    # Intentar reiniciar en directorio de app.py
    APP_DIR=$(dirname "$APP_PATH")
    if [[ -d "$APP_DIR" ]]; then
        cd "$APP_DIR"
        # Buscar comando de inicio en archivos de configuración
        if [[ -f "start.sh" ]]; then
            print_status "Ejecutando start.sh..."
            ./start.sh &
        elif [[ -f "run.sh" ]]; then
            print_status "Ejecutando run.sh..."
            ./run.sh &
        elif [[ -f "requirements.txt" ]]; then
            print_status "Iniciando Flask con gunicorn..."
            nohup gunicorn -w 4 -b 0.0.0.0:8000 app:app > flask.log 2>&1 &
        fi
    fi
    SERVICE_RESTARTED=true
fi

if [[ "$SERVICE_RESTARTED" = true ]]; then
    print_status "✅ Servicios reiniciados"
else
    print_warning "No se pudieron reiniciar automáticamente los servicios"
    print_warning "Es posible que necesites reiniciar manualmente"
fi

# PASO 6: Verificación
print_header "VERIFICACIÓN FINAL"

sleep 3  # Esperar a que los servicios se inicien

# Verificar que los archivos se desplegaron correctamente
if [[ -f "$ADMIN_PATH" ]]; then
    SIZE=$(wc -c < "$ADMIN_PATH")
    if [[ $SIZE -gt 1000 ]]; then
        print_status "✅ admin.html verificado (${SIZE} bytes)"
    else
        print_error "❌ admin.html parece estar vacío o corrupto"
    fi
fi

if [[ -f "$APP_PATH" ]]; then
    SIZE=$(wc -c < "$APP_PATH")
    if [[ $SIZE -gt 5000 ]]; then
        print_status "✅ app.py verificado (${SIZE} bytes)"
    else
        print_error "❌ app.py parece estar vacío o corrupto"
    fi
fi

# Verificar procesos
PYTHON_PROCS=$(ps aux | grep -E "(gunicorn|python.*app)" | grep -v grep | wc -l)
if [[ $PYTHON_PROCS -gt 0 ]]; then
    print_status "✅ $PYTHON_PROCS procesos Flask/Gunicorn activos"
else
    print_warning "⚠️  No se encontraron procesos Flask activos"
fi

# Verificar puerto
PORT_CHECK=$(netstat -tlnp 2>/dev/null | grep ":8000\|:5000\|:3000" | wc -l)
if [[ $PORT_CHECK -gt 0 ]]; then
    print_status "✅ Puerto Flask detectado activo"
else
    print_warning "⚠️  No se detectó puerto Flask activo"
fi

# PASO 7: Instrucciones finales
print_header "DESPLIEGUE COMPLETADO"

print_status "🎉 Despliegue completado exitosamente"
print_status ""
print_status "PRÓXIMOS PASOS:"
print_status "1. Abre tu navegador: https://dantepropiedades.com.ar/admin.html"
print_status "2. Ingresa la contraseña: 2205"
print_status "3. Verifica que no hay errores 404 en la consola (F12)"
print_status "4. Prueba todos los botones: Ver, Editar, Borrar, Agregar"
print_status ""
print_status "📁 Backup creado en: $BACKUP_DIR"
print_status "📄 admin.html desplegado en: $ADMIN_PATH"
print_status "📄 app.py desplegado en: $APP_PATH"

# Mostrar logs recientes si existen
if [[ -f "flask.log" ]]; then
    print_status ""
    print_status "📋 Últimas líneas del log Flask:"
    tail -10 flask.log
fi

print_status ""
print_status "Si encuentras problemas:"
print_status "- Revisa los logs: sudo journalctl -u [servicio] -f"
print_status "- Verifica que no hay errores de sintaxis en Python"
print_status "- Asegúrate de que todas las dependencias están instaladas"

print_header "DESPLIEGUE FINALIZADO"