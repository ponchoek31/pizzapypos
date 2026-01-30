#!/usr/bin/env python3

# Script de prueba para verificar que todos los módulos funcionen
# Ejecutar desde /proyectos/pizza/programa

import sys
import os

print("=== VERIFICACIÓN DE MÓDULOS PYTHON ===")
print(f"Python version: {sys.version}")
print(f"Directorio actual: {os.getcwd()}")
print(f"Archivos en directorio: {os.listdir('.')}")

print("\n1. Probando importación de database...")
try:
    from database import db
    print("✅ database.py importado correctamente")
    
    print("2. Probando conexión a base de datos...")
    if db.connect():
        print("✅ Conexión a base de datos exitosa")
        
        print("3. Probando consulta simple...")
        result = db.execute_query("SELECT COUNT(*) as count FROM usuarios")
        if result:
            print(f"✅ Consulta exitosa. Usuarios en BD: {result[0]['count']}")
        else:
            print("❌ Error en consulta")
        
        db.close()
    else:
        print("❌ Error de conexión a base de datos")
        
except ImportError as e:
    print(f"❌ Error importando database: {e}")
    print("Solución: Asegúrate de que database.py existe en el directorio")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

print("\n4. Probando importación de auth...")
try:
    from auth import auth
    print("✅ auth.py importado correctamente")
except ImportError as e:
    print(f"❌ Error importando auth: {e}")
    sys.exit(1)

print("\n5. Probando importación de printer...")
try:
    from printer import printer
    print("✅ printer.py importado correctamente")
except ImportError as e:
    print(f"❌ Error importando printer: {e}")
    sys.exit(1)

print("\n6. Probando tkinter...")
try:
    import tkinter as tk
    print("✅ tkinter disponible")
except ImportError:
    print("❌ tkinter no disponible. Instalar con: sudo apt install python3-tk")
    sys.exit(1)

print("\n7. Probando dependencias adicionales...")
try:
    import pymysql
    print("✅ PyMySQL disponible")
except ImportError:
    print("❌ PyMySQL no disponible. Instalar con: pip3 install PyMySQL --break-system-packages")

try:
    import reportlab
    print("✅ ReportLab disponible")
except ImportError:
    print("❌ ReportLab no disponible. Instalar con: pip3 install reportlab --break-system-packages")

print("\n=== VERIFICACIÓN COMPLETADA ===")
print("Si todos los módulos están ✅, puedes ejecutar:")
print("python3 main.py")
