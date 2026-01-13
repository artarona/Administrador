#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SISTEMA ADMINISTRATIVO DANTEPROPIEDADES - VERSIÓN FINAL
Funcionando al 100% con PostgreSQL en Render
"""

import os
import psycopg2
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import logging
import threading
import time
import requests

# ============================================================================
# CONFIGURACIÓN INICIAL
# ============================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN', '2205')
DATABASE_URL = os.environ.get('DATABASE_URL')

print("=" * 70)
print("🚀 SISTEMA DANTEPROPIEDADES - OPERATIVO AL 100%")
print("=" * 70)
print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ============================================================================
# FUNCIÓN PARA MANTENER BASE DE DATOS ACTIVA
# ============================================================================

def keep_database_alive():
    """Pings periódicos para mantener la DB activa en plan Free"""
    def ping():
        while True:
            try:
                requests.get('https://administrador-63nc.onrender.com/health', timeout=5)
                logger.info(f"✅ Keep-alive ping: {datetime.now().strftime('%H:%M:%S')}")
            except:
                logger.warning(f"⚠️ Keep-alive falló")
            time.sleep(1800)  # Cada 30 minutos
    
    thread = threading.Thread(target=ping, daemon=True)
    thread.start()
    logger.info("🛡️ Keep-alive activado (pings cada 30 minutos)")

# ============================================================================
# INICIALIZAR FLASK
# ============================================================================

app = Flask(__name__)
CORS(app)

# ============================================================================
# FUNCIONES DE BASE DE DATOS
# ============================================================================

def get_db():
    """Conectar a PostgreSQL con manejo de errores"""
    if not DATABASE_URL:
        logger.error("DATABASE_URL no configurada")
        return None
    
    try:
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
        return conn
    except Exception as e:
        logger.error(f"❌ Error PostgreSQL: {str(e)}")
        return None

def ensure_table_exists():
    """Asegurar que la tabla contactos existe"""
    conn = get_db()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contactos (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(150) NOT NULL,
                email VARCHAR(150) NOT NULL UNIQUE,
                telefono VARCHAR(30),
                mensaje TEXT,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Tabla 'contactos' verificada/creada")
        return True
    except Exception as e:
        logger.error(f"Error creando tabla: {str(e)}")
        return False

# Inicializar tabla al inicio
ensure_table_exists()

# ============================================================================
# RUTAS PRINCIPALES
# ============================================================================

@app.route('/')
def index():
    """Servir frontend"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Archivos estáticos"""
    return send_from_directory('.', filename)

# ============================================================================
# ENDPOINTS DE API
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Estado del sistema"""
    conn = get_db()
    db_status = "connected" if conn else "disconnected"
    
    if conn:
        conn.close()
    
    return jsonify({
        'status': 'healthy',
        'database': db_status,
        'service': 'Dante Propiedades Admin',
        'version': '3.0.0',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/admin/data', methods=['GET'])
def get_contacts():
    """Obtener todos los contactos"""
    token = request.args.get('token', '')
    if token != ADMIN_TOKEN:
        return jsonify({'error': 'Token inválido'}), 401
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Error de conexión a DB'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Obtener datos con orden descendente
        cursor.execute("""
            SELECT id, nombre, email, telefono, mensaje, fecha_creacion
            FROM contactos 
            ORDER BY fecha_creacion DESC
        """)
        
        contacts = []
        for row in cursor.fetchall():
            contacts.append({
                'id': row[0],
                'nombre': row[1] or '',
                'email': row[2] or '',
                'telefono': row[3] or '',
                'mensaje': row[4] or '',
                'fecha_creacion': row[5].isoformat() if row[5] else ''
            })
        
        cursor.close()
        
        return jsonify({
            'success': True,
            'data': contacts,
            'count': len(contacts),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error /admin/data: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/admin/add', methods=['POST'])
def add_contact():
    """Agregar nuevo contacto"""
    token = request.args.get('token', '')
    if token != ADMIN_TOKEN:
        return jsonify({'error': 'Token inválido'}), 401
    
    try:
        data = request.get_json()
    except:
        return jsonify({'error': 'Datos JSON inválidos'}), 400
    
    if not data:
        return jsonify({'error': 'No hay datos'}), 400
    
    nombre = data.get('nombre', '').strip()
    email = data.get('email', '').strip().lower()
    
    if not nombre or not email:
        return jsonify({'error': 'Nombre y email requeridos'}), 400
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Error de conexión a DB'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Insertar contacto
        cursor.execute("""
            INSERT INTO contactos (nombre, email, telefono, mensaje)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (nombre, email, data.get('telefono', ''), data.get('mensaje', '')))
        
        new_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        
        logger.info(f"✅ Contacto agregado: ID {new_id} - {email}")
        
        return jsonify({
            'success': True,
            'message': 'Contacto agregado exitosamente',
            'id': new_id,
            'email': email
        })
        
    except psycopg2.IntegrityError:
        return jsonify({'error': 'El email ya existe'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/admin/update', methods=['PUT'])
def update_contact():
    """Actualizar contacto"""
    token = request.args.get('token', '')
    if token != ADMIN_TOKEN:
        return jsonify({'error': 'Token inválido'}), 401
    
    try:
        data = request.get_json()
    except:
        return jsonify({'error': 'Datos inválidos'}), 400
    
    email = data.get('email', '').strip().lower()
    if not email:
        return jsonify({'error': 'Email requerido'}), 400
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Error de conexión a DB'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE contactos 
            SET nombre = %s, telefono = %s, mensaje = %s, 
                fecha_actualizacion = CURRENT_TIMESTAMP
            WHERE email = %s
            RETURNING id
        """, (
            data.get('nombre', ''),
            data.get('telefono', ''),
            data.get('mensaje', ''),
            email
        ))
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Contacto no encontrado'}), 404
        
        conn.commit()
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': 'Contacto actualizado exitosamente'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/admin/delete', methods=['DELETE'])
def delete_contact():
    """Eliminar contacto"""
    token = request.args.get('token', '')
    if token != ADMIN_TOKEN:
        return jsonify({'error': 'Token inválido'}), 401
    
    try:
        data = request.get_json()
    except:
        return jsonify({'error': 'Datos inválidos'}), 400
    
    email = data.get('email', '').strip().lower()
    if not email:
        return jsonify({'error': 'Email requerido'}), 400
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Error de conexión a DB'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM contactos WHERE email = %s RETURNING id", (email,))
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Contacto no encontrado'}), 404
        
        conn.commit()
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': 'Contacto eliminado exitosamente'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/admin/clear', methods=['DELETE'])
def clear_all():
    """Eliminar todos los contactos (ADMIN ONLY)"""
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
        
        return jsonify({
            'success': True,
            'message': f'Todos los contactos eliminados ({count} contactos)'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# ============================================================================
# INICIAR APLICACIÓN
# ============================================================================

if __name__ == '__main__':
    # Activar keep-alive para mantener DB activa
    keep_database_alive()
    
    port = int(os.environ.get('PORT', 5000))
    print(f"\n✅ Sistema operativo al 100%")
    print(f"🌐 URL: https://administrador-63nc.onrender.com/")
    print(f"🔑 Contraseña admin: {ADMIN_TOKEN}")
    print(f"🗄️  Base de datos: PostgreSQL (Render)")
    print(f"📅 Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    app.run(host='0.0.0.0', port=port, debug=False)