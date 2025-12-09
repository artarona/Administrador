# -*- coding: utf-8 -*-
"""
🚀 SISTEMA DE ALMACENAMIENTO POSTGRESQL - BACKEND RENDER
================================================================

Versión con múltiples fallbacks para DATABASE_URL
Compatible con Render.com y bases de datos en la nube
"""

import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime
import logging
import time

# Configuración de logging detallada
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

app = Flask(__name__)

# Configuración CORS para dominio personalizado
CORS(app, origins=[
    "https://dantepropiedades.com.ar",
    "https://danterealestate.github.io",
    "http://localhost:3000",
    "http://localhost:8000"
])

# 🔍 DIAGNÓSTICO COMPLETO DE VARIABLES DE ENTORNO
print("🔍 DIAGNÓSTICO DE VARIABLES DE ENTORNO")
print("=" * 50)

# Verificar todas las variables posibles
admin_token_env = os.environ.get('ADMIN_TOKEN')
database_url_env = os.environ.get('DATABASE_URL')
flask_env_env = os.environ.get('FLASK_ENV')
port_env = os.environ.get('PORT')

print(f"🔧 ADMIN_TOKEN: {'✅' if admin_token_env else '❌'} {admin_token_env or 'No encontrado'}")
print(f"🔧 DATABASE_URL: {'✅' if database_url_env else '❌'} {'Configurada' if database_url_env else 'No encontrada'}")
print(f"🔧 FLASK_ENV: {'✅' if flask_env_env else '❌'} {flask_env_env or 'No encontrada'}")
print(f"🔧 PORT: {port_env or 'No encontrada'}")

# Configuración con MÚLTIPLES FALLBACKS
ADMIN_TOKEN = admin_token_env or '2205'

# DATABASE_URL con 3 niveles de fallback
if database_url_env:
    DATABASE_URL = database_url_env
    print(f"✅ DATABASE_URL desde variables de entorno: OK")
elif os.path.exists('/data/database_url.txt'):
    try:
        with open('/data/database_url.txt', 'r') as f:
            DATABASE_URL = f.read().strip()
        print(f"✅ DATABASE_URL desde archivo: OK")
    except Exception as e:
        print(f"❌ Error leyendo DATABASE_URL de archivo: {e}")
        DATABASE_URL = None
else:
    # Fallback hardcodeado (debería ser el último recurso)
    DATABASE_URL = "postgresql://dantepropiedades_db_user:g7n7acitEIXzMHiVUZRPGB2J2vALxjeV@dpg-d4rp1kbuibrs73cik0m0-a.oregon-postgres.render.com/dantepropiedades_db"
    print(f"⚠️ DATABASE_URL hardcodeada (fallback): OK")

# Logging seguro (ocultar contraseña)
if DATABASE_URL:
    try:
        # Extraer solo la parte segura para logging
        url_parts = DATABASE_URL.split('@')
        if len(url_parts) == 2:
            safe_url = url_parts[0].split(':')[0] + ':***@' + url_parts[1]
        else:
            safe_url = '***'
        print(f"🔧 DATABASE_URL (segura): {safe_url}")
    except:
        print(f"🔧 DATABASE_URL: Configurada (oculta por seguridad)")

print("=" * 50)

