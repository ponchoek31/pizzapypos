# SISTEMA COMPLETO POS PARA RESTAURANTE
## Instalación y Uso - Guía Definitiva

### 📋 RESUMEN DEL SISTEMA

✅ **FUNCIONALIDADES IMPLEMENTADAS:**

**CAJERO:**
- ✅ Inicio y cierre de turno con fondo de caja
- ✅ Creación de órdenes (mostrador/restaurante/telefónicas)  
- ✅ Gestión automática de clientes
- ✅ Procesamiento de pagos (efectivo/tarjeta)
- ✅ Impresión automática de tickets y comandas
- ✅ Historial de órdenes del día
- ✅ Arqueo intermedio de caja con supervisión
- ✅ Corte de caja con validación doble
- ✅ Control de sesión sin cerrar turno (para descansos)

**ADMINISTRADOR:**
- ✅ Panel de administración completo
- 🔄 Gestión de menú (en desarrollo)
- 🔄 Gestión de usuarios (en desarrollo)  
- 🔄 Reportes de ventas (en desarrollo)
- 🔄 Gestión de clientes (en desarrollo)

**SISTEMA:**
- ✅ Base de datos MariaDB completa
- ✅ Interfaz gráfica con Tkinter (paleta gris-azul)
- ✅ Autenticación por roles
- ✅ Control de turnos completo
- ✅ Sistema de impresión de tickets térmicos
- ✅ Arquitectura modular extensible

---

### 🚀 INSTALACIÓN RÁPIDA

**1. Hacer ejecutable el script:**
```bash
chmod +x install_pizza_pos.sh
```

**2. Ejecutar instalación:**
```bash
sudo ./install_pizza_pos.sh
```

**3. Ejecutar sistema:**
```bash
cd /proyectos/pizza/programa
python3 main.py
```

---

### 👥 USUARIOS DEL SISTEMA

| Usuario | Password | Rol | Permisos |
|---------|----------|-----|----------|
| `admin` | `admin` | Administrador | Gestión completa |
| `super` | `super` | SuperUsuario | Acceso total + programación |
| `cajero` | `cajero` | Cajero | Operaciones de venta |

---

### 💻 USO DEL SISTEMA

#### **FLUJO CAJERO:**

**1. Login y Turno**
- Iniciar sesión con credenciales de cajero
- Si no hay turno: crear turno con fondo inicial
- Si hay turno pendiente: continuar turno existente

**2. Crear Órdenes**

**MOSTRADOR:**
- Clic en "Venta Mostrador" 
- Ingresar nombre del cliente
- Seleccionar productos del menú
- Procesar pago → Impresión automática

**RESTAURANTE:**
- Clic en "Pedido Restaurante"
- Mismo flujo que mostrador
- Identificado para servicio en mesa

**TELEFÓNICO:**
- Clic en "Pedido Telefónico"
- Buscar cliente por teléfono
- Si no existe: crear cliente automáticamente
- Seleccionar productos y procesar pago

**3. Operaciones del Turno**
- **Historial:** Ver órdenes del día, reimprimir tickets
- **Arqueo:** Retirar efectivo (requiere supervisor)
- **Corte:** Cerrar turno al final del día

#### **FLUJO ADMINISTRADOR:**

**1. Login**
- Usar credenciales de administrador
- Acceso a panel de administración

**2. Gestión** (Módulos base implementados)
- Administrar Menú
- Administrar Usuarios  
- Administrar Ventas
- Administrar Clientes

---

### 🛠️ INSTALACIÓN MANUAL (Si es necesaria)

