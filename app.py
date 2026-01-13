#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SISTEMA ADMINISTRATIVO DANTEPROPIEDADES - VERSIÓN DEFINITIVA
Backend Flask con PostgreSQL - Optimizado para Render
"""

import os
import sys
import psycopg2
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import logging
import traceback

# ============================================================================
# CONFIGURACIÓN INICIAL
# ============================================================================

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Obtener variables de entorno CRÍTICAS
ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN', '2205')
DATABASE_URL = os.environ.get('DATABASE_URL')
PORT = int(os.environ.get('PORT', 5000))

# ============================================================================
# DIAGNÓSTICO AL INICIAR
# ============================================================================

print("=" * 70)
print("🚀 SISTEMA ADMINISTRATIVO DANTEPROPIEDADES - INICIANDO")
print("=" * 70)
print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"🔑 Token Admin: {'✅ CONFIGURADO' if ADMIN_TOKEN else '❌ NO CONFIGURADO'}")
print(f"🗄️  DATABASE_URL: {'✅ CONFIGURADA' if DATABASE_URL else '❌ NO CONFIGURADA'}")

if DATABASE_URL:
    # Mostrar info segura (sin contraseña)
    if '@' in DATABASE_URL:
        try:
            host_part = DATABASE_URL.split('@')[1].split('/')[0]
            db_name = DATABASE_URL.split('/')[-1].split('?')[0]
            print(f"🌐 Servidor: {host_part}")
            print(f"📂 Base de datos: {db_name}")
            
            # Verificar formato Render
            if 'render.com' not in DATABASE_URL:
                print("⚠️  ADVERTENCIA: URL no parece ser de Render")
        except:
            print("ℹ️  URL configurada pero formato inusual")
else:
    print("❌ ERROR CRÍTICO: DATABASE_URL no configurada")
    print("💡 SOLUCIÓN: Configura la variable en Render -> Environment")
    print("   Nombre: DATABASE_URL")
    print("   Valor: postgresql://usuario:contraseña@servidor.render.com/basededatos")

# ============================================================================
# INICIALIZAR FLASK
# ============================================================================

app = Flask(__name__, static_folder='.')
app.config['SECRET_KEY'] = 'dante-propiedades-admin-2024-secure-key'
app.config['JSON_SORT_KEYS'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Configurar CORS para permitir todas las conexiones
CORS(app, resources={r"/*": {"origins": "*"}})

# ============================================================================
# FUNCIONES DE BASE DE DATOS
# ============================================================================

def get_db_connection():
    """Obtener conexión a PostgreSQL con manejo robusto de errores"""
    if not DATABASE_URL:
        logger.error("DATABASE_URL no configurada")
        return None
    
    try:
        # Conexión con timeout
        conn = psycopg2.connect(
            DATABASE_URL,
            connect_timeout=10
        )
        logger.info("✅ Conexión PostgreSQL establecida")
        return conn
        
    except psycopg2.OperationalError as e:
        error_msg = str(e).lower()
        logger.error(f"❌ Error de conexión PostgreSQL: {error_msg}")
        
        # Diagnóstico específico
        if "could not translate host name" in error_msg:
            logger.error("💡 Problema: Nombre de host incorrecto o no resuelve DNS")
        elif "connection refused" in error_msg:
            logger.error("💡 Problema: Conexión rechazada - ¿Base de datos activa?")
        elif "timeout" in error_msg:
            logger.error("💡 Problema: Timeout - Servidor no responde")
        elif "password authentication" in error_msg:
            logger.error("💡 Problema: Credenciales incorrectas")
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Error inesperado en conexión: {str(e)}")
        traceback.print_exc()
        return None

def init_database():
    """Inicializar base de datos - Crear tabla si no existe"""
    conn = get_db_connection()
    if not conn:
        logger.error("No se pudo conectar para inicializar BD")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Verificar si la tabla existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'contactos'
            );
        """)
        
        if cursor.fetchone()[0]:
            logger.info("✅ Tabla 'contactos' ya existe")
            
            # Contar registros existentes
            cursor.execute("SELECT COUNT(*) FROM contactos;")
            count = cursor.fetchone()[0]
            logger.info(f"📊 Registros existentes: {count}")
            
        else:
            logger.info("📋 Creando tabla 'contactos'...")
            
            # Crear tabla con estructura completa
            cursor.execute("""
                CREATE TABLE contactos (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(150) NOT NULL,
                    email VARCHAR(150) NOT NULL UNIQUE,
                    telefono VARCHAR(30),
                    mensaje TEXT,
                    estado VARCHAR(20) DEFAULT 'activo',
                    ip_address VARCHAR(50),
                    user_agent VARCHAR(255),
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT email_unique UNIQUE (email)
                );
            """)
            
            # Crear índice para búsquedas rápidas
            cursor.execute("""
                CREATE INDEX idx_contactos_email ON contactos(email);
                CREATE INDEX idx_contactos_fecha ON contactos(fecha_creacion DESC);
            """)
            
            conn.commit()
            logger.info("✅ Tabla 'contactos' creada exitosamente")
        
        cursor.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error inicializando base de datos: {str(e)}")
        traceback.print_exc()
        return False
        
    finally:
        conn.close()

