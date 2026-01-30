#!/bin/bash

# Script de instalación completa con todos los archivos
# Soluciona el error "from database import db"

echo "=== INSTALACIÓN COMPLETA SISTEMA POS ==="
echo "Solucionando error de importación de módulos..."

# Crear directorio
sudo mkdir -p /proyectos/pizza/programa
sudo chown $USER:$USER /proyectos/pizza/programa
cd /proyectos/pizza/programa

# Instalar dependencias del sistema
echo "Instalando dependencias del sistema..."
sudo apt update
sudo apt install -y python3 python3-pip python3-tk mariadb-server mariadb-client

# Instalar dependencias Python
echo "Instalando dependencias Python..."
pip3 install PyMySQL reportlab openpyxl Pillow --break-system-packages

# Configurar MariaDB
echo "Configurando base de datos..."
sudo systemctl start mariadb
sudo systemctl enable mariadb

# Crear base de datos y usuario
sudo mysql << 'SQLEOF'
CREATE DATABASE IF NOT EXISTS restaurant_pos;
CREATE USER IF NOT EXISTS 'poncho'@'localhost' IDENTIFIED BY 'poncho';
GRANT ALL PRIVILEGES ON restaurant_pos.* TO 'poncho'@'localhost';
FLUSH PRIVILEGES;
SQLEOF

echo "Creando archivo database.py..."
cat > database.py << 'PYEOF'
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

echo "Creando archivo auth.py..."
cat > auth.py << 'PYEOF'
from database import db
import hashlib

class Auth:
    def __init__(self):
        self.current_user = None
        self.current_turno = None

    def login(self, username, password):
        query = """
        SELECT id, nombre, username, tipo 
        FROM usuarios 
        WHERE username = %s AND password = %s AND activo = 1
        """
        user = db.execute_one(query, (username, password))
        
        if user:
            self.current_user = user
            # Si es cajero, verificar si tiene turno abierto
            if user['tipo'] == 'cajero':
                self.check_turno_abierto()
            return True
        return False

    def check_turno_abierto(self):
        query = """
        SELECT * FROM turnos 
        WHERE cajero_id = %s AND estado = 'abierto'
        ORDER BY fecha_inicio DESC 
        LIMIT 1
        """
        turno = db.execute_one(query, (self.current_user['id'],))
        if turno:
            self.current_turno = turno

    def logout(self):
        self.current_user = None
        self.current_turno = None

    def is_authenticated(self):
        return self.current_user is not None

    def has_permission(self, required_type):
        if not self.current_user:
            return False
        
        user_type = self.current_user['tipo']
        
        if required_type == 'cajero':
            return user_type in ['cajero', 'administrador', 'superusuario']
        elif required_type == 'administrador':
            return user_type in ['administrador', 'superusuario']
        elif required_type == 'superusuario':
            return user_type == 'superusuario'
        
        return False

    def crear_turno(self, fondo_inicial):
        if not self.current_user or self.current_user['tipo'] != 'cajero':
            return False
        
        # Verificar que no tenga turno abierto
        if self.current_turno:
            return False
        
        query = """
        INSERT INTO turnos (cajero_id, fondo_inicial, fecha_inicio)
        VALUES (%s, %s, NOW())
        """
        turno_id = db.execute_one(query, (self.current_user['id'], fondo_inicial))
        
        if turno_id:
            # Cargar el turno creado
            query = "SELECT * FROM turnos WHERE id = %s"
            self.current_turno = db.execute_one(query, (turno_id,))
            return True
        
        return False

    def cerrar_turno(self, efectivo_final, tarjeta_final):
        if not self.current_turno:
            return False
        
        # Calcular total de ventas del turno
        query = """
        SELECT COALESCE(SUM(total), 0) as total_ventas
        FROM ordenes 
        WHERE turno_id = %s
        """
        result = db.execute_one(query, (self.current_turno['id'],))
        total_ventas = result['total_ventas'] if result else 0
        
        # Calcular faltante
        total_esperado = self.current_turno['fondo_inicial'] + total_ventas
        total_real = efectivo_final + tarjeta_final
        faltante = total_esperado - total_real
        
        # Cerrar turno
        query = """
        UPDATE turnos 
        SET fecha_cierre = NOW(), efectivo_final = %s, tarjeta_final = %s,
            total_ventas = %s, faltante = %s, estado = 'cerrado'
        WHERE id = %s
        """
        result = db.execute_query(query, (
            efectivo_final, tarjeta_final, total_ventas, faltante, self.current_turno['id']
        ))
        
        if result:
            self.current_turno = None
            return True
        
        return False

