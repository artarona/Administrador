#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sistema Administrativo Dantepropiedades - SoluciÃ³n Final Fechas
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

# ConfiguraciÃ³n de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ConfiguraciÃ³n inicial
ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN', '2205')
FLASK_ENV = os.environ.get('FLASK_ENV', 'production')
DATABASE_URL = os.environ.get('DATABASE_URL')

print("RENDER: ðŸ” DIAGNÃ“STICO DE VARIABLES DE ENTORNO")
print("=" * 50)
print(f"ðŸ”§ ADMIN_TOKEN: âœ… {ADMIN_TOKEN}")
print(f"ðŸ”§ DATABASE_URL: âœ… {'Configurada' if DATABASE_URL else 'NO configurada'}")
print(f"ðŸ”§ FLASK_ENV: âœ… {FLASK_ENV}")

# Variables de entorno del sistema
if 'PORT' in os.environ:
    port = int(os.environ['PORT'])
    print(f"ðŸ”§ PORT: {port}")
else:
    port = 5000
    print(f"ðŸ”§ PORT: {port} (default)")

if DATABASE_URL:
    # Ocultar credenciales en logs
    db_safe = DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else '***'
    print(f"âœ… DATABASE_URL desde variables de entorno: OK")
    print(f"ðŸ”§ DATABASE_URL (segura): postgresql:***@{db_safe}")
else:
    print("âŒ DATABASE_URL no encontrada en variables de entorno")
    # Intentar leer desde archivo .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
        DATABASE_URL = os.environ.get('DATABASE_URL')
        if DATABASE_URL:
            db_safe = DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else '***'
            print(f"âœ… DATABASE_URL desde archivo .env: OK")
            print(f"ðŸ”§ DATABASE_URL (.env, segura): postgresql:***@{db_safe}")
        else:
            print("âŒ DATABASE_URL tampoco en archivo .env")
    except ImportError:
        print("âŒ python-dotenv no instalado")

print("=" * 50)

# Inicializar Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dantepropiedades-secret-key-2024'

# ðŸ”§ CONFIGURACIÃ“N CORS PARA GITHUB PAGES Y RENDER
CORS(app, origins=[
    "https://artarona.github.io",     # GitHub Pages del frontend
    "https://administrador-63nc.onrender.com",  # Backend actual
    "http://localhost:3000",          # Desarrollo local
    "http://localhost:5000",          # Desarrollo local alternativo
    "null",                          # Permitir null para desarrollo
    "*"                              # Permitir todos en desarrollo
])

# ðŸ”— VARIABLES GLOBALES PARA BASE DE DATOS
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
        
        print("ðŸ”— Intentando conectar a PostgreSQL...")
        db_connection = psycopg2.connect(DATABASE_URL)
        db_cursor = db_connection.cursor()
        
        print("âœ… ConexiÃ³n a PostgreSQL exitosa")
        print("âœ… Sistema de almacenamiento PostgreSQL inicializado")
        
        return True
        
    except Exception as e:
        print(f"âŒ Error conectando a PostgreSQL: {str(e)}")
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
                print(f"âš ï¸ Error procesando fila: {str(row_error)}")
                # Continuar con la siguiente fila
                continue
        
        print(f"ðŸ“Š Datos obtenidos: {len(contactos)} contactos")
        return contactos
        
    except Exception as e:
        print(f"âŒ Error obteniendo datos: {str(e)}")
        traceback.print_exc()
        return []

def verificar_token():
    """Verificar token de administrador"""
    token = request.args.get('token', '') or request.headers.get('Authorization', '').replace('Bearer ', '')
    return token == ADMIN_TOKEN

# ðŸ  RUTA PRINCIPAL - SERVE FRONTEND
@app.route('/')
def index():
    """Servir el archivo index.html desde la raÃ­z"""
    try:
        return send_from_directory('.', 'index.html')
    except Exception as e:
        return f"Error cargando frontend: {str(e)}", 500

@app.route('/<path:filename>')
def serve_static(filename):
    """Servir archivos estÃ¡ticos"""
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


# ðŸ” RUTAS DE ADMINISTRACIÃ“N - PROTEGIDAS POR TOKEN
@app.route('/admin/data', methods=['GET'])
def admin_data():
    """Obtener todos los contactos"""
    if not verificar_token():
        return jsonify({'error': 'Token de administrador invÃ¡lido'}), 401
    
    try:
        contactos = obtener_datos()
        return jsonify({
            'success': True,
            'data': contactos,
            'count': len(contactos),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"âŒ Error en /admin/data: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': 'Error interno del servidor',
            'details': str(e)
        }), 500

