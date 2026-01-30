# Sistema POS para Restaurante

Sistema completo de punto de venta diseñado específicamente para restaurantes con pocas opciones de menú. Desarrollado en Python con interfaz de escritorio usando Tkinter.

## Características Principales

### Tipos de Usuario
- **Cajero**: Crear órdenes, gestionar turnos, historial del día
- **Administrador**: Gestión completa del sistema, reportes, configuración
- **SuperUsuario**: Acceso completo del sistema y programación

### Funcionalidades del Cajero
- ✅ Inicio y cierre de turno con fondo de caja
- ✅ Creación de órdenes (mostrador, restaurante, telefónicas)
- ✅ Gestión de clientes automática
- ✅ Procesamiento de pagos (efectivo/tarjeta)
- ✅ Impresión automática de tickets y comandas
- ✅ Historial de órdenes del día
- ✅ Arqueo intermedio de caja
- ✅ Corte de caja con supervisión

### Funcionalidades del Administrador
- 📋 Administración de menú y productos
- 👥 Gestión de usuarios cajeros
- 📊 Historial completo de ventas
- 📈 Reportes en Excel (mensual/semanal)
- 👤 Administración de clientes
- 📋 Top 10 clientes por consumo

## Instalación

### Instalación Automática

1. **Descargar script de instalación:**
```bash
chmod +x install_pizza_pos.sh
sudo ./install_pizza_pos.sh
```

### Instalación Manual

1. **Instalar dependencias del sistema:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-tk mariadb-server mariadb-client
```

2. **Instalar dependencias de Python:**
```bash
pip3 install -r requirements.txt
```

3. **Configurar MariaDB:**
```bash
sudo systemctl start mariadb
sudo systemctl enable mariadb
```

4. **Crear base de datos:**
```bash
sudo mysql -e "CREATE DATABASE restaurant_pos;"
sudo mysql -e "CREATE USER 'poncho'@'localhost' IDENTIFIED BY 'poncho';"
sudo mysql -e "GRANT ALL PRIVILEGES ON restaurant_pos.* TO 'poncho'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"
```

5. **Importar estructura de base de datos:**
```bash
mysql -u poncho -pponcho restaurant_pos < database_structure.sql
```

## Estructura de Archivos

```
/proyectos/pizza/programa/
├── main.py              # Aplicación principal
├── database.py          # Conexión y manejo de base de datos
├── auth.py             # Autenticación y manejo de sesiones
├── printer.py          # Manejo de impresión de tickets
├── config.py           # Configuración del sistema
├── requirements.txt    # Dependencias de Python
└── README.md          # Este archivo
```

## Uso del Sistema

### Ejecutar la Aplicación
```bash
cd /proyectos/pizza/programa
python3 main.py
```

### Usuarios por Defecto
- **Administrador**: admin / admin
- **SuperUsuario**: super / super  
- **Cajero**: cajero / cajero

### Flujo de Trabajo para Cajeros

1. **Iniciar Sesión**
   - Usar credenciales de cajero
   - Si no hay turno abierto, se solicitará crear uno

2. **Iniciar Turno**
   - Ingresar fondo inicial de caja
   - El sistema registra fecha/hora de inicio

3. **Crear Órdenes**
   - Seleccionar tipo (mostrador/restaurante/telefónica)
   - Para telefónicas: buscar o crear cliente
   - Agregar productos del menú
   - Procesar pago (efectivo/tarjeta)
   - Impresión automática de tickets

4. **Arqueo Intermedio** (Opcional)
   - Retirar efectivo durante el turno
   - Requiere autorización de administrador

5. **Corte de Caja**
   - Al final del turno
   - Contar efectivo y tarjetas
   - Supervisión de administrador
   - Cálculo automático de faltantes

### Flujo para Administradores

1. **Gestión de Menú**
   - Agregar/editar productos
   - Organizar por categorías
   - Activar/desactivar items

2. **Gestión de Usuarios**
   - Crear cajeros
   - Asignar credenciales

3. **Reportes de Ventas**
   - Consultar por día/período
   - Exportar a Excel
   - Revisar cortes de caja

4. **Gestión de Clientes**
   - Ver historial de clientes
   - Top 10 por consumo
   - Editar información

## Base de Datos

### Tablas Principales
- `usuarios`: Cajeros, administradores y superusuarios
- `productos`: Catálogo de productos con precios
- `clientes`: Base de datos de clientes
- `turnos`: Control de turnos de cajeros
- `ordenes`: Registro de todas las ventas
- `orden_detalles`: Desglose de productos por orden
- `arqueos`: Retiros de efectivo durante turnos

## Configuración de Impresora

El sistema está preparado para impresoras térmicas de 32 caracteres por línea. Los tickets se guardan temporalmente en `/tmp/` para pruebas.

Para configurar una impresora térmica real:
1. Conectar impresora via USB o serie
2. Configurar en sistema operativo
3. Modificar `printer.py` con el nombre correcto de la impresora

## Personalización

### Colores y Diseño
Editar `config.py` para cambiar:
- Paleta de colores
- Configuraciones de impresión
- Tamaños de ventana

### Agregar Funcionalidades
El sistema está diseñado para ser extensible:
- Nuevos módulos en archivos separados
- Estructura modular de base de datos
- Interfaz responsive con Tkinter

## Solución de Problemas

### Error de Conexión a Base de Datos
```bash
sudo systemctl status mariadb
sudo systemctl restart mariadb
```

### Error de Permisos
```bash
sudo chown -R poncho:poncho /proyectos/pizza/
```

### Reinstalar Dependencias
```bash
pip3 install -r requirements.txt --force-reinstall
```

## Soporte

Para soporte técnico o modificaciones, el sistema está desarrollado en Python con tecnologías estándar:
- **Frontend**: Tkinter (incluido en Python)
- **Base de datos**: MariaDB/MySQL
- **Reportes**: ReportLab, OpenPyXL

## Características de Seguridad

- ✅ Control de sesiones por usuario
- ✅ Validación de permisos por rol
- ✅ Auditoría de turnos y cortes de caja
- ✅ Verificación doble en operaciones críticas
- ✅ Backup automático de datos de turno

## Rendimiento

- Optimizado para uso local
- Respuesta inmediata en operaciones frecuentes
- Manejo eficiente de memoria
- Base de datos indexada para consultas rápidas

---

**Desarrollado para uso en Ciudad Juárez, Chihuahua, México**