# Instancia global de autenticación
auth = Auth()
PYEOF

echo "Creando archivo printer.py..."
cat > printer.py << 'PYEOF'
import os
import subprocess
from datetime import datetime
from database import db

class TicketPrinter:
    def __init__(self):
        self.printer_name = "thermal_printer"
        self.width = 32

    def format_line(self, text, width=None):
        if width is None:
            width = self.width
        return text[:width].ljust(width)

    def format_price(self, price):
        return f"${price:.2f}"

    def center_text(self, text, width=None):
        if width is None:
            width = self.width
        if len(text) >= width:
            return text[:width]
        padding = (width - len(text)) // 2
        return " " * padding + text

    def print_customer_ticket(self, orden_id):
        try:
            # Obtener información de la orden
            query = """
            SELECT o.*, c.nombre as cliente_nombre, c.telefono,
                   u.nombre as cajero_nombre
            FROM ordenes o
            LEFT JOIN clientes c ON o.cliente_id = c.id
            LEFT JOIN usuarios u ON o.cajero_id = u.id
            WHERE o.id = %s
            """
            orden = db.execute_one(query, (orden_id,))
            
            if not orden:
                return False

            # Obtener detalles de la orden
            query = """
            SELECT od.*, p.nombre as producto_nombre
            FROM orden_detalles od
            JOIN productos p ON od.producto_id = p.id
            WHERE od.orden_id = %s
            """
            detalles = db.execute_query(query, (orden_id,))

            # Crear contenido del ticket
            ticket_content = []
            
            ticket_content.append("=" * self.width)
            ticket_content.append(self.center_text("PIZZERIA SISTEMA POS"))
            ticket_content.append(self.center_text("TICKET DE VENTA"))
            ticket_content.append("=" * self.width)
            ticket_content.append("")
            
            ticket_content.append(f"Orden: {orden['numero_orden']}")
            ticket_content.append(f"Fecha: {orden['fecha_orden'].strftime('%d/%m/%Y %H:%M')}")
            ticket_content.append(f"Cajero: {orden['cajero_nombre']}")
            ticket_content.append(f"Tipo: {orden['tipo_orden'].title()}")
            
            if orden['cliente_nombre']:
                ticket_content.append(f"Cliente: {orden['cliente_nombre']}")
            
            ticket_content.append("")
            ticket_content.append("-" * self.width)
            ticket_content.append("PRODUCTOS")
            ticket_content.append("-" * self.width)
            
            for detalle in detalles:
                name_line = f"{detalle['cantidad']}x {detalle['producto_nombre']}"
                price_line = f"   {self.format_price(detalle['precio_unitario'])} c/u = {self.format_price(detalle['subtotal'])}"
                ticket_content.append(name_line[:self.width])
                ticket_content.append(price_line)
            
            ticket_content.append("")
            ticket_content.append("-" * self.width)
            ticket_content.append(f"TOTAL: {self.format_price(orden['total'])}")
            ticket_content.append(f"Pago ({orden['metodo_pago']}): {self.format_price(orden['monto_pagado'])}")
            if orden['cambio'] > 0:
                ticket_content.append(f"Cambio: {self.format_price(orden['cambio'])}")
            
            ticket_content.append("")
            ticket_content.append("=" * self.width)
            ticket_content.append(self.center_text("¡GRACIAS POR SU COMPRA!"))
            ticket_content.append("=" * self.width)

            # Guardar ticket
            ticket_path = f"/tmp/ticket_venta_{orden_id}.txt"
            with open(ticket_path, 'w', encoding='utf-8') as f:
                for line in ticket_content:
                    f.write(line + '\n')

            print(f"Ticket de venta guardado en: {ticket_path}")
            return ticket_path

        except Exception as e:
            print(f"Error imprimiendo ticket de venta: {e}")
            return False

    def print_kitchen_ticket(self, orden_id):
        try:
            query = """
            SELECT o.*, c.nombre as cliente_nombre, c.telefono
            FROM ordenes o
            LEFT JOIN clientes c ON o.cliente_id = c.id
            WHERE o.id = %s
            """
            orden = db.execute_one(query, (orden_id,))
            
            if not orden:
                return False

            query = """
            SELECT od.*, p.nombre as producto_nombre
            FROM orden_detalles od
            JOIN productos p ON od.producto_id = p.id
            WHERE od.orden_id = %s
            """
            detalles = db.execute_query(query, (orden_id,))

            comanda_content = []
            comanda_content.append("=" * self.width)
            comanda_content.append(self.center_text("COMANDA DE COCINA"))
            comanda_content.append("=" * self.width)
            comanda_content.append("")
            comanda_content.append(f"ORDEN: {orden['numero_orden']}")
            comanda_content.append(f"HORA: {orden['fecha_orden'].strftime('%H:%M')}")
            comanda_content.append(f"TIPO: {orden['tipo_orden'].upper()}")
            
            if orden['cliente_nombre'] and orden['cliente_nombre'] != 'Cliente Mostrador':
                comanda_content.append(f"CLIENTE: {orden['cliente_nombre']}")
            
            comanda_content.append("")
            comanda_content.append("-" * self.width)
            comanda_content.append("PRODUCTOS A PREPARAR")
            comanda_content.append("-" * self.width)
            
            for detalle in detalles:
                qty_product = f"{detalle['cantidad']}x {detalle['producto_nombre']}"
                comanda_content.append(qty_product[:self.width])
                comanda_content.append("")
            
            comanda_content.append("=" * self.width)

            comanda_path = f"/tmp/comanda_{orden_id}.txt"
            with open(comanda_path, 'w', encoding='utf-8') as f:
                for line in comanda_content:
                    f.write(line + '\n')

            print(f"Comanda guardada en: {comanda_path}")
            return comanda_path

        except Exception as e:
            print(f"Error imprimiendo comanda: {e}")
            return False

    def print_corte_caja(self, turno_id):
        try:
            query = """
            SELECT t.*, u.nombre as cajero_nombre
            FROM turnos t
            JOIN usuarios u ON t.cajero_id = u.id
            WHERE t.id = %s
            """
            turno = db.execute_one(query, (turno_id,))
            
            if not turno:
                return False

            query = """
            SELECT 
                COUNT(*) as total_ordenes,
                SUM(CASE WHEN metodo_pago = 'efectivo' THEN total ELSE 0 END) as ventas_efectivo,
                SUM(CASE WHEN metodo_pago = 'tarjeta' THEN total ELSE 0 END) as ventas_tarjeta,
                SUM(total) as ventas_total
            FROM ordenes 
            WHERE turno_id = %s
            """
            ventas = db.execute_one(query, (turno_id,))

            corte_content = []
            corte_content.append("=" * self.width)
            corte_content.append(self.center_text("CORTE DE CAJA"))
            corte_content.append("=" * self.width)
            corte_content.append("")
            corte_content.append(f"Turno: {turno['id']}")
            corte_content.append(f"Cajero: {turno['cajero_nombre']}")
            corte_content.append(f"Inicio: {turno['fecha_inicio'].strftime('%d/%m/%Y %H:%M')}")
            corte_content.append(f"Cierre: {turno['fecha_cierre'].strftime('%d/%m/%Y %H:%M')}")
            corte_content.append("")
            corte_content.append("-" * self.width)
            corte_content.append("RESUMEN DE VENTAS")
            corte_content.append("-" * self.width)
            corte_content.append(f"Ordenes: {ventas['total_ordenes'] or 0}")
            corte_content.append(f"Efectivo: {self.format_price(ventas['ventas_efectivo'] or 0)}")
            corte_content.append(f"Tarjeta: {self.format_price(ventas['ventas_tarjeta'] or 0)}")
            corte_content.append(f"Total ventas: {self.format_price(ventas['ventas_total'] or 0)}")
            corte_content.append("")
            corte_content.append("-" * self.width)
            corte_content.append("ARQUEO DE CAJA")
            corte_content.append("-" * self.width)
            corte_content.append(f"Fondo inicial: {self.format_price(turno['fondo_inicial'])}")
            corte_content.append(f"Efectivo final: {self.format_price(turno['efectivo_final'])}")
            corte_content.append(f"Tarjeta final: {self.format_price(turno['tarjeta_final'])}")
            
            if turno['faltante'] != 0:
                status = "FALTANTE" if turno['faltante'] > 0 else "SOBRANTE"
                corte_content.append(f"{status}: {self.format_price(abs(turno['faltante']))}")
            else:
                corte_content.append("ESTADO: CUADRADO")
            
            corte_content.append("")
            corte_content.append("-" * self.width)
            corte_content.append("FIRMAS:")
            corte_content.append("Cajero: ________________")
            corte_content.append("Supervisor: _____________")
            corte_content.append("=" * self.width)

            corte_path = f"/tmp/corte_caja_{turno_id}.txt"
            with open(corte_path, 'w', encoding='utf-8') as f:
                for line in corte_content:
                    f.write(line + '\n')

            print(f"Corte de caja guardado en: {corte_path}")
            return corte_path

        except Exception as e:
            print(f"Error imprimiendo corte de caja: {e}")
            return False

