#!/bin/bash

# Script de instalación automática del Sistema POS para Restaurante
# Usuario: poncho / Password: poncho

echo "=== INSTALANDO SISTEMA POS PARA RESTAURANTE ==="

# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias del sistema
sudo apt install -y python3 python3-pip python3-tk mariadb-server mariadb-client

# Instalar dependencias de Python
pip3 install PyMySQL reportlab openpyxl Pillow

# Crear directorio del proyecto
sudo mkdir -p /proyectos/pizza/programa
sudo chown poncho:poncho /proyectos/pizza/programa
cd /proyectos/pizza/programa

# Configurar MariaDB
sudo systemctl start mariadb
sudo systemctl enable mariadb

# Configurar usuario de base de datos
sudo mysql -e "CREATE DATABASE IF NOT EXISTS restaurant_pos;"
sudo mysql -e "CREATE USER IF NOT EXISTS 'poncho'@'localhost' IDENTIFIED BY 'poncho';"
sudo mysql -e "GRANT ALL PRIVILEGES ON restaurant_pos.* TO 'poncho'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"

echo "=== CREANDO ESTRUCTURA DE BASE DE DATOS ==="

# Crear tablas
mysql -u poncho -pponcho restaurant_pos << 'EOF'

CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    tipo ENUM('cajero', 'administrador', 'superusuario') NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS clientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    telefono VARCHAR(20) UNIQUE,
    direccion TEXT,
    producto_preferido VARCHAR(100),
    total_consumo DECIMAL(10,2) DEFAULT 0,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS categorias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    activo BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS productos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    precio DECIMAL(8,2) NOT NULL,
    categoria_id INT,
    activo BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id)
);

CREATE TABLE IF NOT EXISTS turnos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cajero_id INT NOT NULL,
    fondo_inicial DECIMAL(10,2) NOT NULL,
    fecha_inicio DATETIME NOT NULL,
    fecha_cierre DATETIME NULL,
    efectivo_final DECIMAL(10,2) DEFAULT 0,
    tarjeta_final DECIMAL(10,2) DEFAULT 0,
    total_ventas DECIMAL(10,2) DEFAULT 0,
    faltante DECIMAL(10,2) DEFAULT 0,
    estado ENUM('abierto', 'cerrado') DEFAULT 'abierto',
    FOREIGN KEY (cajero_id) REFERENCES usuarios(id)
);

CREATE TABLE IF NOT EXISTS arqueos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    turno_id INT NOT NULL,
    monto DECIMAL(10,2) NOT NULL,
    fecha_arqueo DATETIME DEFAULT CURRENT_TIMESTAMP,
    administrador_id INT NOT NULL,
    FOREIGN KEY (turno_id) REFERENCES turnos(id),
    FOREIGN KEY (administrador_id) REFERENCES usuarios(id)
);

CREATE TABLE IF NOT EXISTS ordenes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    numero_orden VARCHAR(20) UNIQUE NOT NULL,
    cliente_id INT NULL,
    cliente_nombre VARCHAR(100),
    tipo_orden ENUM('mostrador', 'restaurante', 'telefonico') NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    total DECIMAL(10,2) NOT NULL,
    metodo_pago ENUM('efectivo', 'tarjeta') NOT NULL,
    monto_pagado DECIMAL(10,2) NOT NULL,
    cambio DECIMAL(10,2) DEFAULT 0,
    turno_id INT NOT NULL,
    cajero_id INT NOT NULL,
    fecha_orden DATETIME DEFAULT CURRENT_TIMESTAMP,
    estado ENUM('pendiente', 'completada', 'cancelada') DEFAULT 'pendiente',
    FOREIGN KEY (cliente_id) REFERENCES clientes(id),
    FOREIGN KEY (turno_id) REFERENCES turnos(id),
    FOREIGN KEY (cajero_id) REFERENCES usuarios(id)
);

CREATE TABLE IF NOT EXISTS orden_detalles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    orden_id INT NOT NULL,
    producto_id INT NOT NULL,
    cantidad INT NOT NULL,
    precio_unitario DECIMAL(8,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (orden_id) REFERENCES ordenes(id),
    FOREIGN KEY (producto_id) REFERENCES productos(id)
);

-- Insertar datos iniciales
INSERT IGNORE INTO usuarios (nombre, username, password, tipo) VALUES 
('Administrador', 'admin', 'admin', 'administrador'),
('SuperUsuario', 'super', 'super', 'superusuario'),
('Cajero Demo', 'cajero', 'cajero', 'cajero');

