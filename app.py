#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sistema Administrativo Dantepropiedades - Versión Corregida Final
Backend Flask con PostgreSQL y adaptación automática de estructura BD
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

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración inicial
ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN', '2205')
FLASK_ENV = os.environ.get('FLASK_ENV', 'production')
DATABASE_URL = os.environ.get('DATABASE_URL')

print("RENDER: 🔍 DIAGNÓSTICO DE VARIABLES DE ENTORNO")
print("=" * 50)
print(f"🔧 ADMIN_TOKEN: ✅ {ADMIN_TOKEN}")
print(f"🔧 DATABASE_URL: ✅ {'Configurada' if DATABASE_URL else 'NO configurada'}")
print(f"🔧 FLASK_ENV: ✅ {FLASK_ENV}")

# Variables de entorno del sistema
if 'PORT' in os.environ:
    port = int(os.environ['PORT'])
    print(f"🔧 PORT: {port}")
else:
    port = 5000
    print(f"🔧 PORT: {port} (default)")

if DATABASE_URL:
    # Ocultar credenciales en logs
    db_safe = DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else '***'
    print(f"✅ DATABASE_URL desde variables de entorno: OK")
    print(f"🔧 DATABASE_URL (segura): postgresql:***@{db_safe}")
else:
    print("❌ DATABASE_URL no encontrada en variables de entorno")
    # Intentar leer desde archivo .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
        DATABASE_URL = os.environ.get('DATABASE_URL')
        if DATABASE_URL:
            db_safe = DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else '***'
            print(f"✅ DATABASE_URL desde archivo .env: OK")
            print(f"🔧 DATABASE_URL (.env, segura): postgresql:***@{db_safe}")
        else:
            print("❌ DATABASE_URL tampoco en archivo .env")
    except ImportError:
        print("❌ python-dotenv no instalado")

print("=" * 50)

# Inicializar Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dantepropiedades-secret-key-2024'

# 🔧 CONFIGURACIÓN CORS PARA GITHUB PAGES Y RENDER
CORS(app, origins=[
    "https://artarona.github.io",     # GitHub Pages del frontend
    "https://administrador-63nc.onrender.com",  # Backend actual
    "http://localhost:3000",          # Desarrollo local
    "http://localhost:5000",          # Desarrollo local alternativo
    "null",                          # Permitir null para desarrollo
    "*"                              # Permitir todos en desarrollo
])

# 🔗 VARIABLES GLOBALES PARA BASE DE DATOS
db_connection = None
db_cursor = None