class PostgreSQLStorageManager:
    """
    📊 Gestor de almacenamiento en PostgreSQL
    Con manejo robusto de errores y fallbacks
    """
    
    def __init__(self):
        self.database_available = False
        self.init_database()
    
    def get_connection(self):
        """Obtener conexión a PostgreSQL con manejo de errores"""
        if not DATABASE_URL:
            raise Exception("DATABASE_URL no está configurada")
        
        try:
            print(f"🔗 Intentando conectar a PostgreSQL...")
            conn = psycopg2.connect(DATABASE_URL)
            print(f"✅ Conexión a PostgreSQL exitosa")
            self.database_available = True
            return conn
        except Exception as e:
            print(f"❌ Error conectando a PostgreSQL: {e}")
            self.database_available = False
            raise
    
    def test_connection(self):
        """Probar conexión sin inicializar tabla"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.close()
            conn.close()
            return True
        except:
            return False
    
    def init_database(self):
        """Inicializar tabla de contactos"""
        if not DATABASE_URL:
            print("❌ DATABASE_URL no configurada, saltando inicialización")
            return
        
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            # Crear tabla si no existe
            cur.execute("""
                CREATE TABLE IF NOT EXISTS contactos (
                    id SERIAL PRIMARY KEY,
                    nombre TEXT NOT NULL,
                    email TEXT NOT NULL,
                    telefono TEXT,
                    mensaje TEXT,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            cur.close()
            conn.close()
            print("✅ Base de datos inicializada correctamente")
            
        except Exception as e:
            print(f"❌ Error inicializando base de datos: {e}")
            # No raise para permitir que la app inicie sin BD

# Inicializar gestor de almacenamiento (con manejo de errores)
try:
    storage_manager = PostgreSQLStorageManager()
    print("✅ Sistema de almacenamiento PostgreSQL inicializado")
except Exception as e:
    print(f"❌ Error inicializando sistema de almacenamiento: {e}")
    storage_manager = None

def obtener_timestamp():
    """Generar timestamp en formato ISO"""
    return int(time.time() * 1000)

def response_error(mensaje, codigo=400):
    """Generar respuesta de error estandarizada"""
    return {
        "error": True,
        "message": mensaje,
        "timestamp": obtener_timestamp()
    }, codigo

def response_success(data=None, mensaje="Operación exitosa", total=0):
    """Generar respuesta de éxito estandarizada"""
    response = {
        "success": True,
        "message": mensaje,
        "timestamp": obtener_timestamp()
    }
    if data is not None:
        response["data"] = data
    if total > 0:
        response["total"] = total
    return response

@app.route('/', methods=['GET'])
def health_check():
    """Verificar que el servicio está funcionando"""
    try:
        # Verificar estado de la base de datos
        db_status = "disconnected"
        total_contactos = 0
        
        if storage_manager and storage_manager.database_available:
            try:
                conn = storage_manager.get_connection()
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM contactos")
                total_contactos = cur.fetchone()[0]
                cur.close()
                conn.close()
                db_status = "connected"
            except:
                db_status = "connection_error"
        
        return response_success({
            "status": "healthy",
            "database": db_status,
            "total_contactos": total_contactos,
            "version": "1.1.0"
        })
        
    except Exception as e:
        return response_error(f"Service unhealthy: {str(e)}", 503)

@app.route('/admin/data/<token>', methods=['GET'])
def obtener_datos(token):
    """Obtener todos los contactos almacenados"""
    if token != ADMIN_TOKEN:
        return response_error("Token de acceso inválido", 403)
    
    if not storage_manager or not storage_manager.database_available:
        return response_error("Base de datos no disponible", 503)
    
    try:
        conn = storage_manager.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT id, nombre, email, telefono, mensaje, fecha_creacion 
            FROM contactos 
            ORDER BY fecha_creacion DESC
        """)
        
        contactos = cur.fetchall()
        cur.close()
        conn.close()
        
        # Convertir a lista de diccionarios
        contactos_list = [dict(contacto) for contacto in contactos]
        
        print(f"📊 Obteniendo {len(contactos_list)} contactos")
        
        return response_success(
            data=contactos_list,
            mensaje=f"Contactos obtenidos exitosamente",
            total=len(contactos_list)
        )
        
    except Exception as e:
        print(f"Error obteniendo datos: {e}")
        return response_error(f"Error obteniendo datos: {str(e)}", 500)

@app.route('/admin/add/<token>', methods=['POST'])
def agregar_contacto(token):
    """Agregar nuevo contacto"""
    if token != ADMIN_TOKEN:
        return response_error("Token de acceso inválido", 403)
    
    if not storage_manager or not storage_manager.database_available:
        return response_error("Base de datos no disponible", 503)
    
    try:
        data = request.get_json()
        if not data:
            return response_error("Datos JSON requeridos", 400)
        
        nombre = data.get('nombre', '').strip()
        email = data.get('email', '').strip()
        telefono = data.get('telefono', '').strip()
        mensaje = data.get('mensaje', '').strip()
        
        # Validaciones
        if not nombre or not email:
            return response_error("Nombre y email son requeridos", 400)
        
        conn = storage_manager.get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO contactos (nombre, email, telefono, mensaje)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (nombre, email, telefono, mensaje))
        
        nuevo_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"➕ Nuevo contacto agregado: {email}")
        
        return response_success(
            data={"id": nuevo_id, "nombre": nombre, "email": email},
            mensaje="Contacto agregado exitosamente"
        )
        
    except Exception as e:
        print(f"Error agregando contacto: {e}")
        return response_error(f"Error agregando contacto: {str(e)}", 500)

@app.route('/admin/update/<token>', methods=['PUT'])
def actualizar_contacto(token):
    """Actualizar contacto existente"""
    if token != ADMIN_TOKEN:
        return response_error("Token de acceso inválido", 403)
    
    if not storage_manager or not storage_manager.database_available:
        return response_error("Base de datos no disponible", 503)
    
    try:
        data = request.get_json()
        if not data:
            return response_error("Datos JSON requeridos", 400)
        
        nombre = data.get('nombre', '').strip()
        email = data.get('email', '').strip()
        telefono = data.get('telefono', '').strip()
        mensaje = data.get('mensaje', '').strip()
        
        if not nombre or not email:
            return response_error("Nombre y email son requeridos", 400)
        
        conn = storage_manager.get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE contactos 
            SET nombre = %s, telefono = %s, mensaje = %s
            WHERE email = %s
            RETURNING id
        """, (nombre, telefono, mensaje, email))
        
        if cur.rowcount == 0:
            cur.close()
            conn.close()
            return response_error("Contacto no encontrado", 404)
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✏️ Contacto actualizado: {email}")
        
        return response_success(
            data={"email": email, "nombre": nombre},
            mensaje="Contacto actualizado exitosamente"
        )
        
    except Exception as e:
        print(f"Error actualizando contacto: {e}")
        return response_error(f"Error actualizando contacto: {str(e)}", 500)

