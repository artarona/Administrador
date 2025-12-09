# -*- coding: utf-8 -*-
"""
🚀 SISTEMA DE ALMACENAMIENTO POSTGRESQL - BACKEND RENDER
================================================================

Versión optimizada para Render.com con PostgreSQL
Almacenamiento robusto y escalable en la nube
"""

import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime
import logging
import time

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

app = Flask(__name__)

# Configuración CORS para dominio personalizado
CORS(app, origins=[
    "https://dantepropiedades.com.ar",
    "https://danterealestate.github.io",
    "http://localhost:3000",
    "http://localhost:8000"
])

# Configuración desde variables de entorno
ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN', '2205')
DATABASE_URL = os.environ.get('DATABASE_URL')

class PostgreSQLStorageManager:
    """
    📊 Gestor de almacenamiento en PostgreSQL
    Compatible con Render.com y bases de datos en la nube
    """
    
    def __init__(self):
        self.init_database()
    
    def get_connection(self):
        """Obtener conexión a PostgreSQL"""
        try:
            conn = psycopg2.connect(DATABASE_URL)
            return conn
        except Exception as e:
            logging.error(f"Error conectando a PostgreSQL: {e}")
            raise
    
    def init_database(self):
        """Inicializar tabla de contactos"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Crear tabla si no existe
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contactos (
                    id SERIAL PRIMARY KEY,
                    timestamp VARCHAR(255) UNIQUE NOT NULL,
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
            
            # Crear índices para mejorar rendimiento
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_contactos_timestamp 
                ON contactos(timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_contactos_fecha 
                ON contactos(fecha_creacion)
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            logging.info("✅ Base de datos PostgreSQL inicializada correctamente")
            
        except Exception as e:
            logging.error(f"❌ Error inicializando base de datos: {e}")
            raise
    
    def guardar_contacto(self, datos):
        """Guardar nuevo contacto"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO contactos (
                    timestamp, nombre, email, telefono, estado, notas, 
                    ip_address, user_agent, fecha_creacion, fecha_actualizacion
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (timestamp) DO UPDATE SET
                    nombre = EXCLUDED.nombre,
                    email = EXCLUDED.email,
                    telefono = EXCLUDED.telefono,
                    estado = EXCLUDED.estado,
                    notas = EXCLUDED.notas,
                    fecha_actualizacion = CURRENT_TIMESTAMP
            """, (
                datos.get('timestamp'),
                datos.get('nombre'),
                datos.get('email'),
                datos.get('telefono'),
                datos.get('estado', 'nuevo'),
                datos.get('notas'),
                datos.get('ip_address'),
                datos.get('user_agent'),
                datetime.now(),
                datetime.now()
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logging.info(f"✅ Contacto guardado: {datos.get('nombre', 'Sin nombre')}")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error guardando contacto: {e}")
            return False
    
    def obtener_todos_contactos(self):
        """Obtener todos los contactos"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT id, timestamp, nombre, email, telefono, estado, notas,
                       ip_address, user_agent, fecha_creacion, fecha_actualizacion
                FROM contactos 
                ORDER BY fecha_creacion DESC
            """)
            
            contactos = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            # Convertir a lista de diccionarios para JSON
            return [dict(contacto) for contacto in contactos]
            
        except Exception as e:
            logging.error(f"❌ Error obteniendo contactos: {e}")
            return []
    
    def obtener_contacto_por_id(self, timestamp):
        """Obtener contacto específico por timestamp"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT * FROM contactos WHERE timestamp = %s
            """, (timestamp,))
            
            contacto = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            return dict(contacto) if contacto else None
            
        except Exception as e:
            logging.error(f"❌ Error obteniendo contacto: {e}")
            return None
    
    def actualizar_contacto(self, timestamp, datos_actualizados):
        """Actualizar contacto existente"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            campos_actualizar = []
            valores = []
            
            for campo in ['nombre', 'email', 'telefono', 'estado', 'notas']:
                if campo in datos_actualizados:
                    campos_actualizar.append(f"{campo} = %s")
                    valores.append(datos_actualizados[campo])
            
            if campos_actualizar:
                valores.append(datetime.now())
                valores.append(timestamp)
                
                query = f"""
                    UPDATE contactos 
                    SET {', '.join(campos_actualizar)}, fecha_actualizacion = %s 
                    WHERE timestamp = %s
                """
                
                cursor.execute(query, valores)
                conn.commit()
            
            cursor.close()
            conn.close()
            
            logging.info(f"✅ Contacto actualizado: {timestamp}")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error actualizando contacto: {e}")
            return False
    
    def eliminar_contacto(self, timestamp):
        """Eliminar contacto"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM contactos WHERE timestamp = %s", (timestamp,))
            filas_afectadas = cursor.rowcount
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logging.info(f"✅ Contacto eliminado: {timestamp} ({filas_afectadas} filas)")
            return filas_afectadas > 0
            
        except Exception as e:
            logging.error(f"❌ Error eliminando contacto: {e}")
            return False
    
    def limpiar_todos_contactos(self):
        """Eliminar todos los contactos"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM contactos")
            total = cursor.fetchone()[0]
            
            cursor.execute("DELETE FROM contactos")
            conn.commit()
            
            cursor.close()
            conn.close()
            
            logging.info(f"✅ {total} contactos eliminados")
            return total
            
        except Exception as e:
            logging.error(f"❌ Error limpiando contactos: {e}")
            return False
    
    def obtener_estadisticas(self):
        """Obtener estadísticas de contactos"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Total de contactos
            cursor.execute("SELECT COUNT(*) as total FROM contactos")
            total = cursor.fetchone()['total']
            
            # Contactos por estado
            cursor.execute("""
                SELECT estado, COUNT(*) as cantidad 
                FROM contactos 
                GROUP BY estado 
                ORDER BY cantidad DESC
            """)
            por_estado = cursor.fetchall()
            
            # Contactos por día (últimos 30 días)
            cursor.execute("""
                SELECT DATE(fecha_creacion) as fecha, COUNT(*) as cantidad
                FROM contactos 
                WHERE fecha_creacion >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY DATE(fecha_creacion)
                ORDER BY fecha DESC
            """)
            por_dia = cursor.fetchall()
            
            # Últimos contactos
            cursor.execute("""
                SELECT nombre, email, fecha_creacion 
                FROM contactos 
                ORDER BY fecha_creacion DESC 
                LIMIT 5
            """)
            ultimos = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return {
                'total': total,
                'por_estado': [dict(row) for row in por_estado],
                'por_dia': [dict(row) for row in por_dia],
                'ultimos': [dict(row) for row in ultimos]
            }
            
        except Exception as e:
            logging.error(f"❌ Error obteniendo estadísticas: {e}")
            return {'total': 0, 'por_estado': [], 'por_dia': [], 'ultimos': []}

# Instancia del gestor de almacenamiento
storage_manager = PostgreSQLStorageManager()

# ============================================================================
# RUTAS DE LA API
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check para Render"""
    try:
        contactos = storage_manager.obtener_todos_contactos()
        return jsonify({
            'status': 'healthy',
            'message': 'Servidor funcionando correctamente',
            'total_contactos': len(contactos),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/')
def home():
    """Página principal"""
    return jsonify({
        'message': 'API de Gestión de Contactos - Dantepropiedades',
        'version': '2.0 (Render + PostgreSQL)',
        'endpoints': [
            'GET /health',
            'POST /api/guardar-contacto',
            'GET /api/obtener-consultas',
            'GET /api/resumen',
            'GET /admin/data/<token>',
            'POST /admin/add/<token>',
            'PUT /admin/update/<token>',
            'DELETE /admin/delete/<token>',
            'DELETE /admin/clear/<token>'
        ]
    })

# ============================================================================
# RUTAS PÚBLICAS DE LA API
# ============================================================================

@app.route('/api/guardar-contacto', methods=['POST'])
def guardar_contacto():
    """Guardar nuevo contacto desde formulario web"""
    try:
        datos = request.get_json()
        
        if not datos or not datos.get('nombre'):
            return jsonify({'success': False, 'error': 'Datos incompletos'}), 400
        
        # Agregar metadatos
        datos['timestamp'] = str(int(time.time() * 1000))
        datos['ip_address'] = request.remote_addr
        datos['user_agent'] = request.headers.get('User-Agent', '')
        
        # Guardar en base de datos
        if storage_manager.guardar_contacto(datos):
            logging.info(f"✅ Nuevo contacto guardado: {datos['nombre']}")
            return jsonify({
                'success': True, 
                'message': 'Contacto guardado correctamente',
                'timestamp': datos['timestamp']
            })
        else:
            return jsonify({'success': False, 'error': 'Error guardando contacto'}), 500
            
    except Exception as e:
        logging.error(f"❌ Error en guardar-contacto: {e}")
        return jsonify({'success': False, 'error': 'Error interno del servidor'}), 500

@app.route('/api/obtener-consultas', methods=['GET'])
def obtener_consultas():
    """Obtener todas las consultas"""
    try:
        contactos = storage_manager.obtener_todos_contactos()
        return jsonify({'success': True, 'data': contactos})
    except Exception as e:
        logging.error(f"❌ Error obteniendo consultas: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/resumen', methods=['GET'])
def obtener_resumen():
    """Obtener resumen de contactos"""
    try:
        stats = storage_manager.obtener_estadisticas()
        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        logging.error(f"❌ Error obteniendo resumen: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# RUTAS ADMINISTRATIVAS (PROTEGIDAS)
# ============================================================================

@app.route('/admin/data/<token>')
def obtener_datos_admin(token):
    """Obtener todos los contactos para admin"""
    if token != ADMIN_TOKEN:
        return jsonify({'error': 'Acceso no autorizado'}), 403
    
    try:
        contactos = storage_manager.obtener_todos_contactos()
        return jsonify({'success': True, 'data': contactos})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/add/<token>', methods=['POST'])
def agregar_contacto_admin(token):
    """Agregar nuevo contacto desde admin"""
    if token != ADMIN_TOKEN:
        return jsonify({'error': 'Acceso no autorizado'}), 403
    
    try:
        datos = request.get_json()
        
        if not datos or not datos.get('nombre'):
            return jsonify({'error': 'Nombre es requerido'}), 400
        
        # Agregar timestamp si no existe
        if 'timestamp' not in datos:
            datos['timestamp'] = str(int(time.time() * 1000))
        
        datos['estado'] = datos.get('estado', 'nuevo')
        
        if storage_manager.guardar_contacto(datos):
            return jsonify({'success': True, 'message': 'Contacto agregado correctamente'})
        else:
            return jsonify({'error': 'Error guardando contacto'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/update/<token>', methods=['PUT'])
def actualizar_contacto_admin(token):
    """Actualizar contacto existente desde admin"""
    if token != ADMIN_TOKEN:
        return jsonify({'error': 'Acceso no autorizado'}), 403
    
    try:
        datos = request.get_json()
        contacto_id = datos.get('timestamp')
        
        if not contacto_id:
            return jsonify({'error': 'ID de contacto requerido'}), 400
        
        if storage_manager.actualizar_contacto(contacto_id, datos):
            return jsonify({'success': True, 'message': 'Contacto actualizado correctamente'})
        else:
            return jsonify({'error': 'Error actualizando contacto'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/delete/<token>', methods=['DELETE'])
def eliminar_contacto_admin(token):
    """Eliminar contacto desde admin"""
    if token != ADMIN_TOKEN:
        return jsonify({'error': 'Acceso no autorizado'}), 403
    
    try:
        datos = request.get_json()
        contacto_id = datos.get('timestamp')
        
        if not contacto_id:
            return jsonify({'error': 'ID de contacto requerido'}), 400
        
        if storage_manager.eliminar_contacto(contacto_id):
            return jsonify({'success': True, 'message': 'Contacto eliminado correctamente'})
        else:
            return jsonify({'error': 'Error eliminando contacto'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/clear/<token>', methods=['DELETE'])
def limpiar_datos_admin(token):
    """Limpiar todos los datos desde admin"""
    if token != ADMIN_TOKEN:
        return jsonify({'error': 'Acceso no autorizado'}), 403
    
    try:
        total_eliminados = storage_manager.limpiar_todos_contactos()
        return jsonify({
            'success': True, 
            'message': f'{total_eliminados} contactos eliminados correctamente'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# CONFIGURACIÓN PARA RENDER
# ============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)