# ============================================================================
# MIDDLEWARE Y FUNCIONES AUXILIARES
# ============================================================================

def verify_admin_token():
    """Verificar token de administrador desde query params o headers"""
    token = request.args.get('token', '')
    
    # También verificar en headers por si acaso
    if not token and 'Authorization' in request.headers:
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
    
    if token != ADMIN_TOKEN:
        logger.warning(f"Intento de acceso con token inválido: {token}")
        return False
    
    return True

def format_datetime(dt):
    """Formatear datetime para JSON"""
    if dt:
        return dt.isoformat() if hasattr(dt, 'isoformat') else str(dt)
    return ''

# ============================================================================
# RUTAS PRINCIPALES Y ARCHIVOS ESTÁTICOS
# ============================================================================

@app.route('/')
def serve_index():
    """Servir el frontend principal"""
    try:
        return send_from_directory('.', 'index.html')
    except Exception as e:
        logger.error(f"Error sirviendo index.html: {str(e)}")
        return """
        <html>
        <head><title>Panel Administrativo</title></head>
        <body style="font-family: Arial; padding: 20px;">
            <h1>Panel Administrativo Danteproiedades</h1>
            <p>El sistema se está iniciando...</p>
            <p><a href="/health">Ver estado del sistema</a></p>
        </body>
        </html>
        """

@app.route('/<path:filename>')
def serve_static_files(filename):
    """Servir archivos estáticos (CSS, JS, imágenes)"""
    try:
        return send_from_directory('.', filename)
    except:
        return jsonify({'error': 'Archivo no encontrado'}), 404

# ============================================================================
# ENDPOINTS DE API - ADMINISTRACIÓN
# ============================================================================

@app.route('/admin/data', methods=['GET'])
def get_all_contacts():
    """Obtener todos los contactos"""
    logger.info(f"📥 GET /admin/data desde {request.remote_addr}")
    
    if not verify_admin_token():
        return jsonify({'error': 'Token de administrador inválido'}), 401
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a base de datos'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Consulta optimizada
        cursor.execute("""
            SELECT 
                id, nombre, email, telefono, mensaje,
                fecha_creacion, fecha_actualizacion, estado
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
                'fecha_creacion': format_datetime(row[5]),
                'fecha_actualizacion': format_datetime(row[6]),
                'estado': row[7] or 'activo'
            })
        
        cursor.close()
        
        logger.info(f"✅ Datos obtenidos: {len(contacts)} contactos")
        
        return jsonify({
            'success': True,
            'data': contacts,
            'count': len(contacts),
            'timestamp': datetime.now().isoformat(),
            'message': f'Se encontraron {len(contacts)} contactos'
        })
        
    except Exception as e:
        logger.error(f"❌ Error en /admin/data: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'details': str(e)
        }), 500
        
    finally:
        conn.close()

@app.route('/admin/add', methods=['POST'])
def add_contact():
    """Agregar nuevo contacto"""
    logger.info(f"📤 POST /admin/add desde {request.remote_addr}")
    
    if not verify_admin_token():
        return jsonify({'error': 'Token de administrador inválido'}), 401
    
    # Obtener datos del request
    try:
        data = request.get_json(force=True, silent=False)
        logger.info(f"Datos recibidos: {data}")
    except Exception as e:
        logger.error(f"❌ Error parseando JSON: {str(e)}")
        return jsonify({'error': 'Formato de datos inválido'}), 400
    
    if not data:
        return jsonify({'error': 'No se recibieron datos'}), 400
    
    # Validar campos requeridos
    nombre = data.get('nombre', '').strip()
    email = data.get('email', '').strip().lower()
    
    if not nombre:
        return jsonify({'error': 'El nombre es requerido'}), 400
    if not email:
        return jsonify({'error': 'El email es requerido'}), 400
    
    # Validar formato de email básico
    if '@' not in email or '.' not in email.split('@')[-1]:
        return jsonify({'error': 'Formato de email inválido'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a base de datos'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Verificar si el email ya existe
        cursor.execute("SELECT id FROM contactos WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({'error': 'Ya existe un contacto con este email'}), 400
        
        # Insertar nuevo contacto
        current_time = datetime.now()
        cursor.execute("""
            INSERT INTO contactos (
                nombre, email, telefono, mensaje,
                ip_address, user_agent, fecha_creacion, fecha_actualizacion
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            nombre,
            email,
            data.get('telefono', ''),
            data.get('mensaje', ''),
            request.remote_addr or '0.0.0.0',
            request.headers.get('User-Agent', 'Desconocido'),
            current_time,
            current_time
        ))
        
        new_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        
        logger.info(f"✅ Contacto agregado: ID {new_id}, Email: {email}")
        
        return jsonify({
            'success': True,
            'message': 'Contacto agregado exitosamente',
            'id': new_id,
            'email': email,
            'nombre': nombre,
            'timestamp': current_time.isoformat()
        })
        
    except psycopg2.IntegrityError as e:
        conn.rollback()
        if 'unique constraint' in str(e).lower():
            return jsonify({'error': 'El email ya está registrado'}), 400
        return jsonify({'error': 'Error de integridad en base de datos'}), 500
        
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Error en /admin/add: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': 'Error interno del servidor',
            'details': str(e)
        }), 500
        
    finally:
        conn.close()

