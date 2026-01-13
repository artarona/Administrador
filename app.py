#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sistema Administrativo Dantepropiedades - Solución Final Fechas
Backend Flask con PostgreSQL y manejo robusto de fechas
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
print(f"🔐 ADMIN_TOKEN: ✅ {ADMIN_TOKEN}")
print(f"🔐 DATABASE_URL: ✅ {'Configurada' if DATABASE_URL else 'NO configurada'}")
print(f"🔐 FLASK_ENV: ✅ {FLASK_ENV}")

# Variables de entorno del sistema
if 'PORT' in os.environ:
    port = int(os.environ['PORT'])
    print(f"🔐 PORT: {port}")
else:
    port = 5000
    print(f"🔐 PORT: {port} (default)")

if DATABASE_URL:
    # Ocultar credenciales en logs
    db_safe = DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else '***'
    print(f"✅ DATABASE_URL desde variables de entorno: OK")
    print(f"🔐 DATABASE_URL (segura): postgresql:***@{db_safe}")
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
            print(f"🔐 DATABASE_URL (.env, segura): postgresql:***@{db_safe}")
        else:
            print("❌ DATABASE_URL tampoco en archivo .env")
    except ImportError:
        print("❌ python-dotenv no instalado")

print("=" * 50)

# Inicializar Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dantepropiedades-secret-key-2024'

# 🔒 CONFIGURACIÓN CORS PARA GITHUB PAGES Y RENDER
CORS(app, origins=[
    "https://artarona.github.io",     # GitHub Pages del frontend
    "https://administrador-63nc.onrender.com",  # Backend actual
    "http://localhost:3000",          # Desarrollo local
    "http://localhost:5000",          # Desarrollo local alternativo
    "null",                          # Permitir null para desarrollo
    "*"                              # Permitir todos en desarrollo
])

# 🗄️ VARIABLES GLOBALES PARA BASE DE DATOS
db_connection = None
db_cursor = None

def formatear_fecha(fecha_valor):
    """Formatear fecha que puede ser string o datetime object"""
    if not fecha_valor:
        return ''
    
    # Si ya es un string, devolverlo
    if isinstance(fecha_valor, str):
        return fecha_valor
    
    # Si es datetime, convertir a ISO format
    if hasattr(fecha_valor, 'isoformat'):
        return fecha_valor.isoformat()
    
    # Convertir cualquier otro tipo a string
    return str(fecha_valor)

def conectar_postgresql():
    """Conectar a PostgreSQL con manejo de errores"""
    global db_connection, db_cursor
    
    try:
        if not DATABASE_URL:
            raise Exception("DATABASE_URL no configurada")
        
        print("🗄️ Intentando conectar a PostgreSQL...")
        db_connection = psycopg2.connect(DATABASE_URL)
        db_cursor = db_connection.cursor()
        
        print("✅ Conexión a PostgreSQL exitosa")
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
        
        # ✅ SELECT explícito con columnas en orden correcto
        db_cursor.execute("""
            SELECT id, nombre, email, telefono, mensaje, 
                   fecha_creacion, fecha_actualizacion
            FROM contactos 
            ORDER BY fecha_creacion DESC
        """)
        resultados = db_cursor.fetchall()
        
        contactos = []
        for fila in resultados:
            # Manejar cada campo de forma segura con índices correctos
            try:
                contacto = {
                    'id': fila[0] if len(fila) > 0 and fila[0] else 0,
                    'nombre': fila[1] if len(fila) > 1 and fila[1] else '',
                    'email': fila[2] if len(fila) > 2 and fila[2] else '',
                    'telefono': fila[3] if len(fila) > 3 and fila[3] else '',
                    'mensaje': fila[4] if len(fila) > 4 and fila[4] else '',
                    'fecha_creacion': formatear_fecha(fila[5]) if len(fila) > 5 else '',
                    'fecha_actualizacion': formatear_fecha(fila[6]) if len(fila) > 6 else ''
                }
                contactos.append(contacto)
            except Exception as row_error:
                print(f"⚠️ Error procesando fila: {str(row_error)}")
                # Continuar con la siguiente fila
                continue
        
        print(f"📊 Datos obtenidos: {len(contactos)} contactos")
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