@app.route('/admin/add', methods=['POST'])
def admin_add():
    """Agregar nuevo contacto"""
    # Log del request completo
    logger.info("=" * 60)
    logger.info("[REQUEST] /admin/add recibido")
    logger.info(f"Content-Type: {request.content_type}")
    logger.info(f"Content-Length: {request.content_length}")
    
    if not verificar_token():
        logger.error("[ERROR] Token invalido en /admin/add")
        return jsonify({'error': 'Token de administrador invalido'}), 401
    
    try:
        # Intentar obtener datos JSON
        datos = None
        try:
            datos = request.get_json(force=True, silent=False)
            logger.info(f"[DATA] Datos JSON parseados: {datos}")
        except Exception as json_error:
            logger.error(f"[ERROR] Error parseando JSON: {str(json_error)}")
            # Intentar obtener el raw body
            try:
                raw_body = request.get_data(as_text=True)
                logger.error(f"[RAW] Raw request body: {raw_body[:500]}")
            except:
                pass
        
        # Validaciones basicas
        if not datos:
            logger.error("[ERROR] No se recibieron datos JSON validos")
            return jsonify({
                'error': 'No se recibieron datos validos'
            }), 400
            
        if not datos.get('nombre') or not datos.get('email'):
            logger.error(f"[VALIDATION] Validacion fallida - nombre: '{datos.get('nombre')}', email: '{datos.get('email')}'")
            logger.error(f"[VALIDATION] Datos completos recibidos: {datos}")
            return jsonify({
                'error': 'Nombre y email son requeridos'
            }), 400
        
        # Verificar conexiÃ³n a DB
        if not db_connection:
            if not conectar_postgresql():
                return jsonify({'error': 'Error de conexiÃ³n a base de datos'}), 500
        
        # Verificar si el email ya existe
        try:
            db_cursor.execute("SELECT id FROM contactos WHERE email = %s", (datos['email'],))
            if db_cursor.fetchone():
                logger.warning(f"[WARNING] Email duplicado: {datos['email']}")
                return jsonify({'error': 'Ya existe un contacto con este email'}), 400
        except Exception as e:
            logger.error(f"[WARNING] Error verificando email existente: {str(e)}")
        
        # Insertar nuevo contacto con TODAS las columnas necesarias
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
                'activo',  # estado
                request.headers.get('X-Forwarded-For', request.remote_addr) or '0.0.0.0',  # ip_address
                request.headers.get('User-Agent', 'Unknown'),  # user_agent
                current_timestamp,  # timestamp (NOT NULL)
                current_timestamp,  # fecha_creacion
                current_timestamp   # fecha_actualizacion
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
        
        logger.info(f"[SUCCESS] Contacto agregado exitosamente: {datos['nombre']} ({datos['email']})")
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
        logger.info("=" * 60)
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
        return jsonify({'error': 'Token de administrador invÃ¡lido'}), 401
    
    try:
        datos = request.get_json()
        
        if not datos.get('email'):
            return jsonify({'error': 'Email es requerido para actualizar'}), 400
        
        if not db_connection:
            if not conectar_postgresql():
                return jsonify({'error': 'Error de conexiÃ³n a base de datos'}), 500
        
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
            print(f"❌ Error en actualizaciÃ³n: {str(e)}")
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
        return jsonify({'error': 'Token de administrador invÃ¡lido'}), 401
    
    try:
        datos = request.get_json()
        
        if not datos.get('email'):
            return jsonify({'error': 'Email es requerido para eliminar'}), 400
        
        if not db_connection:
            if not conectar_postgresql():
                return jsonify({'error': 'Error de conexiÃ³n a base de datos'}), 500
        
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
        print(f"âŒ Error en /admin/delete: {str(e)}")
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
        return jsonify({'error': 'Token de administrador invÃ¡lido'}), 401
    
    try:
        if not db_connection:
            if not conectar_postgresql():
                return jsonify({'error': 'Error de conexiÃ³n a base de datos'}), 500
        
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
        print(f"âŒ Error en /admin/clear: {str(e)}")
        traceback.print_exc()
        if db_connection:
            db_connection.rollback()
        return jsonify({
            'error': 'Error interno del servidor',
            'details': str(e)
        }), 500

# ðŸ” RUTAS DE SALUD Y ESTADO
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

# ðŸš€ INICIALIZACIÃ“N DE LA APLICACIÃ“N
def init_app():
    """Inicializar la aplicaciÃ³n"""
    try:
        print("ðŸš€ Iniciando Sistema Administrativo Dantepropiedades...")
        print(f"ðŸŒ Entorno: {FLASK_ENV}")
        print(f"ðŸ”‘ Token de administrador: {ADMIN_TOKEN}")
        print(f"ðŸ”§ Fechas: Manejo robusto de strings y datetime")
        
        # Conectar a base de datos
        if not conectar_postgresql():
            print("âš ï¸ Advertencia: No se pudo conectar a la base de datos inicialmente")
        
        print("âœ… AplicaciÃ³n inicializada correctamente")
        return True
        
    except Exception as e:
        print(f"âŒ Error inicializando aplicaciÃ³n: {str(e)}")
        traceback.print_exc()
        return False

# ðŸŽ¯ MAIN
if __name__ == '__main__':
    if init_app():
        print(f"ðŸŽ¯ Iniciando servidor en puerto {port}...")
        app.run(host='0.0.0.0', port=port, debug=(FLASK_ENV != 'production'))
    else:
        print("âŒ No se pudo inicializar la aplicaciÃ³n")
        exit(1)