@app.route('/admin/update', methods=['PUT'])
def update_contact():
    """Actualizar contacto existente"""
    if not verify_admin_token():
        return jsonify({'error': 'Token inválido'}), 401
    
    try:
        data = request.get_json()
    except:
        return jsonify({'error': 'Datos inválidos'}), 400
    
    email = data.get('email', '').strip().lower()
    if not email:
        return jsonify({'error': 'Email es requerido'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a base de datos'}), 500
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE contactos 
            SET nombre = %s, telefono = %s, mensaje = %s, 
                fecha_actualizacion = %s
            WHERE email = %s
            RETURNING id
        """, (
            data.get('nombre', ''),
            data.get('telefono', ''),
            data.get('mensaje', ''),
            datetime.now(),
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
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/admin/delete', methods=['DELETE'])
def delete_contact():
    """Eliminar contacto por email"""
    if not verify_admin_token():
        return jsonify({'error': 'Token inválido'}), 401
    
    try:
        data = request.get_json()
    except:
        return jsonify({'error': 'Datos inválidos'}), 400
    
    email = data.get('email', '').strip().lower()
    if not email:
        return jsonify({'error': 'Email es requerido'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a base de datos'}), 500
    
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
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/admin/clear', methods=['DELETE'])
def clear_all_contacts():
    """Eliminar todos los contactos (ADMIN ONLY)"""
    if not verify_admin_token():
        return jsonify({'error': 'Token inválido'}), 401
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a base de datos'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Contar antes de eliminar
        cursor.execute("SELECT COUNT(*) FROM contactos")
        count = cursor.fetchone()[0]
        
        if count == 0:
            return jsonify({'error': 'No hay contactos para eliminar'}), 404
        
        # Eliminar todos
        cursor.execute("DELETE FROM contactos")
        conn.commit()
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': f'Todos los contactos eliminados ({count} contactos)'
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# ============================================================================
# ENDPOINTS DE DIAGNÓSTICO Y MONITOREO
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check completo del sistema"""
    conn = get_db_connection()
    
    health_data = {
        'status': 'healthy',
        'service': 'Dante Propiedades Admin Panel',
        'version': '2.0.0',
        'timestamp': datetime.now().isoformat(),
        'environment': os.environ.get('FLASK_ENV', 'production'),
        'components': {}
    }
    
    # Verificar PostgreSQL
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT version(), NOW()")
            db_info = cursor.fetchone()
            cursor.close()
            conn.close()
            
            health_data['components']['postgresql'] = {
                'status': 'connected',
                'version': db_info[0].split(',')[0],
                'server_time': db_info[1].isoformat()
            }
            
        except Exception as e:
            health_data['components']['postgresql'] = {
                'status': 'error',
                'error': str(e)
            }
            health_data['status'] = 'degraded'
    else:
        health_data['components']['postgresql'] = {
            'status': 'disconnected',
            'error': 'No se pudo conectar'
        }
        health_data['status'] = 'degraded'
    
    # Verificar variables críticas
    health_data['components']['environment'] = {
        'admin_token_configured': bool(ADMIN_TOKEN),
        'database_url_configured': bool(DATABASE_URL),
        'port': PORT
    }
    
    return jsonify(health_data)

@app.route('/api/status', methods=['GET'])
def api_status():
    """Estado simple del API"""
    return jsonify({
        'api': 'Sistema Administrativo Dantepropiedades',
        'status': 'active',
        'version': '2.0.0',
        'timestamp': datetime.now().isoformat(),
        'endpoints': {
            'health': '/health',
            'admin_data': '/admin/data?token=TOKEN',
            'admin_add': '/admin/add?token=TOKEN',
            'admin_update': '/admin/update?token=TOKEN',
            'admin_delete': '/admin/delete?token=TOKEN'
        }
    })

@app.route('/debug/connection', methods=['GET'])
def debug_connection():
    """Debug detallado de la conexión a PostgreSQL"""
    if not DATABASE_URL:
        return jsonify({
            'connected': False,
            'error': 'DATABASE_URL no configurada',
            'hint': 'Configura la variable en Render Environment'
        })
    
    conn = get_db_connection()
    if not conn:
        return jsonify({
            'connected': False,
            'error': 'No se pudo conectar a PostgreSQL',
            'database_url_preview': DATABASE_URL[:100] + '...',
            'hint': 'Verifica: 1) URL correcta, 2) BD activa en Render, 3) Credenciales'
        })
    
    try:
        cursor = conn.cursor()
        
        # Obtener información del servidor
        cursor.execute("""
            SELECT 
                version(),
                current_database(),
                current_user,
                inet_server_addr(),
                inet_server_port(),
                NOW()
        """)
        
        info = cursor.fetchone()
        
        # Obtener información de la tabla
        cursor.execute("""
            SELECT 
                COUNT(*) as total_contactos,
                MIN(fecha_creacion) as mas_antiguo,
                MAX(fecha_creacion) as mas_reciente
            FROM contactos
        """)
        
        table_info = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'connected': True,
            'postgresql_version': info[0],
            'database': info[1],
            'user': info[2],
            'server_address': info[3],
            'server_port': info[4],
            'server_time': info[5].isoformat(),
            'table_info': {
                'total_contactos': table_info[0],
                'contacto_mas_antiguo': format_datetime(table_info[1]),
                'contacto_mas_reciente': format_datetime(table_info[2])
            },
            'message': '✅ Conexión PostgreSQL funcionando correctamente'
        })
        
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({
            'connected': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })

