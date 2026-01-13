#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SISTEMA DANTEPROPIEDADES - VERSIÓN FINAL FUNCIONAL
Base de datos: dantepropiedades_db_e3ku
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
print("🚀 SISTEMA DANTEPROPIEDADES - CONEXIÓN NUEVA")
print("=" * 70)
print(f"Iniciando: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Verificar conexión
if DATABASE_URL:
    print("✅ DATABASE_URL configurada")
else:
    print("❌ DATABASE_URL NO configurada - El sistema no funcionará")

# Inicializar Flask
app = Flask(__name__)
CORS(app)  # Permitir todas las conexiones

# Función para conectar a PostgreSQL
def get_db():
    """Conectar a la base de datos"""
    if not DATABASE_URL:
        logger.error("DATABASE_URL no configurada")
        return None
    
    try:
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
        return conn
    except Exception as e:
        logger.error(f"Error conectando a PostgreSQL: {str(e)}")
        return None

# Ruta principal - Frontend
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# Archivos estáticos
@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

# ==================== ENDPOINTS DE API ====================

# Health check
@app.route('/health', methods=['GET'])
def health_check():
    """Verificar estado del sistema"""
    conn = get_db()
    
    if conn:
        try:
            # Probar la conexión
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
        'timestamp': datetime.now().isoformat(),
        'service': 'Dante Propiedades Admin'
    })

# Obtener todos los contactos
@app.route('/admin/data', methods=['GET'])
def get_all_contacts():
    """Obtener lista de contactos"""
    # Verificar token
    token = request.args.get('token', '')
    if token != ADMIN_TOKEN:
        return jsonify({'error': 'Token de administrador inválido'}), 401
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Error de conexión a base de datos'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Crear tabla si no existe
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
        
        # Obtener datos
        cursor.execute("""
            SELECT id, nombre, email, telefono, mensaje, fecha_creacion
            FROM contactos 
            ORDER BY fecha_creacion DESC
        """)
        
        contactos = []
        for row in cursor.fetchall():
            contactos.append({
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
            'data': contactos,
            'count': len(contactos),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en /admin/data: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# Agregar nuevo contacto
@app.route('/admin/add', methods=['POST'])
def add_contact():
    """Agregar un nuevo contacto"""
    # Verificar token
    token = request.args.get('token', '')
    if token != ADMIN_TOKEN:
        return jsonify({'error': 'Token de administrador inválido'}), 401
    
    # Obtener datos JSON
    try:
        datos = request.get_json()
    except:
        return jsonify({'error': 'Formato de datos inválido'}), 400
    
    if not datos:
        return jsonify({'error': 'No se recibieron datos'}), 400
    
    # Validar campos requeridos
    nombre = datos.get('nombre', '').strip()
    email = datos.get('email', '').strip().lower()
    
    if not nombre:
        return jsonify({'error': 'El nombre es requerido'}), 400
    if not email:
        return jsonify({'error': 'El email es requerido'}), 400
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Error de conexión a base de datos'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Verificar si el email ya existe
        cursor.execute("SELECT id FROM contactos WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({'error': 'Ya existe un contacto con este email'}), 400
        
        # Insertar nuevo contacto
        cursor.execute("""
            INSERT INTO contactos (nombre, email, telefono, mensaje)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (
            nombre,
            email,
            datos.get('telefono', ''),
            datos.get('mensaje', '')
        ))
        
        nuevo_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        
        logger.info(f"✅ Contacto agregado: ID {nuevo_id}, Email: {email}")
        
        return jsonify({
            'success': True,
            'message': 'Contacto agregado exitosamente',
            'id': nuevo_id,
            'email': email
        })
        
    except psycopg2.IntegrityError:
        return jsonify({'error': 'El email ya está registrado'}), 400
    except Exception as e:
        logger.error(f"Error en /admin/add: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# Eliminar contacto
@app.route('/admin/delete', methods=['DELETE'])
def delete_contact():
    """Eliminar contacto por email"""
    token = request.args.get('token', '')
    if token != ADMIN_TOKEN:
        return jsonify({'error': 'Token inválido'}), 401
    
    try:
        datos = request.get_json()
    except:
        return jsonify({'error': 'Datos inválidos'}), 400
    
    email = datos.get('email', '').strip().lower()
    if not email:
        return jsonify({'error': 'Email es requerido'}), 400
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Error de conexión a base de datos'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM contactos WHERE email = %s", (email,))
        
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

# ==================== INICIAR SERVIDOR ====================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n🎯 Servidor iniciando en puerto {port}")
    print("🌐 URL: http://0.0.0.0:{port}/")
    print("🔧 Endpoints disponibles:")
    print("   • /health - Verificar estado")
    print("   • /admin/data?token=2205 - Obtener contactos")
    print("   • /admin/add?token=2205 - Agregar contacto")
    print("=" * 70)
    
    app.run(host='0.0.0.0', port=port, debug=False)