# Instancia global del printer
printer = TicketPrinter()
PYEOF

echo "Creando archivo config.py..."
cat > config.py << 'PYEOF'
# Configuración del Sistema POS

DB_CONFIG = {
    'host': 'localhost',
    'user': 'poncho',
    'password': 'poncho',
    'database': 'restaurant_pos',
    'charset': 'utf8mb4'
}

PRINTER_CONFIG = {
    'name': 'thermal_printer',
    'width': 32,
    'path': '/tmp/tickets/'
}

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

echo "Creando estructura de base de datos..."
mysql -u poncho -pponcho restaurant_pos << 'SQLEOF'

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

SQLEOF

# Verificar que los archivos se crearon correctamente
echo ""
echo "=== VERIFICANDO INSTALACIÓN ==="
if [ -f "database.py" ]; then
    echo "✅ database.py creado"
else
    echo "❌ Error creando database.py"
fi

if [ -f "auth.py" ]; then
    echo "✅ auth.py creado"
else
    echo "❌ Error creando auth.py"
fi

if [ -f "printer.py" ]; then
    echo "✅ printer.py creado"
else
    echo "❌ Error creando printer.py"
fi

# Probar la importación
echo "Probando importación de módulos..."
python3 -c "
try:
    from database import db
    print('✅ database.py importado correctamente')
    if db.connect():
        print('✅ Conexión a base de datos exitosa')
        db.close()
    else:
        print('❌ Error de conexión a base de datos')
except ImportError as e:
    print('❌ Error importando database:', e)
except Exception as e:
    print('❌ Error:', e)
"

echo ""
echo "=== INSTALACIÓN COMPLETADA ==="
echo "Directorio: /proyectos/pizza/programa"
echo ""
echo "Usuarios del sistema:"
echo "- Administrador: admin/admin"
echo "- Cajero: cajero/cajero"
echo "- SuperUsuario: super/super"
echo ""
echo "Para ejecutar el sistema:"
echo "cd /proyectos/pizza/programa"
echo "python3 main.py"
echo ""
echo "Si necesitas el archivo main.py completo, avísame."
