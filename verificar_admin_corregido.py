#!/usr/bin/env python3
"""
🔧 SCRIPT DE VERIFICACIÓN: Panel Admin Corregido
===============================================

Este script verifica que todos los componentes del sistema admin estén funcionando:
- Backend Flask con endpoints correctos
- Frontend conectado al backend
- Funciones CRUD operativas

Uso: python3 verificar_admin_corregido.py
"""

import requests
import json
import time
from datetime import datetime

def test_backend_endpoints():
    """Probar todos los endpoints del backend Flask"""
    print("🔍 Verificando Backend Flask...")
    print("-" * 50)
    
    base_url = "http://localhost:5000"  # Ajustar según tu configuración
    token = "2205"
    
    endpoints = [
        ("data", "GET", "Obtener datos"),
        ("add", "POST", "Agregar contacto"),
        ("update", "PUT", "Actualizar contacto"),
        ("delete", "DELETE", "Eliminar contacto"),
        ("clear", "DELETE", "Limpiar datos"),
        ("download", "GET", "Descargar Excel"),
        ("stats", "GET", "Estadísticas")
    ]
    
    resultados = {}
    
    for endpoint, method, description in endpoints:
        try:
            url = f"{base_url}/admin/{endpoint}/{token}"
            
            if method == "GET":
                response = requests.get(url, timeout=5)
            elif method == "POST":
                test_data = {
                    "nombre": "Test Usuario",
                    "email": "test@example.com",
                    "telefono": "123456789",
                    "tipo_consulta": "general",
                    "mensaje": "Mensaje de prueba",
                    "pagina_origen": "Test",
                    "estado": "nuevo"
                }
                response = requests.post(url, json=test_data, timeout=5)
            elif method == "PUT":
                test_data = {
                    "id": "test_id",
                    "nombre": "Test Usuario Updated",
                    "email": "test_updated@example.com"
                }
                response = requests.put(url, json=test_data, timeout=5)
            elif method == "DELETE":
                test_data = {"id": "test_id"}
                response = requests.delete(url, json=test_data, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ {description}: OK (Status {response.status_code})")
                resultados[endpoint] = True
            else:
                print(f"⚠️  {description}: Status {response.status_code}")
                resultados[endpoint] = False
                
        except requests.exceptions.ConnectionError:
            print(f"❌ {description}: No se puede conectar al servidor")
            print(f"   💡 Asegúrate de que Flask esté ejecutándose en {base_url}")
            resultados[endpoint] = False
        except Exception as e:
            print(f"❌ {description}: Error - {str(e)}")
            resultados[endpoint] = False
    
    return resultados

def test_frontend_files():
    """Verificar que los archivos frontend estén correctos"""
    print("\n🔍 Verificando Archivos Frontend...")
    print("-" * 50)
    
    archivos = [
        ("admin_corregido.html", "Panel admin corregido"),
        ("admin.html", "Panel admin actual"),
    ]
    
    resultados = {}
    
    for archivo, descripcion in archivos:
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                contenido = f.read()
            
            # Verificaciones básicas
            checks = {
                "Contraseña 2205": "const ADMIN_PASSWORD = '2205';" in contenido,
                "API Request": "async function apiRequest" in contenido,
                "Función verContacto": "function verContacto" in contenido,
                "Función editarContacto": "function editarContacto" in contenido,
                "Función eliminarContacto": "function eliminarContacto" in contenido,
                "Función guardarContacto": "async function guardarContacto" in contenido,
                "Fetch al backend": "fetch(`/admin/" in contenido,
                "Manejo de errores": "mostrarMensaje" in contenido
            }
            
            passed = sum(checks.values())
            total = len(checks)
            
            if passed == total:
                print(f"✅ {descripcion}: Todos los componentes OK ({passed}/{total})")
                resultados[archivo] = True
            else:
                print(f"⚠️  {descripcion}: {passed}/{total} componentes OK")
                for check, status in checks.items():
                    status_icon = "✅" if status else "❌"
                    print(f"   {status_icon} {check}")
                resultados[archivo] = False
                
        except FileNotFoundError:
            print(f"❌ {descripcion}: Archivo no encontrado")
            resultados[archivo] = False
        except Exception as e:
            print(f"❌ {descripcion}: Error - {str(e)}")
            resultados[archivo] = False
    
    return resultados

def generar_reporte_verificacion(resultados_backend, resultados_frontend):
    """Generar reporte final de verificación"""
    print("\n" + "="*60)
    print("📊 REPORTE DE VERIFICACIÓN FINAL")
    print("="*60)
    
    # Contar resultados
    backend_ok = sum(resultados_backend.values())
    backend_total = len(resultados_backend)
    frontend_ok = sum(resultados_frontend.values())
    frontend_total = len(resultados_frontend)
    
    print(f"🔧 Backend Flask: {backend_ok}/{backend_total} endpoints funcionando")
    print(f"🎨 Frontend: {frontend_ok}/{frontend_total} archivos correctos")
    
    # Estado general
    if backend_ok == backend_total and frontend_ok == frontend_total:
        print("\n🎉 ¡SISTEMA COMPLETAMENTE FUNCIONAL!")
        print("✅ Todos los componentes están operativos")
        print("✅ Los botones del admin deberían funcionar correctamente")
        
        print("\n📋 PRÓXIMOS PASOS:")
        print("1. ✅ Reemplaza admin.html con admin_corregido.html")
        print("2. ✅ Verifica que el servidor Flask esté ejecutándose")
        print("3. ✅ Prueba el acceso en https://dantepropiedades.com.ar/admin.html")
        print("4. ✅ Confirma que puedes editar, eliminar y ver contactos")
        
    else:
        print("\n⚠️  PROBLEMAS DETECTADOS")
        
        if backend_ok < backend_total:
            print("❌ Backend Flask necesita atención:")
            for endpoint, status in resultados_backend.items():
                if not status:
                    print(f"   - {endpoint}: No funciona")
        
        if frontend_ok < frontend_total:
            print("❌ Frontend necesita atención:")
            for archivo, status in resultados_frontend.items():
                if not status:
                    print(f"   - {archivo}: Problemas detectados")
        
        print("\n🔧 ACCIONES REQUERIDAS:")
        if backend_ok < backend_total:
            print("1. Verificar que Flask esté ejecutándose")
            print("2. Verificar endpoints en app.py")
            print("3. Verificar imports y dependencias")
        
        if frontend_ok < frontend_total:
            print("1. Usar admin_corregido.html como referencia")
            print("2. Verificar sintaxis JavaScript")
            print("3. Revisar console del navegador")

def main():
    """Función principal de verificación"""
    print("🚀 INICIANDO VERIFICACIÓN DEL SISTEMA ADMIN")
    print("=" * 60)
    print(f"⏰ Fecha/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Verificar backend
    resultados_backend = test_backend_endpoints()
    
    # Verificar frontend
    resultados_frontend = test_frontend_files()
    
    # Generar reporte final
    generar_reporte_verificacion(resultados_backend, resultados_frontend)
    
    print("\n" + "="*60)
    print("🏁 VERIFICACIÓN COMPLETADA")
    print("="*60)

if __name__ == "__main__":
    main()