INSERT IGNORE INTO categorias (nombre) VALUES 
('Pizzas'), ('Bebidas'), ('Entradas'), ('Postres');

INSERT IGNORE INTO productos (nombre, precio, categoria_id) VALUES 
('Pizza Margherita', 150.00, 1),
('Pizza Pepperoni', 180.00, 1),
('Pizza Hawaiana', 170.00, 1),
('Coca Cola', 25.00, 2),
('Agua', 15.00, 2),
('Cerveza', 35.00, 2),
('Alitas', 80.00, 3),
('Pan de Ajo', 45.00, 3),
('Helado', 40.00, 4),
('Cheesecake', 60.00, 4);

INSERT IGNORE INTO clientes (nombre, telefono, direccion) VALUES 
('Cliente Mostrador', '0000000000', 'Venta Mostrador'),
('María García', '6561234567', 'Av. Principal 123'),
('Juan Pérez', '6567654321', 'Col. Centro 456');

EOF

echo "=== CREANDO ARCHIVOS DEL SISTEMA ==="

# Crear archivos del sistema
cat > /proyectos/pizza/programa/database.py << 'PYEOF'
import pymysql
from pymysql.cursors import DictCursor
import datetime

class Database:
    def __init__(self):
        self.host = 'localhost'
        self.user = 'poncho'
        self.password = 'poncho'
        self.database = 'restaurant_pos'
        self.connection = None

    def connect(self):
        try:
            self.connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                cursorclass=DictCursor
            )
            return True
        except Exception as e:
            print(f"Error conectando a la base de datos: {e}")
            return False

    def execute_query(self, query, params=None):
        try:
            if not self.connection:
                if not self.connect():
                    return None
            
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                if query.strip().upper().startswith('SELECT'):
                    result = cursor.fetchall()
                else:
                    self.connection.commit()
                    result = cursor.rowcount
                return result
        except Exception as e:
            print(f"Error ejecutando query: {e}")
            if self.connection:
                self.connection.rollback()
            return None

    def execute_one(self, query, params=None):
        try:
            if not self.connection:
                if not self.connect():
                    return None
            
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                if query.strip().upper().startswith('SELECT'):
                    result = cursor.fetchone()
                else:
                    self.connection.commit()
                    result = cursor.lastrowid
                return result
        except Exception as e:
            print(f"Error ejecutando query: {e}")
            if self.connection:
                self.connection.rollback()
            return None

    def close(self):
        if self.connection:
            self.connection.close()

# Instancia global de la base de datos
db = Database()
PYEOF

# Crear archivo de configuración
cat > /proyectos/pizza/programa/config.py << 'PYEOF'
# Configuración del Sistema POS

# Base de datos
DB_CONFIG = {
    'host': 'localhost',
    'user': 'poncho',
    'password': 'poncho',
    'database': 'restaurant_pos',
    'charset': 'utf8mb4'
}

# Configuración de impresora térmica
PRINTER_CONFIG = {
    'name': 'thermal_printer',
    'width': 32,  # caracteres por línea
    'path': '/tmp/tickets/'  # ruta donde guardar tickets
}

# Configuración de la aplicación
APP_CONFIG = {
    'name': 'Sistema POS Restaurante',
    'version': '1.0',
    'window_size': '1024x768',
    'theme_colors': {
        'primary': '#3498db',
        'success': '#27ae60', 
        'danger': '#e74c3c',
        'warning': '#f39c12',
        'dark': '#34495e',
        'light': '#f5f5f5'
    }
}
PYEOF

# Crear requirements.txt
cat > /proyectos/pizza/programa/requirements.txt << 'PYEOF'
PyMySQL==1.0.2
reportlab==4.0.4
openpyxl==3.1.2
Pillow==10.0.0
PYEOF

echo "✅ Archivos del sistema creados"

echo "=== INSTALACIÓN COMPLETADA ==="
echo "Base de datos: restaurant_pos"
echo "Usuario DB: poncho"
echo "Password DB: poncho"
echo ""
echo "Usuarios del sistema:"
echo "Administrador: admin/admin"
echo "SuperUsuario: super/super" 
echo "Cajero: cajero/cajero"
echo ""
echo "Para ejecutar: cd /proyectos/pizza/programa && python3 main.py"