def adaptar_estructura_bd():
    """Adaptar la estructura de la base de datos para compatibilidad"""
    global db_connection, db_cursor
    
    try:
        print("🔧 Verificando y adaptando estructura de la base de datos...")
        
        # Verificar si la tabla contactos existe
        db_cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'contactos'
            )
        """)
        
        tabla_existe = db_cursor.fetchone()[0]
        print(f"📋 Tabla 'contactos' existe: {tabla_existe}")
        
        if not tabla_existe:
            print("📝 Tabla 'contactos' no existe, creando...")
            db_cursor.execute('''
                CREATE TABLE contactos (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    telefono VARCHAR(50),
                    mensaje TEXT,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            db_connection.commit()
            print("✅ Tabla 'contactos' creada exitosamente")
            return True
        
        # Si la tabla existe, verificar qué columnas existen
        db_cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'contactos'
            ORDER BY column_name
        """)
        
        columnas_info = db_cursor.fetchall()
        columnas_existentes = [row[0] for row in columnas_info]
        print(f"📊 Columnas existentes: {columnas_existentes}")
        
        # Verificar si existe la columna 'mensaje'
        if 'mensaje' not in columnas_existentes:
            print("➕ Agregando columna 'mensaje' a la tabla...")
            db_cursor.execute('ALTER TABLE contactos ADD COLUMN mensaje TEXT')
            db_connection.commit()
            print("✅ Columna 'mensaje' agregada exitosamente")
        else:
            print("✅ Columna 'mensaje' ya existe")
        
        # Verificar si existe la columna 'fecha_creacion'
        if 'fecha_creacion' not in columnas_existentes:
            print("➕ Agregando columna 'fecha_creacion' a la tabla...")
            db_cursor.execute('ALTER TABLE contactos ADD COLUMN fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            db_connection.commit()
            print("✅ Columna 'fecha_creacion' agregada exitosamente")
        else:
            print("✅ Columna 'fecha_creacion' ya existe")
        
        # Verificar si existe la columna 'fecha_actualizacion'
        if 'fecha_actualizacion' not in columnas_existentes:
            print("➕ Agregando columna 'fecha_actualizacion' a la tabla...")
            db_cursor.execute('ALTER TABLE contactos ADD COLUMN fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            db_connection.commit()
            print("✅ Columna 'fecha_actualizacion' agregada exitosamente")
        else:
            print("✅ Columna 'fecha_actualizacion' ya existe")
        
        print("✅ Estructura de base de datos adaptada exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error adaptando estructura BD: {str(e)}")
        traceback.print_exc()
        return False

def conectar_postgresql():
    """Conectar a PostgreSQL con manejo de errores y adaptación de BD"""
    global db_connection, db_cursor
    
    try:
        if not DATABASE_URL:
            raise Exception("DATABASE_URL no configurada")
        
        print("🔗 Intentando conectar a PostgreSQL...")
        db_connection = psycopg2.connect(DATABASE_URL)
        db_cursor = db_connection.cursor()
        
        # Adaptar estructura de la base de datos
        if not adaptar_estructura_bd():
            return False
        
        print("✅ Conexión a PostgreSQL exitosa")
        print("✅ Base de datos inicializada correctamente")
        print("✅ Sistema de almacenamiento PostgreSQL inicializado")
        
        return True
        
    except Exception as e:
        print(f"❌ Error conectando a PostgreSQL: {str(e)}")
        return False

def obtener_datos():
    """Obtener todos los contactos de la base de datos"""
    try:
        if not db_connection:
            if not conectar_postgresql():
                return []
        
        db_cursor.execute("SELECT * FROM contactos ORDER BY fecha_creacion DESC")
        resultados = db_cursor.fetchall()
        
        contactos = []
        for fila in resultados:
            contacto = {
                'id': fila[0],
                'nombre': fila[1],
                'email': fila[2],
                'telefono': fila[3] if len(fila) > 3 and fila[3] else '',
                'mensaje': fila[4] if len(fila) > 4 and fila[4] else '',
                'fecha_creacion': fila[5].isoformat() if len(fila) > 5 and fila[5] else '',
                'fecha_actualizacion': fila[6].isoformat() if len(fila) > 6 and fila[6] else ''
            }
            contactos.append(contacto)
        
        return contactos
        
    except Exception as e:
        print(f"❌ Error obteniendo datos: {str(e)}")
        traceback.print_exc()
        return []

def verificar_token():
    """Verificar token de administrador"""
    token = request.args.get('token', '') or request.headers.get('Authorization', '').replace('Bearer ', '')
    return token == ADMIN_TOKEN

# 🏠 RUTA PRINCIPAL - SERVE FRONTEND
@app.route('/')
def index():
    """Servir el archivo index.html desde la raíz"""
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

# 🔐 RUTAS DE ADMINISTRACIÓN - PROTEGIDAS POR TOKEN
@app.route('/admin/data', methods=['GET'])
def admin_data():
    """Obtener todos los contactos"""
    if not verificar_token():
        return jsonify({'error': 'Token de administrador inválido'}), 401
    
    try:
        contactos = obtener_datos()
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

@app.route('/admin/add', methods=['POST'])
def admin_add():
    """Agregar nuevo contacto"""
    if not verificar_token():
        return jsonify({'error': 'Token de administrador inválido'}), 401
    
    try:
        datos = request.get_json()
        
        # Validaciones básicas
        if not datos.get('nombre') or not datos.get('email'):
            return jsonify({
                'error': 'Nombre y email son requeridos'
            }), 400
        
        # Verificar conexión a DB
        if not db_connection:
            if not conectar_postgresql():
                return jsonify({'error': 'Error de conexión a base de datos'}), 500
        
        # Verificar si el email ya existe
        try:
            db_cursor.execute("SELECT id FROM contactos WHERE email = %s", (datos['email'],))
            if db_cursor.fetchone():
                return jsonify({'error': 'Ya existe un contacto con este email'}), 400
        except Exception as e:
            print(f"⚠️ Error verificando email existente: {str(e)}")
        
        # Insertar nuevo contacto usando solo las columnas que sabemos que existen
        # Basado en los logs: ['id', 'fecha_creacion', 'fecha_actualizacion', 'email', 'telefono', 'estado', 'notas', 'ip_address', 'user_agent', 'timestamp', 'nombre']
        try:
            db_cursor.execute('''
                INSERT INTO contactos (nombre, email, telefono, estado)
                VALUES (%s, %s, %s, 'activo')
                RETURNING id
            ''', (
                datos['nombre'],
                datos['email'],
                datos.get('telefono', '')
            ))
        except Exception as e:
            print(f"❌ Error en inserción: {str(e)}")
            traceback.print_exc()
            return jsonify({
                'error': 'Error insertando en base de datos',
                'details': str(e)
            }), 500
        
        contacto_id = db_cursor.fetchone()[0]
        db_connection.commit()
        
        print(f"✅ Contacto agregado: {datos['nombre']} ({datos['email']})")
        
        return jsonify({
            'success': True,
            'message': 'Contacto agregado exitosamente',
            'contacto_id': contacto_id,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Error en /admin/add: {str(e)}")
        traceback.print_exc()
        if db_connection:
            db_connection.rollback()
        return jsonify({
            'error': 'Error interno del servidor',
            'details': str(e)
        }), 500

@app.route('/admin/update', methods=['PUT'])
def admin_update():
    """Actualizar contacto existente"""
    if not verificar_token():
        return jsonify({'error': 'Token de administrador inválido'}), 401
    
    try:
        datos = request.get_json()
        
        if not datos.get('email'):
            return jsonify({'error': 'Email es requerido para actualizar'}), 400
        
        if not db_connection:
            if not conectar_postgresql():
                return jsonify({'error': 'Error de conexión a base de datos'}), 500
        
        # Actualizar contacto usando las columnas que sabemos que existen
        try:
            db_cursor.execute('''
                UPDATE contactos 
                SET nombre = %s, telefono = %s, estado = 'activo', fecha_actualizacion = CURRENT_TIMESTAMP
                WHERE email = %s
            ''', (
                datos.get('nombre', ''),
                datos.get('telefono', ''),
                datos['email']
            ))
        except Exception as e:
            print(f"❌ Error en actualización: {str(e)}")
            traceback.print_exc()
            return jsonify({
                'error': 'Error actualizando en base de datos',
                'details': str(e)
            }), 500
        
        if db_cursor.rowcount == 0:
            return jsonify({'error': 'Contacto no encontrado'}), 404
        
        db_connection.commit()
        
        return jsonify({
            'success': True,
            'message': 'Contacto actualizado exitosamente',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Error en /admin/update: {str(e)}")
        traceback.print_exc()
        if db_connection:
            db_connection.rollback()
        return jsonify({
            'error': 'Error interno del servidor',
            'details': str(e)
        }), 500

@app.route('/admin/delete', methods=['DELETE'])
def admin_delete():
    """Eliminar contacto"""
    if not verificar_token():
        return jsonify({'error': 'Token de administrador inválido'}), 401
    
    try:
        datos = request.get_json()
        
        if not datos.get('email'):
            return jsonify({'error': 'Email es requerido para eliminar'}), 400
        
        if not db_connection:
            if not conectar_postgresql():
                return jsonify({'error': 'Error de conexión a base de datos'}), 500
        
        # Eliminar contacto
        db_cursor.execute("DELETE FROM contactos WHERE email = %s", (datos['email'],))
        
        if db_cursor.rowcount == 0:
            return jsonify({'error': 'Contacto no encontrado'}), 404
        
        db_connection.commit()
        
        return jsonify({
            'success': True,
            'message': 'Contacto eliminado exitosamente',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Error en /admin/delete: {str(e)}")
        traceback.print_exc()
        if db_connection:
            db_connection.rollback()
        return jsonify({
            'error': 'Error interno del servidor',
            'details': str(e)
        }), 500

@app.route('/admin/clear', methods=['DELETE'])
def admin_clear():
    """Limpiar todos los contactos"""
    if not verificar_token():
        return jsonify({'error': 'Token de administrador inválido'}), 401
    
    try:
        if not db_connection:
            if not conectar_postgresql():
                return jsonify({'error': 'Error de conexión a base de datos'}), 500
        
        # Contar contactos antes de eliminar
        db_cursor.execute("SELECT COUNT(*) FROM contactos")
        count = db_cursor.fetchone()[0]
        
        # Limpiar todos los datos
        db_cursor.execute("DELETE FROM contactos")
        db_connection.commit()
        
        return jsonify({
            'success': True,
            'message': f'Todos los contactos eliminados ({count} contactos)',
            'count_deleted': count,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Error en /admin/clear: {str(e)}")
        traceback.print_exc()
        if db_connection:
            db_connection.rollback()
        return jsonify({
            'error': 'Error interno del servidor',
            'details': str(e)
        }), 500

# 🔍 RUTAS DE SALUD Y ESTADO
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        db_status = "connected" if db_connection and not db_connection.closed else "disconnected"
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': db_status,
            'environment': FLASK_ENV
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/status', methods=['GET'])
def api_status():
    """Estado del API"""
    return jsonify({
        'api': 'Sistema Administrativo Dantepropiedades',
        'version': '2.2.0',
        'status': 'active',
        'database': 'PostgreSQL',
        'frontend': 'GitHub Pages + Backend Render',
        'cors': 'enabled',
        'bd_compatibility': 'automatic_adaptation',
        'timestamp': datetime.now().isoformat()
    })

# 🚀 INICIALIZACIÓN DE LA APLICACIÓN
def init_app():
    """Inicializar la aplicación"""
    try:
        print("🚀 Iniciando Sistema Administrativo Dantepropiedades...")
        print(f"🌍 Entorno: {FLASK_ENV}")
        print(f"🔑 Token de administrador: {ADMIN_TOKEN}")
        print(f"🔧 BD Compatible: Adaptación automática habilitada")
        
        # Conectar a base de datos
        if not conectar_postgresql():
            print("⚠️ Advertencia: No se pudo conectar a la base de datos inicialmente")
        
        print("✅ Aplicación inicializada correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error inicializando aplicación: {str(e)}")
        traceback.print_exc()
        return False

# 🎯 MAIN
if __name__ == '__main__':
    if init_app():
        print(f"🎯 Iniciando servidor en puerto {port}...")
        app.run(host='0.0.0.0', port=port, debug=(FLASK_ENV != 'production'))
    else:
        print("❌ No se pudo inicializar la aplicación")
        exit(1)