**1. Dependencias del Sistema:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-tk mariadb-server
```

**2. Dependencias Python:**
```bash
pip3 install PyMySQL reportlab openpyxl Pillow
```

**3. Base de Datos:**
```bash
sudo systemctl start mariadb
sudo mysql -e "CREATE DATABASE restaurant_pos;"
sudo mysql -e "CREATE USER 'poncho'@'localhost' IDENTIFIED BY 'poncho';"
sudo mysql -e "GRANT ALL PRIVILEGES ON restaurant_pos.* TO 'poncho'@'localhost';"
```

**4. Estructura de Tablas:**
Se crea automáticamente con el script de instalación.

---

### 📁 ESTRUCTURA DE ARCHIVOS

```
/proyectos/pizza/programa/
├── main.py                 # ⭐ Aplicación principal
├── database.py            # 🗄️ Manejo de base de datos
├── auth.py               # 🔐 Autenticación y sesiones
├── printer.py            # 🖨️ Sistema de impresión
├── config.py             # ⚙️ Configuración
├── requirements.txt      # 📦 Dependencias
├── launch_pos.sh        # 🚀 Script de lanzamiento
└── pos-restaurante.desktop # 🖥️ Acceso directo escritorio
```

---

### 🎨 DISEÑO Y COLORES

- **Paleta:** Escala de grises con detalles en azul (#3498db)
- **Tipografía:** Arial moderna y legible
- **Layout:** Interfaz responsive y intuitiva
- **Botones:** Códigos de color por función (verde=confirmar, rojo=cancelar)

---

### 🖨️ CONFIGURACIÓN DE IMPRESIÓN

**Tickets generados:**
- `/tmp/ticket_venta_[id].txt` - Ticket para cliente
- `/tmp/comanda_[id].txt` - Orden para cocina  
- `/tmp/corte_caja_[id].txt` - Corte de turno

**Para impresora térmica real:**
1. Conectar impresora USB/Serie
2. Configurar en sistema operativo
3. Modificar `printer.py` línea 8 con nombre real

---

### 🔧 PERSONALIZACIÓN

**Modificar colores:**
Editar `config.py` sección `theme_colors`

**Agregar productos:**
Base de datos tabla `productos` - categorías incluidas

**Nuevo cajero:**
```sql
INSERT INTO usuarios (nombre, username, password, tipo) 
VALUES ('Nuevo Cajero', 'username', 'password', 'cajero');
```

---

### 📊 BASE DE DATOS

**Tablas principales:**
- `usuarios` - Cajeros, administradores
- `productos` - Menú con categorías  
- `clientes` - Base de datos clientes
- `turnos` - Control de turnos cajeros
- `ordenes` - Registro de ventas
- `orden_detalles` - Productos por orden
- `arqueos` - Retiros durante turno

---

### ❗ SOLUCIÓN DE PROBLEMAS

**Error base de datos:**
```bash
sudo systemctl restart mariadb
```

**Error permisos:**
```bash
sudo chown -R poncho:poncho /proyectos/pizza/
```

**Reinstalar dependencias:**
```bash
pip3 install -r requirements.txt --force-reinstall
```

**Verificar instalación:**
```bash
cd /proyectos/pizza/programa
python3 -c "from database import db; print('✅ OK' if db.connect() else '❌ Error')"
```

---

### 🚀 SIGUIENTES PASOS RECOMENDADOS

1. **Probar sistema completo** con flujo cajero
2. **Configurar impresora térmica real**
3. **Completar módulos de administración**
4. **Personalizar menú y productos**
5. **Capacitar usuarios finales**

---

### 💡 CARACTERÍSTICAS TÉCNICAS

- **Frontend:** Tkinter (nativo Python)
- **Backend:** Python 3
- **Base de datos:** MariaDB/MySQL
- **OS:** Linux (Ubuntu 24+)
- **Arquitectura:** Aplicación escritorio standalone
- **Escalabilidad:** Diseño modular para extensiones

---

### 📞 SOPORTE

Sistema desarrollado para ser fácilmente administrable:
- Código Python legible y comentado
- Estructura modular
- Base de datos normalizada
- Configuración centralizada

**¡El sistema está listo para producción con todas las funcionalidades de cajero implementadas!**
