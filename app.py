#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sistema Administrativo Dantepropiedades - Backend Flask
Versión Simplificada y Funcional para Render
"""

import os
import psycopg2
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import logging
import traceback

# Configuración
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN', '2205')
DATABASE_URL = os.environ.get('DATABASE_URL')

print("=" * 60)
print("🚀 SISTEMA ADMINISTRATIVO DANTEPROPIEDADES")
print("=" * 60)

# Verificar variables de entorno
if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL no configurada")
    print("💡 Configúrala en Render -> Environment")
    DATABASE_URL = ""  # Continuar pero mostrar error

if DATABASE_URL:
    # Mostrar URL segura (sin contraseña)
    if '@' in DATABASE_URL:
        parts = DATABASE_URL.split('@')
        if len(parts) == 2:
            print(f"🔗 Base de datos: postgresql://***@{parts[1]}")
    else:
        print(f"🔗 Base de datos: {DATABASE_URL[:50]}...")

# Inicializar Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dantepropiedades-secret-key-2024'
CORS(app)

# 🗄️ FUNCIÓN DE CONEXIÓN A POSTGRESQL
def get_db():
    """Obtener conexión a PostgreSQL"""
    try:
        if not DATABASE_URL:
            raise Exception("DATABASE_URL no configurada")
        
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
        return conn
    except Exception as e:
        logger.error(f"❌ Error conectando a PostgreSQL: {str(e)}")
        return None

# 🏠 RUTAS PRINCIPALES
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

# 🔐 FUNCIONES AUXILIARES
def verificar_token():
    """Verificar token de administrador"""
    token = request.args.get('token', '')
    if token != ADMIN_TOKEN:
        logger.warning(f"Token inválido recibido: {token}")
        return False
    return True

# 📊 API ENDPOINTS
@app.route('/admin/data', methods=['GET'])
def admin_data():
    """Obtener todos los contactos"""
    if not verificar_token():
        return jsonify({'error': 'Token de administrador inválido'}), 401
    
    conn = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'error': 'Error de conexión a base de datos'}), 500
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nombre, email, telefono, mensaje,
                   fecha_creacion, fecha_actualizacion
            FROM contactos
            ORDER BY fecha_creacion DESC
        """)
        
        rows = cursor.fetchall()
        contactos = []
        
        for row in rows:
            contactos.append({
                'id': row[0],
                'nombre': row[1] or '',
                'email': row[2] or '',
                'telefono': row[3] or '',
                'mensaje': row[4] or '',
                'fecha_creacion': row[5].isoformat() if row[5] else '',
                'fecha_actualizacion': row[6].isoformat() if row[6] else ''
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
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/admin/add', methods=['POST'])
def admin_add():
    """Agregar nuevo contacto"""
    logger.info(f"📥 Request recibido en /admin/add")
    
    if not verificar_token():
        return jsonify({'error': 'Token de administrador inválido'}), 401
    
    conn = None
    try:
        # Obtener datos del request
        content_type = request.headers.get('Content-Type', '')
        logger.info(f"Content-Type: {content_type}")
        
        datos = None
        if 'application/json' in content_type:
            try:
                datos = request.get_json(force=True, silent=False)
                logger.info(f"Datos JSON: {datos}")
            except Exception as json_error:
                logger.error(f"Error parseando JSON: {str(json_error)}")
                return jsonify({'error': 'Formato JSON inválido'}), 400
        else:
            # Intentar obtener como form data
            datos = request.form.to_dict()
            logger.info(f"Datos Form: {datos}")
        
        if not datos:
            # Intentar leer body raw
            try:
                raw_body = request.get_data(as_text=True)
                logger.error(f"Body raw: {raw_body[:500]}")
                return jsonify({'error': 'No se recibieron datos válidos'}), 400
            except:
                return jsonify({'error': 'No se recibieron datos'}), 400
        
        # Validar datos requeridos
        nombre = datos.get('nombre', '').strip()
        email = datos.get('email', '').strip()
        
        if not nombre:
            return jsonify({'error': 'El nombre es requerido'}), 400
        if not email:
            return jsonify({'error': 'El email es requerido'}), 400
        
        # Conectar a la base de datos
        conn = get_db()
        if not conn:
            return jsonify({'error': 'Error de conexión a base de datos'}), 500
        
        cursor = conn.cursor()
        
        # Verificar si el email ya existe
        cursor.execute("SELECT id FROM contactos WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({'error': 'Ya existe un contacto con este email'}), 400
        
        # Insertar nuevo contacto
        cursor.execute("""
            INSERT INTO contactos (nombre, email, telefono, mensaje, fecha_creacion, fecha_actualizacion)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            nombre,
            email,
            datos.get('telefono', ''),
            datos.get('mensaje', ''),
            datetime.now(),
            datetime.now()
        ))
        
        contacto_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        
        logger.info(f"✅ Contacto agregado: ID {contacto_id}")
        
        return jsonify({
            'success': True,
            'message': 'Contacto agregado exitosamente',
            'id': contacto_id,
            'timestamp': datetime.now().isoformat()
        })
        
    except psycopg2.IntegrityError as e:
        logger.error(f"Error de integridad: {str(e)}")
        if conn:
            conn.rollback()
        if 'unique constraint' in str(e).lower() or 'duplicate' in str(e).lower():
            return jsonify({'error': 'Ya existe un contacto con este email'}), 400
        else:
            return jsonify({'error': 'Error en base de datos'}), 500
    except Exception as e:
        logger.error(f"Error en /admin/add: {str(e)}")
        traceback.print_exc()
        if conn:
            conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/admin/update', methods=['PUT'])
def admin_update():
    """Actualizar contacto"""
    if not verificar_token():
        return jsonify({'error': 'Token inválido'}), 401
    
    conn = None
    try:
        datos = request.get_json()
        if not datos or not datos.get('email'):
            return jsonify({'error': 'Email es requerido'}), 400
        
        conn = get_db()
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
        cursor.close()
        
        return jsonify({'success': True, 'message': 'Contacto actualizado'})
        
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/admin/delete', methods=['DELETE'])
def admin_delete():
    """Eliminar contacto"""
    if not verificar_token():
        return jsonify({'error': 'Token inválido'}), 401
    
    conn = None
    try:
        datos = request.get_json()
        if not datos or not datos.get('email'):
            return jsonify({'error': 'Email es requerido'}), 400
        
        conn = get_db()
        if not conn:
            return jsonify({'error': 'Error de conexión a base de datos'}), 500
        
        cursor = conn.cursor()
        cursor.execute("DELETE FROM contactos WHERE email = %s RETURNING id", (datos['email'],))
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Contacto no encontrado'}), 404
        
        conn.commit()
        cursor.close()
        
        return jsonify({'success': True, 'message': 'Contacto eliminado'})
        
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/admin/clear', methods=['DELETE'])
def admin_clear():
    """Limpiar todos los contactos"""
    if not verificar_token():
        return jsonify({'error': 'Token inválido'}), 401
    
    conn = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'error': 'Error de conexión a base de datos'}), 500
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM contactos")
        count = cursor.fetchone()[0]
        
        cursor.execute("DELETE FROM contactos")
        conn.commit()
        cursor.close()
        
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
            conn.close()

# 🩺 RUTAS DE DIAGNÓSTICO
@app.route('/health', methods=['GET'])
def health_check():
    """Verificar estado del servicio"""
    conn = None
    try:
        conn = get_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            db_status = "connected"
        else:
            db_status = "disconnected"
    except:
        db_status = "error"
    finally:
        if conn:
            conn.close()
    
    return jsonify({
        'status': 'healthy' if db_status == 'connected' else 'degraded',
        'database': db_status,
        'timestamp': datetime.now().isoformat(),
        'service': 'Dante Propiedades Admin'
    })

@app.route('/api/test', methods=['GET'])
def api_test():
    """Endpoint de prueba simple"""
    return jsonify({
        'status': 'ok',
        'message': 'API funcionando',
        'timestamp': datetime.now().isoformat()
    })

# 🚀 INICIALIZACIÓN DE BASE DE DATOS
def init_database():
    """Crear tabla si no existe"""
    conn = None
    try:
        conn = get_db()
        if not conn:
            print("❌ No se pudo conectar para inicializar base de datos")
            return False
        
        cursor = conn.cursor()
        
        # Verificar si la tabla existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'contactos'
            );
        """)
        
        if not cursor.fetchone()[0]:
            print("📋 Creando tabla 'contactos'...")
            cursor.execute("""
                CREATE TABLE contactos (
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
        else:
            print("✅ Tabla 'contactos' ya existe")
        
        cursor.close()
        return True
        
    except Exception as e:
        print(f"❌ Error inicializando base de datos: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

# 🎯 MAIN
if __name__ == '__main__':
    print("\n🔧 Inicializando sistema...")
    
    # Inicializar base de datos
    if DATABASE_URL:
        if init_database():
            print("✅ Sistema inicializado correctamente")
        else:
            print("⚠️  Problemas inicializando base de datos")
    else:
        print("⚠️  DATABASE_URL no configurada, algunas funciones no estarán disponibles")
    
    port = int(os.environ.get('PORT', 5000))
    print(f"🎯 Servidor iniciado en puerto {port}")
    app.run(host='0.0.0.0', port=port, debug=False)