# API PUBLICA - FORMULARIO DE CONTACTO
@app.route('/api/contacto', methods=['POST'])
def contacto_publico():
    """Endpoint publico para formulario de contacto (sin autenticacion)"""
    logger.info("=" * 60)
    logger.info("[REQUEST] /api/contacto recibido (formulario publico)")
    logger.info(f"Content-Type: {request.content_type}")
    logger.info(f"Origin: {request.headers.get('Origin', 'Unknown')}")
    
    try:
        # Obtener datos JSON
        datos = None
        try:
            datos = request.get_json(force=True, silent=False)
            logger.info(f"[DATA] Datos del formulario: {datos}")
        except Exception as json_error:
            logger.error(f"[ERROR] Error parseando JSON: {str(json_error)}")
            return jsonify({'error': 'Datos invalidos'}), 400
        
        # Validaciones basicas
        if not datos:
            logger.error("[ERROR] No se recibieron datos")
            return jsonify({'error': 'No se recibieron datos'}), 400
            
        if not datos.get('nombre') or not datos.get('email') or not datos.get('mensaje'):
            logger.error(f"[VALIDATION] Campos obligatorios faltantes")
            return jsonify({'error': 'Nombre, email y mensaje son obligatorios'}), 400
        
        # Verificar conexion a DB
        if not db_connection:
            if not conectar_postgresql():
                return jsonify({'error': 'Error de conexion a base de datos'}), 500
        
        # Construir mensaje completo con campos adicionales del formulario
        mensaje_completo = datos.get('mensaje', '')
        
        # Agregar interes si existe
        if datos.get('interes'):
            interes_map = {
                'compra': 'Comprar propiedad',
                'venta': 'Vender propiedad',
                'alquiler': 'Alquilar propiedad',
                'consulta': 'Consulta general'
            }
            interes_texto = interes_map.get(datos['interes'], datos['interes'])
            mensaje_completo = f"[Interes: {interes_texto}]\n{mensaje_completo}"
        
        # Agregar presupuesto si existe
        if datos.get('presupuesto'):
            presupuesto_map = {
                'hasta-100k': 'Hasta $100.000 USD',
                '100k-200k': '$100.000 - $200.000 USD',
                '200k-300k': '$200.000 - $300.000 USD',
                '300k-500k': '$300.000 - $500.000 USD',
                'mas-500k': 'Mas de $500.000 USD'
            }
            presupuesto_texto = presupuesto_map.get(datos['presupuesto'], datos['presupuesto'])
            mensaje_completo = f"[Presupuesto: {presupuesto_texto}]\n{mensaje_completo}"
        
        # Insertar en base de datos
        current_timestamp = datetime.now()
        
        try:
            db_cursor.execute('''
                INSERT INTO contactos (
                    nombre, email, telefono, mensaje, estado, 
                    ip_address, user_agent, timestamp, fecha_creacion, fecha_actualizacion
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                datos['nombre'],
                datos['email'],
                datos.get('telefono', ''),
                mensaje_completo,
                'pendiente',  # Estado inicial para contactos del formulario publico
                request.headers.get('X-Forwarded-For', request.remote_addr) or '0.0.0.0',
                request.headers.get('User-Agent', 'Formulario Web'),
                current_timestamp,
                current_timestamp,
                current_timestamp
            ))
        except Exception as e:
            logger.error(f"[ERROR] Error en insercion: {str(e)}")
            logger.error(traceback.format_exc())
            if db_connection:
                db_connection.rollback()
            return jsonify({
                'error': 'Error insertando en base de datos',
                'details': str(e)
            }), 500
        
        contacto_id = db_cursor.fetchone()[0]
        db_connection.commit()
        
        logger.info(f"[SUCCESS] Contacto publico guardado: {datos['nombre']} ({datos['email']}) - ID: {contacto_id}")
        logger.info("=" * 60)
        
        return jsonify({
            'success': True,
            'message': 'Contacto guardado exitosamente',
            'id': contacto_id,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"[ERROR] Error general en /api/contacto: {str(e)}")
        logger.error(traceback.format_exc())
        logger.info("=" * 60)
        if db_connection:
            db_connection.rollback()
        return jsonify({
            'error': 'Error interno del servidor',
            'details': str(e)
        }), 500

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
def admin_add_contact():  # NOMBRE ÚNICO, NO DUPLICADO
    """Agregar nuevo contacto desde panel admin"""
    logger.info("=" * 60)
    logger.info("[REQUEST] /admin/add recibido desde panel admin")
    
    # Verificar token
    token = request.args.get('token', '')
    if token != ADMIN_TOKEN:
        logger.error(f"[ERROR] Token inválido. Recibido: '{token}'")
        return jsonify({'error': 'Token de administrador inválido'}), 401
    
    try:
        # Obtener datos JSON
        datos = None
        try:
            datos = request.get_json(force=True, silent=True)
            logger.info(f"[DATA] Datos recibidos: {datos}")
        except Exception as json_error:
            logger.error(f"[ERROR] Error parseando JSON: {str(json_error)}")
            return jsonify({'error': 'Formato de datos inválido'}), 400
        
        # Validaciones básicas
        if not datos:
            logger.error("[ERROR] No se recibieron datos")
            return jsonify({'error': 'No se recibieron datos'}), 400
            
        if not datos.get('nombre') or not datos.get('email'):
            logger.error(f"[VALIDATION] Campos requeridos faltantes")
            return jsonify({'error': 'Nombre y email son requeridos'}), 400
        
        # Verificar conexión a DB
        if not db_connection or db_connection.closed:
            logger.info("[INFO] Reconectando a la base de datos...")
            if not conectar_postgresql():
                return jsonify({'error': 'Error de conexión a base de datos'}), 500
        
        # Verificar si el email ya existe
        try:
            db_cursor.execute("SELECT id FROM contactos WHERE email = %s", (datos['email'],))
            if db_cursor.fetchone():
                logger.warning(f"[WARNING] Email duplicado: {datos['email']}")
                return jsonify({'error': 'Ya existe un contacto con este email'}), 400
        except Exception as e:
            logger.error(f"[WARNING] Error verificando email: {str(e)}")
            # Continuar, no es crítico
        
        # Insertar nuevo contacto
        current_timestamp = datetime.now()
        
        try:
            db_cursor.execute('''
                INSERT INTO contactos (
                    nombre, email, telefono, mensaje, estado, 
                    ip_address, user_agent, timestamp, fecha_creacion, fecha_actualizacion
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
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
        except Exception as e:
            logger.error(f"[ERROR] Error en inserción SQL: {str(e)}")
            logger.error(traceback.format_exc())
            if db_connection:
                db_connection.rollback()
            return jsonify({
                'error': 'Error en base de datos',
                'details': str(e)
            }), 500
        
        contacto_id = db_cursor.fetchone()[0]
        db_connection.commit()
        
        logger.info(f"[SUCCESS] Contacto agregado: ID {contacto_id}")
        logger.info("=" * 60)
        
        return jsonify({
            'success': True,
            'message': 'Contacto agregado exitosamente',
            'contacto_id': contacto_id,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"[ERROR] Error general en /admin/add: {str(e)}")
        logger.error(traceback.format_exc())
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
        
        # Actualizar solo los campos editables por el usuario
        current_timestamp = datetime.now()
        
        try:
            # ✅ UPDATE simplificado - solo campos editables
            db_cursor.execute('''
                UPDATE contactos 
                SET nombre = %s, telefono = %s, mensaje = %s, fecha_actualizacion = %s
                WHERE email = %s
            ''', (
                datos.get('nombre', ''),
                datos.get('telefono', ''),
                datos.get('mensaje', ''),
                current_timestamp,
                datos['email']
            ))
        except Exception as e:
            print(f"❌ Error en actualización: {str(e)}")
            traceback.print_exc()
            if db_connection:
                db_connection.rollback()
            return jsonify({
                'error': 'Error actualizando en base de datos',
                'details': str(e)
            }), 500
        
        if db_cursor.rowcount == 0:
            return jsonify({'error': 'Contacto no encontrado'}), 404
        
        db_connection.commit()
        
        print(f"✅ Contacto actualizado: {datos.get('nombre')} ({datos['email']})")
        
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

# 🩺 RUTAS DE SALUD Y ESTADO
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
        'version': '2.4.0',
        'status': 'active',
        'database': 'PostgreSQL',
        'frontend': 'GitHub Pages + Backend Render',
        'cors': 'enabled',
        'bd_compatibility': 'robust_date_handling',
        'timestamp': datetime.now().isoformat()
    })

# 🚀 INICIALIZACIÓN DE LA APLICACIÓN
def init_app():
    """Inicializar la aplicación"""
    try:
        print("🚀 Iniciando Sistema Administrativo Dantepropiedades...")
        print(f"🌍 Entorno: {FLASK_ENV}")
        print(f"🔑 Token de administrador: {ADMIN_TOKEN}")
        print(f"📅 Fechas: Manejo robusto de strings y datetime")
        
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