# ============================================================================
# MANEJO DE ERRORES GLOBAL
# ============================================================================

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({
        'error': 'Endpoint no encontrado',
        'path': request.path,
        'method': request.method,
        'available_endpoints': [
            '/health',
            '/api/status',
            '/admin/data?token=TOKEN',
            '/admin/add?token=TOKEN',
            '/debug/connection'
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"❌ Error 500: {str(error)}")
    return jsonify({
        'error': 'Error interno del servidor',
        'message': 'Ha ocurrido un error inesperado',
        'timestamp': datetime.now().isoformat()
    }), 500

@app.errorhandler(Exception)
def handle_exception(error):
    logger.error(f"❌ Excepción no manejada: {str(error)}")
    traceback.print_exc()
    return jsonify({
        'error': 'Error del servidor',
        'message': str(error),
        'type': error.__class__.__name__
    }), 500

# ============================================================================
# INICIALIZACIÓN Y EJECUCIÓN
# ============================================================================

def initialize_application():
    """Inicializar toda la aplicación"""
    print("\n" + "=" * 70)
    print("🔧 INICIALIZANDO APLICACIÓN...")
    print("=" * 70)
    
    # Inicializar base de datos
    print("\n🗄️  Inicializando base de datos PostgreSQL...")
    if DATABASE_URL:
        if init_database():
            print("✅ Base de datos inicializada correctamente")
        else:
            print("❌ Error inicializando base de datos")
            print("💡 Verifica:")
            print("   1. DATABASE_URL correcta en Render")
            print("   2. Base de datos activa en Render")
            print("   3. Credenciales correctas")
            print("\n⚠️  La aplicación se iniciará en modo degradado")
    else:
        print("❌ DATABASE_URL no configurada - Modo sin base de datos")
    
    print("\n✅ Aplicación inicializada")
    print(f"🌐 Servidor listo en puerto {PORT}")
    print(f"📅 Hora del sistema: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    return True

# ============================================================================
# PUNTO DE ENTRADA PRINCIPAL
# ============================================================================

if __name__ == '__main__':
    # Inicializar aplicación
    initialize_application()
    
    # Iniciar servidor Flask
    print(f"\n🚀 Iniciando servidor Flask en http://0.0.0.0:{PORT}")
    print("💡 Endpoints disponibles:")
    print(f"   • Health check: http://0.0.0.0:{PORT}/health")
    print(f"   • API Status: http://0.0.0.0:{PORT}/api/status")
    print(f"   • Debug: http://0.0.0.0:{PORT}/debug/connection")
    print(f"   • Frontend: http://0.0.0.0:{PORT}/")
    print("\n📝 Presiona Ctrl+C para detener el servidor")
    print("=" * 70)
    
    # Ejecutar servidor
    app.run(
        host='0.0.0.0',
        port=PORT,
        debug=False,
        threaded=True
    )