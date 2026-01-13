#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sistema Administrativo Dantepropiedades - Backend Flask con PostgreSQL
Versión con manejo robusto de conexiones a base de datos
"""

import os
import time
import psycopg2
import pandas as pd
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import logging
import traceback
import json
from psycopg2 import pool

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración inicial
ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN', '2205')
FLASK_ENV = os.environ.get('FLASK_ENV', 'production')
DATABASE_URL = os.environ.get('DATABASE_URL')

print("=" * 60)
print("🚀 INICIANDO SISTEMA ADMINISTRATIVO DANTEPROPIEDADES")
print("=" * 60)

# 🗄️ CONFIGURACIÓN DE CONEXIÓN A POSTGRESQL
db_pool = None

def create_database_pool():
    """Crear pool de conexiones a PostgreSQL"""
    global db_pool
    
    if not DATABASE_URL:
        print("❌ ERROR: DATABASE_URL no está configurada")
        print("💡 Solución: Configura la variable DATABASE_URL en Render")
        return None
    
    try:
        # Parsear la URL de conexión
        print(f"🔗 Intentando conectar a: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else '***'}")
        
        # Crear pool de conexiones
        db_pool = psycopg2.pool.SimpleConnectionPool(
            1,  # min connections
            10, # max connections
            DATABASE_URL
        )
        
        # Probar la conexión
        conn = db_pool.getconn()
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        
        cursor.execute("SELECT current_database();")
        db_name = cursor.fetchone()
        
        # Liberar conexión
        db_pool.putconn(conn)
        
        print(f"✅ CONEXIÓN EXITOSA A POSTGRESQL")
        print(f"📊 Versión: {db_version[0]}")
        print(f"🗃️  Base de datos: {db_name[0]}")
        
        # Verificar tabla contactos
        conn = db_pool.getconn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'contactos'
            );
        """)
        tabla_existe = cursor.fetchone()[0]
        
        if tabla_existe:
            cursor.execute("SELECT COUNT(*) FROM contactos;")
            total_contactos = cursor.fetchone()[0]
            print(f"📋 Tabla 'contactos': ✅ EXISTE ({total_contactos} registros)")
        else:
            print("⚠️  Tabla 'contactos': ❌ NO EXISTE")
            print("💡 Creando tabla...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contactos (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(100) NOT NULL,
                    email VARCHAR(100) NOT NULL UNIQUE,
                    telefono VARCHAR(20),
                    mensaje TEXT,
                    estado VARCHAR(20) DEFAULT 'activo',
                    ip_address VARCHAR(50),
                    user_agent VARCHAR(255),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            print("✅ Tabla 'contactos' creada exitosamente")
        
        db_pool.putconn(conn)
        
        return db_pool
        
    except Exception as e:
        print(f"❌ ERROR DE CONEXIÓN A POSTGRESQL: {str(e)}")
        print("💡 Posibles soluciones:")
        print("   1. Verifica que DATABASE_URL sea correcta")
        print("   2. Verifica que la base de datos esté activa en Render")
        print("   3. Verifica las credenciales")
        traceback.print_exc()
        return None

def get_db_connection():
    """Obtener conexión a la base de datos"""
    try:
        if not db_pool:
            print("⚠️  Pool no inicializado, intentando reconectar...")
            create_database_pool()
        
        if db_pool:
            return db_pool.getconn()
        else:
            print("❌ No se pudo obtener conexión: pool no disponible")
            return None
            
    except Exception as e:
        print(f"❌ Error obteniendo conexión: {str(e)}")
        return None

def release_db_connection(conn):
    """Liberar conexión a la base de datos"""
    if db_pool and conn:
        try:
            db_pool.putconn(conn)
        except:
            pass

# Inicializar Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dantepropiedades-secret-key-2024'

# 🔒 CONFIGURACIÓN CORS
CORS(app, origins=[
    "https://artarona.github.io",
    "https://administrador-63nc.onrender.com",
    "http://localhost:3000",
    "http://localhost:5000",
    "*"  # Permitir todos temporalmente para pruebas
])

# 🏠 RUTA PRINCIPAL
@app.route('/')
def index():
    """Servir el archivo index.html"""
    try:
        return send_from_directory('.', 'index.html')
    except Exception as e:
        return f"Error cargando frontend: {str(e)}", 500

@app.route('/<path:filename>')
def serve_static(filename):
    """Servir archivos estáticos"""
    try:
        return send_from_directory('.', filename)
    except Exception as e:
        return f"Error cargando archivo: {str(e)}", 404

# 🔐 VERIFICAR TOKEN
def verificar_token():
    """Verificar token de administrador"""
    token = request.args.get('token', '') or request.headers.get('Authorization', '').replace('Bearer ', '')
    return token == ADMIN_TOKEN

# 📊 RUTAS DE ADMINISTRACIÓN
@app.route('/admin/data', methods=['GET'])
def admin_data():
    """Obtener todos los contactos"""
    if not verificar_token():
        return jsonify({'error': 'Token de administrador inválido'}), 401
    
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Error de conexión a base de datos'}), 500
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nombre, email, telefono, mensaje, 
                   fecha_creacion, fecha_actualizacion
            FROM contactos 
            ORDER BY fecha_creacion DESC
        """)
        resultados = cursor.fetchall()
        
        contactos = []
        for fila in resultados:
            contacto = {
                'id': fila[0],
                'nombre': fila[1] or '',
                'email': fila[2] or '',
                'telefono': fila[3] or '',
                'mensaje': fila[4] or '',
                'fecha_creacion': fila[5].isoformat() if fila[5] else '',
                'fecha_actualizacion': fila[6].isoformat() if fila[6] else ''
            }
            contactos.append(contacto)
        
        return jsonify({
            'success': True,
            'data': contactos,
            'count': len(contactos),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Error en /admin/data: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': 'Error interno del servidor',
            'details': str(e)
        }), 500
    finally:
        if conn:
            release_db_connection(conn)

@app.route('/admin/add', methods=['POST'])
def admin_add():
    """Agregar nuevo contacto"""
    logger.info("=" * 60)
    logger.info("[REQUEST] /admin/add recibido")
    
    if not verificar_token():
        return jsonify({'error': 'Token de administrador inválido'}), 401
    
    conn = None
    try:
        # Obtener datos
        datos = request.get_json(force=True, silent=True)
        if not datos:
            return jsonify({'error': 'No se recibieron datos válidos'}), 400
        
        # Validar datos requeridos
        if not datos.get('nombre') or not datos.get('email'):
            return jsonify({'error': 'Nombre y email son requeridos'}), 400
        
        # Obtener conexión a DB
        conn = get_db_connection()
        if not conn:
            logger.error("❌ No se pudo conectar a la base de datos")
            return jsonify({'error': 'Error de conexión a base de datos'}), 500
        
        cursor = conn.cursor()
        
        # Verificar si email ya existe
        cursor.execute("SELECT id FROM contactos WHERE email = %s", (datos['email'],))
        if cursor.fetchone():
            return jsonify({'error': 'Ya existe un contacto con este email'}), 400
        
        # Insertar nuevo contacto
        current_timestamp = datetime.now()
        cursor.execute("""
            INSERT INTO contactos (
                nombre, email, telefono, mensaje, estado,
                ip_address, user_agent, timestamp, fecha_creacion, fecha_actualizacion
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            datos['nombre'],
            datos['email'],
            datos.get('telefono', ''),
            datos.get('mensaje', ''),
            'activo',
            request.headers.get('X-Forwarded-For', request.remote_addr) or '0.0.0.0',
            request.headers.get('User-Agent', 'Admin Panel'),
            current_timestamp,
            current_timestamp,
            current_timestamp
        ))
        
        contacto_id = cursor.fetchone()[0]
        conn.commit()
        
        logger.info(f"✅ Contacto agregado: ID {contacto_id}")
        logger.info("=" * 60)
        
        return jsonify({
            'success': True,
            'message': 'Contacto agregado exitosamente',
            'contacto_id': contacto_id,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Error en /admin/add: {str(e)}")
        traceback.print_exc()
        if conn:
            conn.rollback()
        return jsonify({
            'error': 'Error interno del servidor',
            'details': str(e)
        }), 500
    finally:
        if conn:
            release_db_connection(conn)

@app.route('/admin/update', methods=['PUT'])
def admin_update():
    """Actualizar contacto"""
    if not verificar_token():
        return jsonify({'error': 'Token de administrador inválido'}), 401
    
    conn = None
    try:
        datos = request.get_json()
        if not datos or not datos.get('email'):
            return jsonify({'error': 'Email es requerido'}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Error de conexión a base de datos'}), 500
        
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE contactos 
            SET nombre = %s, telefono = %s, mensaje = %s, fecha_actualizacion = %s
            WHERE email = %s
            RETURNING id
        """, (
            datos.get('nombre', ''),
            datos.get('telefono', ''),
            datos.get('mensaje', ''),
            datetime.now(),
            datos['email']
        ))
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Contacto no encontrado'}), 404
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Contacto actualizado exitosamente'
        })
        
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            release_db_connection(conn)

@app.route('/admin/delete', methods=['DELETE'])
def admin_delete():
    """Eliminar contacto"""
    if not verificar_token():
        return jsonify({'error': 'Token de administrador inválido'}), 401
    
    conn = None
    try:
        datos = request.get_json()
        if not datos or not datos.get('email'):
            return jsonify({'error': 'Email es requerido'}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Error de conexión a base de datos'}), 500
        
        cursor = conn.cursor()
        cursor.execute("DELETE FROM contactos WHERE email = %s RETURNING id", (datos['email'],))
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Contacto no encontrado'}), 404
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Contacto eliminado exitosamente'
        })
        
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            release_db_connection(conn)

@app.route('/admin/clear', methods=['DELETE'])
def admin_clear():
    """Limpiar todos los contactos"""
    if not verificar_token():
        return jsonify({'error': 'Token de administrador inválido'}), 401
    
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Error de conexión a base de datos'}), 500
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM contactos")
        count = cursor.fetchone()[0]
        
        cursor.execute("DELETE FROM contactos")
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': f'{count} contactos eliminados'
        })
        
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            release_db_connection(conn)

# 🩺 RUTAS DE DIAGNÓSTICO
@app.route('/health', methods=['GET'])
def health_check():
    """Verificar estado del sistema"""
    try:
        conn = get_db_connection()
        if conn:
            db_status = "connected"
            release_db_connection(conn)
        else:
            db_status = "disconnected"
        
        return jsonify({
            'status': 'healthy' if db_status == 'connected' else 'degraded',
            'database': db_status,
            'timestamp': datetime.now().isoformat(),
            'service': 'Dante Propiedades Admin Panel'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/debug/database', methods=['GET'])
def debug_database():
    """Información de depuración de la base de datos"""
    info = {
        'database_url_configured': bool(DATABASE_URL),
        'database_url_length': len(DATABASE_URL) if DATABASE_URL else 0,
        'database_pool_exists': bool(db_pool),
        'admin_token_configured': bool(ADMIN_TOKEN),
        'timestamp': datetime.now().isoformat()
    }
    
    # Ocultar credenciales en el log
    if DATABASE_URL and '@' in DATABASE_URL:
        info['database_url_safe'] = 'postgresql://***@' + DATABASE_URL.split('@')[1]
    
    return jsonify(info)

# 🚀 INICIALIZACIÓN
def init_app():
    """Inicializar la aplicación"""
    print("=" * 60)
    print("🔧 INICIALIZANDO APLICACIÓN...")
    print("=" * 60)
    
    print(f"🔑 Token de admin: {'✅ Configurado' if ADMIN_TOKEN else '❌ No configurado'}")
    
    if DATABASE_URL:
        print(f"🗃️  DATABASE_URL: ✅ Configurada")
        # Ocultar credenciales en logs
        safe_url = DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else '***'
        print(f"🔗 Conectando a: {safe_url}")
    else:
        print("❌ ERROR CRÍTICO: DATABASE_URL no configurada")
        print("💡 Configura la variable DATABASE_URL en Render:")
        print("   - Ve a tu servicio en Render")
        print("   - Haz clic en 'Environment'")
        print("   - Agrega DATABASE_URL con tu conexión PostgreSQL")
        return False
    
    # Inicializar pool de conexiones
    if create_database_pool():
        print("✅ Aplicación inicializada correctamente")
        return True
    else:
        print("❌ Error inicializando conexión a base de datos")
        return False

# 🎯 MAIN
if __name__ == '__main__':
    if init_app():
        port = int(os.environ.get('PORT', 5000))
        print(f"🎯 Servidor iniciado en puerto {port}")
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        print("❌ No se pudo inicializar la aplicación")
        exit(1)