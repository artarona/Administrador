#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SISTEMA DANTEPROPIEDADES - VERSIÓN CON CREACIÓN AUTOMÁTICA DE TABLA
"""

import os
import psycopg2
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variables de entorno
ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN', '2205')
DATABASE_URL = os.environ.get('DATABASE_URL')

print("=" * 70)
print("🚀 SISTEMA DANTEPROPIEDADES - CREANDO TABLA AUTOMÁTICAMENTE")
print("=" * 70)

# Función para inicializar la base de datos
def init_database():
    """Crear la tabla contactos si no existe"""
    if not DATABASE_URL:
        print("❌ DATABASE_URL no configurada")
        return False
    
    try:
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
        cursor = conn.cursor()
        
        # Crear tabla contactos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contactos (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(150) NOT NULL,
                email VARCHAR(150) NOT NULL UNIQUE,
                telefono VARCHAR(30),
                mensaje TEXT,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Tabla 'contactos' creada/verificada exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error creando tabla: {str(e)}")
        return False

# Inicializar base de datos al iniciar
init_database()

# Inicializar Flask
app = Flask(__name__)
CORS(app)

# Función para conectar a PostgreSQL
def get_db():
    """Conectar a la base de datos"""
    if not DATABASE_URL:
        return None
    
    try:
        return psycopg2.connect(DATABASE_URL, connect_timeout=10)
    except Exception as e:
        logger.error(f"Error DB: {str(e)}")
        return None

# Ruta principal
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

# Health check
@app.route('/health', methods=['GET'])
def health_check():
    """Verificar estado del sistema"""
    conn = get_db()
    
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()
            db_status = "connected"
        except:
            db_status = "error"
    else:
        db_status = "disconnected"
    
    return jsonify({
        'status': 'healthy' if db_status == 'connected' else 'degraded',
        'database': db_status,
        'timestamp': datetime.now().isoformat()
    })

# Obtener todos los contactos (VERSIÓN SIMPLIFICADA)
@app.route('/admin/data', methods=['GET'])
def get_all_contacts():
    """Obtener lista de contactos - VERSIÓN SIMPLE"""
    # Verificar token
    token = request.args.get('token', '')
    if token != ADMIN_TOKEN:
        return jsonify({'error': 'Token inválido'}), 401
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Error de conexión a base de datos'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Primero, asegurarse de que la tabla existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contactos (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(150) NOT NULL,
                email VARCHAR(150) NOT NULL UNIQUE,
                telefono VARCHAR(30),
                mensaje TEXT,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        
        # Ahora obtener los datos
        cursor.execute("""
            SELECT id, nombre, email, telefono, mensaje
            FROM contactos 
            ORDER BY id DESC
        """)
        
        contactos = []
        for row in cursor.fetchall():
            contactos.append({
                'id': row[0],
                'nombre': row[1] or '',
                'email': row[2] or '',
                'telefono': row[3] or '',
                'mensaje': row[4] or ''
            })
        
        cursor.close()
        
        return jsonify({
            'success': True,
            'data': contactos,
            'count': len(contactos)
        })
        
    except Exception as e:
        logger.error(f"Error en /admin/data: {str(e)}")
        return jsonify({'error': 'Error interno', 'details': str(e)}), 500
    finally:
        conn.close()

# Agregar nuevo contacto (VERSIÓN SIMPLIFICADA)
@app.route('/admin/add', methods=['POST'])
def add_contact():
    """Agregar un nuevo contacto - VERSIÓN SIMPLE"""
    # Verificar token
    token = request.args.get('token', '')
    if token != ADMIN_TOKEN:
        return jsonify({'error': 'Token inválido'}), 401
    
    # Obtener datos JSON
    try:
        datos = request.get_json()
    except:
        return jsonify({'error': 'Datos inválidos'}), 400
    
    if not datos:
        return jsonify({'error': 'No hay datos'}), 400
    
    # Validar campos
    nombre = datos.get('nombre', '').strip()
    email = datos.get('email', '').strip().lower()
    
    if not nombre or not email:
        return jsonify({'error': 'Nombre y email requeridos'}), 400
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Error de conexión a base de datos'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Primero crear tabla si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contactos (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(150) NOT NULL,
                email VARCHAR(150) NOT NULL UNIQUE,
                telefono VARCHAR(30),
                mensaje TEXT,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        
        # Insertar nuevo contacto
        cursor.execute("""
            INSERT INTO contactos (nombre, email, telefono, mensaje)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (nombre, email, datos.get('telefono', ''), datos.get('mensaje', '')))
        
        nuevo_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': 'Contacto agregado',
            'id': nuevo_id
        })
        
    except psycopg2.IntegrityError:
        return jsonify({'error': 'El email ya existe'}), 400
    except Exception as e:
        logger.error(f"Error en /admin/add: {str(e)}")
        return jsonify({'error': 'Error interno', 'details': str(e)}), 500
    finally:
        conn.close()

# Endpoint para crear tabla manualmente
@app.route('/admin/create-table', methods=['POST'])
def create_table():
    """Crear tabla manualmente (para diagnóstico)"""
    token = request.args.get('token', '')
    if token != ADMIN_TOKEN:
        return jsonify({'error': 'Token inválido'}), 401
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Crear tabla
        cursor.execute("""
            DROP TABLE IF EXISTS contactos;
            CREATE TABLE contactos (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(150) NOT NULL,
                email VARCHAR(150) NOT NULL UNIQUE,
                telefono VARCHAR(30),
                mensaje TEXT,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Tabla contactos creada exitosamente'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Iniciar servidor
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n🎯 Servidor iniciando en puerto {port}")
    print("=" * 70)
    app.run(host='0.0.0.0', port=port)