@app.route('/admin/delete/<token>', methods=['DELETE'])
def eliminar_contacto(token):
    """Eliminar contacto por email"""
    if token != ADMIN_TOKEN:
        return response_error("Token de acceso inválido", 403)
    
    if not storage_manager or not storage_manager.database_available:
        return response_error("Base de datos no disponible", 503)
    
    try:
        data = request.get_json()
        if not data:
            return response_error("Datos JSON requeridos", 400)
        
        email = data.get('email', '').strip()
        if not email:
            return response_error("Email es requerido", 400)
        
        conn = storage_manager.get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            DELETE FROM contactos 
            WHERE email = %s
            RETURNING id
        """, (email,))
        
        if cur.rowcount == 0:
            cur.close()
            conn.close()
            return response_error("Contacto no encontrado", 404)
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"🗑️ Contacto eliminado: {email}")
        
        return response_success(
            data={"email": email},
            mensaje="Contacto eliminado exitosamente"
        )
        
    except Exception as e:
        print(f"Error eliminando contacto: {e}")
        return response_error(f"Error eliminando contacto: {str(e)}", 500)

@app.route('/admin/clear/<token>', methods=['DELETE'])
def limpiar_todos_datos(token):
    """Limpiar todos los datos de contactos"""
    if token != ADMIN_TOKEN:
        return response_error("Token de acceso inválido", 403)
    
    if not storage_manager or not storage_manager.database_available:
        return response_error("Base de datos no disponible", 503)
    
    try:
        conn = storage_manager.get_connection()
        cur = conn.cursor()
        
        cur.execute("DELETE FROM contactos")
        eliminados = cur.rowcount
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"🧹 Todos los datos eliminados: {eliminados} registros")
        
        return response_success(
            data={"eliminados": eliminados},
            mensaje="Todos los datos eliminados exitosamente"
        )
        
    except Exception as e:
        print(f"Error limpiando datos: {e}")
        return response_error(f"Error limpiando datos: {str(e)}", 500)

@app.route('/admin/export/<token>', methods=['GET'])
def exportar_datos(token):
    """Exportar contactos a archivo Excel"""
    if token != ADMIN_TOKEN:
        return response_error("Token de acceso inválido", 403)
    
    if not storage_manager or not storage_manager.database_available:
        return response_error("Base de datos no disponible", 503)
    
    try:
        conn = storage_manager.get_connection()
        df = pd.read_sql("SELECT * FROM contactos ORDER BY fecha_creacion DESC", conn)
        conn.close()
        
        # Crear archivo Excel temporal
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        df.to_excel(temp_file.name, index=False)
        
        print(f"📊 Datos exportados: {len(df)} contactos")
        
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=f"contactos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        print(f"Error exportando datos: {e}")
        return response_error(f"Error exportando datos: {str(e)}", 500)

# 🔍 RUTA DE DIAGNÓSTICO PARA VERIFICAR VARIABLES
@app.route('/debug', methods=['GET'])
def debug_info():
    """Información de diagnóstico"""
    return {
        "debug": True,
        "variables": {
            "ADMIN_TOKEN": ADMIN_TOKEN,
            "DATABASE_URL_configured": bool(DATABASE_URL),
            "storage_manager_available": storage_manager is not None,
            "database_available": storage_manager.database_available if storage_manager else False
        },
        "timestamp": obtener_timestamp()
    }

if __name__ == '__main__':
    print("🚀 Iniciando aplicación Flask...")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)