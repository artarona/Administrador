#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SISTEMA ADMINISTRATIVO DANTEPROPIEDADES - VERSIÓN MEJORADA CON DEBUG
"""

import os
import psycopg2
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import logging
import sys
import time

# ============================================================================
# CONFIGURACIÓN INICIAL
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN', '2205')

# ============================================================================
# CONFIGURACIÓN DE BASE DE DATOS
# ============================================================================

# Primero intentar obtener la URL desde las variables de entorno
# ============================================================================
# CONFIGURACIÓN DE BASE DE DATOS
# ============================================================================

# Usar variable de entorno (prioridad)
# ============================================================================
# CONFIGURACIÓN DE BASE DE DATOS
# ============================================================================

# Primero intentar obtener la URL desde las variables de entorno
DATABASE_URL = os.environ.get('DATABASE_URL')

# Si no existe, usa la URL que funciona (la nueva)
if not DATABASE_URL:
    DATABASE_URL = "postgresql://dantepropiedades_user:BHKRZmYiOFgF4vgoeRjAEKNJQwVFVoms@dpg-d5jcenh5pdvs738eqr4g-a.oregon-postgres.render.com:5432/dantepropiedades_db_e3ku?sslmode=require"

# ELIMINA CUALQUIER LÍNEA QUE AGREGE ?sslmode=disable o ?sslmode=allow
# No debe haber nada como: if 'sslmode' not in DATABASE_URL: DATABASE_URL += '?sslmode=disable'
# INICIO DEL SISTEMA
# ============================================================================

print("=" * 70)
print("🚀 SISTEMA DANTEPROPIEDADES - VERSIÓN MEJORADA")
print("=" * 70)
print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
try:
    host_part = DATABASE_URL.split('@')[1].split('/')[0]
except IndexError:
    host_part = "desconocido"
print(f"📊 Base de datos: {host_part}")
print("=" * 70)

# ============================================================================
# INICIALIZAR FLASK
# ============================================================================

app = Flask(__name__)
CORS(app)

# ============================================================================
# FUNCIONES DE BASE DE DATOS
# ============================================================================

def get_db():
    """Conectar a PostgreSQL forzando SSL desactivado (conexión interna)"""
    try:
        logger.info("Intentando conectar a PostgreSQL (sin SSL)...")
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
        logger.info("✅ Conexión a PostgreSQL exitosa")
        return conn
    except Exception as e:
        logger.error(f"❌ Error PostgreSQL: {str(e)}")
        return None

def ensure_table_exists():
    """Asegurar que la tabla contactos existe (con el esquema correcto)"""
    conn = get_db()
    if not conn:
        logger.error("No se pudo conectar para verificar tabla")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Verificar si la tabla existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'contactos'
            )
        """)
        exists = cursor.fetchone()[0]
        
        if not exists:
            logger.info("📝 Creando tabla 'contactos'...")
            cursor.execute("""
                CREATE TABLE contactos (
                    timestamp VARCHAR(255) PRIMARY KEY,
                    nombre VARCHAR(255) NOT NULL,
                    email VARCHAR(255),
                    telefono VARCHAR(255),
                    estado VARCHAR(100) DEFAULT 'nuevo',
                    notas TEXT,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            logger.info("✅ Tabla 'contactos' creada exitosamente")
        else:
            logger.info("✅ Tabla 'contactos' ya existe")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error creando/verificando tabla: {str(e)}")
        return False

# Inicializar tabla al inicio
ensure_table_exists()

# ============================================================================
# RUTAS PRINCIPALES
# ============================================================================

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

@app.route('/health', methods=['GET'])
def health_check():
    conn = get_db()
    db_status = "disconnected"
    contact_count = 0
    
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM contactos")
            contact_count = cursor.fetchone()[0]
            cursor.close()
            db_status = "connected"
        except Exception as e:
            logger.error(f"Error en health check: {e}")
            db_status = "error"
        finally:
            conn.close()
    
    return jsonify({
        'status': 'healthy',
        'database': db_status,
        'contact_count': contact_count,
        'service': 'Dante Propiedades Admin',
        'version': '3.2.0',
        'timestamp': datetime.now().isoformat()
    })

# ============================================================================
# ENDPOINTS DE API (adaptados al esquema real)
# ============================================================================

@app.route('/admin/data', methods=['GET'])
def get_contacts():
    token = request.args.get('token', '')
    if token != ADMIN_TOKEN:
        logger.warning(f"Intento de acceso con token inválido: {token}")
        return jsonify({'error': 'Token inválido'}), 401
    
    logger.info("GET /admin/data - Solicitando lista de contactos")
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, nombre, email, telefono, notas as mensaje, fecha_creacion
            FROM contactos 
            ORDER BY fecha_creacion DESC
        """)
        contacts = []
        for row in cursor.fetchall():
            contacts.append({
                'id': row[0],            # timestamp
                'nombre': row[1] or '',
                'email': row[2] or '',
                'telefono': row[3] or '',
                'mensaje': row[4] or '',  # notas
                'fecha_creacion': row[5].isoformat() if row[5] else ''
            })
        
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Datos obtenidos: {len(contacts)} contactos")
        
        return jsonify({
            'success': True,
            'data': contacts,
            'count': len(contacts),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en /admin/data: {str(e)}")
        return jsonify({'error': f'Error en la consulta: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/admin/add', methods=['POST', 'OPTIONS'])
def add_contact():
    if request.method == 'OPTIONS':
        return '', 200
    
    token = request.args.get('token', '')
    if token != ADMIN_TOKEN:
        logger.warning(f"Intento de agregar con token inválido: {token}")
        return jsonify({'error': 'Token inválido'}), 401
    
    logger.info("POST /admin/add - Intentando agregar contacto")
    
    try:
        data = request.get_json()
        logger.info(f"Datos recibidos: {data}")
    except Exception as e:
        logger.error(f"Error parsing JSON: {e}")
        return jsonify({'error': 'Datos JSON inválidos'}), 400
    
    if not data:
        return jsonify({'error': 'No hay datos'}), 400
    
    nombre = data.get('nombre', '').strip()
    email = data.get('email', '').strip().lower()
    telefono = data.get('telefono', '').strip()
    mensaje = data.get('mensaje', '').strip()
    
    if not nombre or not email:
        return jsonify({'error': 'Nombre y email son requeridos'}), 400
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500
    
    try:
        timestamp = str(int(time.time() * 1000))
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO contactos (timestamp, nombre, email, telefono, notas, estado)
            VALUES (%s, %s, %s, %s, %s, 'nuevo')
        """, (timestamp, nombre, email, telefono, mensaje))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Contacto agregado exitosamente: {timestamp} - {email}")
        
        return jsonify({
            'success': True,
            'message': 'Contacto agregado exitosamente',
            'id': timestamp,
            'email': email
        })
        
    except psycopg2.IntegrityError as e:
        logger.error(f"Error de integridad: {e}")
        return jsonify({'error': 'El timestamp ya existe (contacto duplicado)'}), 400
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        return jsonify({'error': f'Error en el servidor: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/admin/update', methods=['PUT', 'OPTIONS'])
def update_contact():
    if request.method == 'OPTIONS':
        return '', 200
    
    token = request.args.get('token', '')
    if token != ADMIN_TOKEN:
        return jsonify({'error': 'Token inválido'}), 401
    
    try:
        data = request.get_json()
    except:
        return jsonify({'error': 'Datos inválidos'}), 400
    
    contacto_id = data.get('id', '').strip()
    if not contacto_id:
        return jsonify({'error': 'ID de contacto requerido'}), 400
    
    nombre = data.get('nombre', '').strip()
    email = data.get('email', '').strip().lower()
    telefono = data.get('telefono', '').strip()
    mensaje = data.get('mensaje', '').strip()
    
    if not nombre or not email:
        return jsonify({'error': 'Nombre y email son requeridos'}), 400
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Error de conexión a DB'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE contactos 
            SET nombre = %s, email = %s, telefono = %s, notas = %s,
                fecha_actualizacion = CURRENT_TIMESTAMP
            WHERE timestamp = %s
            RETURNING timestamp
        """, (nombre, email, telefono, mensaje, contacto_id))
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Contacto no encontrado'}), 404
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Contacto actualizado exitosamente'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/admin/delete', methods=['DELETE', 'OPTIONS'])
def delete_contact():
    if request.method == 'OPTIONS':
        return '', 200
    
    token = request.args.get('token', '')
    if token != ADMIN_TOKEN:
        return jsonify({'error': 'Token inválido'}), 401
    
    try:
        data = request.get_json()
    except:
        return jsonify({'error': 'Datos inválidos'}), 400
    
    contacto_id = data.get('id', '').strip()
    if not contacto_id:
        return jsonify({'error': 'ID de contacto requerido'}), 400
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Error de conexión a DB'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM contactos WHERE timestamp = %s RETURNING timestamp", (contacto_id,))
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Contacto no encontrado'}), 404
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Contacto eliminado exitosamente'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/admin/clear', methods=['DELETE', 'OPTIONS'])
def clear_all():
    if request.method == 'OPTIONS':
        return '', 200
    
    token = request.args.get('token', '')
    if token != ADMIN_TOKEN:
        return jsonify({'error': 'Token inválido'}), 401
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Error de conexión a DB'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM contactos")
        count = cursor.fetchone()[0]
        
        cursor.execute("DELETE FROM contactos")
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Todos los contactos eliminados ({count} contactos)'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

# ============================================================================
# INICIAR APLICACIÓN
# ============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("\n" + "="*70)
    print("✅ SISTEMA INICIADO CORRECTAMENTE")
    print("="*70)
    print(f"🌐 URL: https://administrador-63nc.onrender.com/")
    print(f"🔑 Token: {ADMIN_TOKEN}")
    print(f"📊 Base de datos: PostgreSQL")
    print(f"📝 Endpoints activos:")
    print(f"   - GET  /health")
    print(f"   - GET  /admin/data")
    print(f"   - POST /admin/add")
    print(f"   - PUT  /admin/update")
    print(f"   - DELETE /admin/delete")
    print(f"   - DELETE /admin/clear")
    print("="*70 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=False)