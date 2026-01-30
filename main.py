#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import datetime
from database import db
from auth import auth
from printer import printer
import subprocess
import os

class RestaurantPOS:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Sistema POS Restaurante")
        self.root.geometry("1024x768")
        self.root.configure(bg='#f5f5f5')
        
        # Configurar estilo
        self.setup_styles()
        
        # Variables
        self.orden_actual = {'items': [], 'total': 0.0}
        self.cliente_actual = None
        
        # Inicializar
        if not db.connect():
            messagebox.showerror("Error", "No se pudo conectar a la base de datos")
            self.root.quit()
            return
        
        # Mostrar login
        self.show_login()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configurar colores - esquema azul consistente
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), background='#f8f9fa', foreground='#2c3e50')
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'), background='#f8f9fa', foreground='#34495e')
        style.configure('Blue.TButton', foreground='white', background='#3498db')
        style.configure('DarkBlue.TButton', foreground='white', background='#2980b9')
        style.configure('Gray.TButton', foreground='white', background='#95a5a6')
        style.configure('LightBlue.TButton', foreground='white', background='#5dade2')

    def show_login(self):
        self.clear_window()
        
        # Frame principal centrado
        main_frame = tk.Frame(self.root, bg='#f5f5f5')
        main_frame.pack(expand=True, fill='both')
        
        # Frame de login centrado
        login_frame = tk.Frame(main_frame, bg='white', relief='raised', bd=2)
        login_frame.place(relx=0.5, rely=0.5, anchor='center', width=400, height=300)
        
        # Título
        title_label = tk.Label(login_frame, text="Sistema POS Restaurante", 
                              font=('Arial', 18, 'bold'), bg='white', fg='#2c3e50')
        title_label.pack(pady=20)
        
        # Campos de login
        tk.Label(login_frame, text="Usuario:", font=('Arial', 12), bg='white').pack(pady=5)
        self.username_entry = tk.Entry(login_frame, font=('Arial', 12), width=20)
        self.username_entry.pack(pady=5)
        
        tk.Label(login_frame, text="Contraseña:", font=('Arial', 12), bg='white').pack(pady=5)
        self.password_entry = tk.Entry(login_frame, font=('Arial', 12), width=20, show='*')
        self.password_entry.pack(pady=5)
        
        # Botón de login
        login_btn = tk.Button(login_frame, text="Iniciar Sesión", font=('Arial', 12, 'bold'),
                             bg='#3498db', fg='white', width=15, command=self.login)
        login_btn.pack(pady=20)
        
        # Bind Enter key
        self.username_entry.bind('<Return>', lambda e: self.password_entry.focus())
        self.password_entry.bind('<Return>', lambda e: self.login())
        
        self.username_entry.focus()

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Por favor complete todos los campos")
            return
        
        if auth.login(username, password):
            if auth.current_user['tipo'] == 'cajero':
                # Verificar si necesita iniciar turno
                if not auth.current_turno:
                    self.show_iniciar_turno()
                else:
                    self.show_cajero_menu()
            elif auth.current_user['tipo'] in ['administrador', 'superusuario']:
                self.show_admin_menu()
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos")

    def show_iniciar_turno(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Iniciar Turno")
        dialog.geometry("380x280")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Configurar color de fondo
        dialog.configure(bg='#f8f9fa')
        
        # Frame principal compacto
        main_frame = tk.Frame(dialog, bg='#f8f9fa')
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        tk.Label(main_frame, text="🕐 INICIAR NUEVO TURNO", font=('Arial', 14, 'bold'), 
                bg='#f8f9fa', fg='#2c3e50').pack(pady=(0,15))
        
        # Frame para fondo inicial - más compacto
        fondo_frame = tk.LabelFrame(main_frame, text="Fondo Inicial de Caja", font=('Arial', 11),
                                   bg='#f8f9fa', fg='#2c3e50')
        fondo_frame.pack(pady=(0,15), fill='x')
        
        entry_frame = tk.Frame(fondo_frame, bg='#f8f9fa')
        entry_frame.pack(pady=10)
        
        tk.Label(entry_frame, text="$", font=('Arial', 16, 'bold'), bg='#f8f9fa').pack(side='left')
        fondo_entry = tk.Entry(entry_frame, font=('Arial', 16), width=8, justify='center',
                              relief='solid', bd=1)
        fondo_entry.pack(side='left', padx=5)
        
        def crear_turno():
            try:
                fondo_text = fondo_entry.get().strip()
                if not fondo_text:
                    messagebox.showerror("Error", "Por favor ingrese el fondo inicial")
                    fondo_entry.focus()
                    return
                
                fondo = float(fondo_text)
                if fondo < 0:
                    messagebox.showerror("Error", "El fondo inicial no puede ser negativo")
                    fondo_entry.focus()
                    return
                
                if auth.crear_turno(fondo):
                    messagebox.showinfo("Éxito", f"Turno iniciado correctamente\nFondo inicial: ${fondo:.2f}")
                    dialog.destroy()
                    self.show_cajero_menu()
                else:
                    messagebox.showerror("Error", "No se pudo crear el turno")
            except ValueError:
                messagebox.showerror("Error", "Por favor ingrese un monto válido")
                fondo_entry.focus()
        
        # Botones - más compactos
        button_frame = tk.Frame(main_frame, bg='#f8f9fa')
        button_frame.pack(pady=(0,5), fill='x')
        
        tk.Button(button_frame, text="CANCELAR", font=('Arial', 11, 'bold'),
                 bg='#95a5a6', fg='white', width=10, height=1,
                 command=self.root.quit).pack(side='left', padx=5)
        
        tk.Button(button_frame, text="INICIAR TURNO", font=('Arial', 11, 'bold'),
                 bg='#3498db', fg='white', width=12, height=1,
                 command=crear_turno).pack(side='right', padx=5)
        
        fondo_entry.focus()
        fondo_entry.bind('<Return>', lambda e: crear_turno())

    def show_cajero_menu(self):
        self.clear_window()
        
        # Header
        header_frame = tk.Frame(self.root, bg='#34495e', height=60)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        # Información del usuario y turno
        user_info = f"Usuario: {auth.current_user['nombre']} | Turno: {auth.current_turno['id']}"
        tk.Label(header_frame, text=user_info, font=('Arial', 12, 'bold'), 
                bg='#34495e', fg='white').pack(side='left', padx=20, pady=20)
        
        # Botones del header
        btn_frame = tk.Frame(header_frame, bg='#34495e')
        btn_frame.pack(side='right', padx=20, pady=10)
        
        tk.Button(btn_frame, text="Historial", command=self.show_historial).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Arqueo", command=self.show_arqueo).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Corte Caja", command=self.show_corte_caja).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Cerrar Sesión", command=self.logout).pack(side='left', padx=5)
        
        # Contenido principal
        main_frame = tk.Frame(self.root, bg='#f5f5f5')
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        # Botones de tipo de orden
        orden_frame = tk.LabelFrame(main_frame, text="Crear Nueva Orden", font=('Arial', 12, 'bold'))
        orden_frame.pack(fill='x', pady=(0, 20))
        
        btn_frame = tk.Frame(orden_frame)
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="Venta Mostrador", font=('Arial', 12, 'bold'),
                 bg='#3498db', fg='white', width=15, height=2,
                 command=lambda: self.nueva_orden('mostrador')).pack(side='left', padx=10)
        
        tk.Button(btn_frame, text="Pedido Restaurante", font=('Arial', 12, 'bold'),
                 bg='#2980b9', fg='white', width=15, height=2,
                 command=lambda: self.nueva_orden('restaurante')).pack(side='left', padx=10)
        
        tk.Button(btn_frame, text="Pedido Telefónico", font=('Arial', 12, 'bold'),
                 bg='#5dade2', fg='white', width=15, height=2,
                 command=lambda: self.nueva_orden('telefonico')).pack(side='left', padx=10)

    def nueva_orden(self, tipo_orden):
        self.tipo_orden = tipo_orden
        self.orden_actual = {'items': [], 'total': 0.0}
        self.cliente_actual = None
        
        if tipo_orden == 'telefonico':
            self.seleccionar_cliente()
        else:
            self.show_orden_screen()

    def seleccionar_cliente(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Seleccionar Cliente")
        dialog.geometry("420x300")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Configurar color de fondo
        dialog.configure(bg='#f8f9fa')
        
        # Frame principal compacto
        main_frame = tk.Frame(dialog, bg='#f8f9fa')
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        tk.Label(main_frame, text="📞 BUSCAR CLIENTE", font=('Arial', 14, 'bold'), 
                bg='#f8f9fa', fg='#2c3e50').pack(pady=(0,15))
        
        # Búsqueda por teléfono - más compacto
        search_frame = tk.LabelFrame(main_frame, text="Buscar por Teléfono", font=('Arial', 11),
                                    bg='#f8f9fa', fg='#2c3e50')
        search_frame.pack(pady=(0,15), fill='x')
        
        entry_frame = tk.Frame(search_frame, bg='#f8f9fa')
        entry_frame.pack(pady=10)
        
        tk.Label(entry_frame, text="📱", font=('Arial', 16), bg='#f8f9fa').pack(side='left', padx=5)
        phone_entry = tk.Entry(entry_frame, font=('Arial', 12), width=15, relief='solid', bd=1)
        phone_entry.pack(side='left', padx=5, fill='x', expand=True)
        
        def buscar_cliente():
            telefono = phone_entry.get().strip()
            if not telefono:
                messagebox.showerror("Error", "Por favor ingrese un número telefónico")
                phone_entry.focus()
                return
            
            query = "SELECT * FROM clientes WHERE telefono = %s"
            cliente = db.execute_one(query, (telefono,))
            
            if cliente:
                self.cliente_actual = cliente
                messagebox.showinfo("Cliente encontrado", 
                                  f"Cliente: {cliente['nombre']}\nTeléfono: {cliente['telefono']}\nDirección: {cliente['direccion'] or 'No especificada'}")
                dialog.destroy()
                self.show_orden_screen()
            else:
                response = messagebox.askyesno("Cliente no encontrado", 
                                             f"No se encontró un cliente con el teléfono {telefono}\n\n¿Desea crear un nuevo cliente?")
                if response:
                    self.crear_cliente_dialog(telefono, dialog)
        
        # Botones - más compactos
        button_frame = tk.Frame(main_frame, bg='#f8f9fa')
        button_frame.pack(pady=(0,5), fill='x')
        
        tk.Button(button_frame, text="CANCELAR", font=('Arial', 11, 'bold'),
                 bg='#95a5a6', fg='white', width=10, height=1,
                 command=dialog.destroy).pack(side='left', padx=5)
        
        tk.Button(button_frame, text="BUSCAR CLIENTE", font=('Arial', 11, 'bold'),
                 bg='#3498db', fg='white', width=15, height=1,
                 command=buscar_cliente).pack(side='right', padx=5)
        
        phone_entry.focus()
        phone_entry.bind('<Return>', lambda e: buscar_cliente())

    def crear_cliente_dialog(self, telefono, parent_dialog):
        dialog = tk.Toplevel(self.root)
        dialog.title("Crear Nuevo Cliente")
        dialog.geometry("400x320")
        dialog.resizable(False, False)
        dialog.transient(parent_dialog)
        dialog.grab_set()
        
        # Configurar color de fondo
        dialog.configure(bg='#f8f9fa')
        
        # Frame principal compacto
        main_frame = tk.Frame(dialog, bg='#f8f9fa')
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        tk.Label(main_frame, text="👤 CREAR NUEVO CLIENTE", font=('Arial', 14, 'bold'), 
                bg='#f8f9fa', fg='#2c3e50').pack(pady=(0,15))
        
        # Campos del formulario - más compactos
        fields_frame = tk.Frame(main_frame, bg='#f8f9fa')
        fields_frame.pack(pady=(0,15), fill='x')
        
        # Nombre
        tk.Label(fields_frame, text="Nombre completo:", font=('Arial', 11), 
                bg='#f8f9fa', fg='#2c3e50').grid(row=0, column=0, sticky='w', pady=6)
        nombre_entry = tk.Entry(fields_frame, width=20, font=('Arial', 11), relief='solid', bd=1)
        nombre_entry.grid(row=0, column=1, pady=6, padx=8, sticky='ew')
        
        # Teléfono
        tk.Label(fields_frame, text="Teléfono:", font=('Arial', 11), 
                bg='#f8f9fa', fg='#2c3e50').grid(row=1, column=0, sticky='w', pady=6)
        telefono_entry = tk.Entry(fields_frame, width=20, font=('Arial', 11), relief='solid', bd=1)
        telefono_entry.insert(0, telefono)
        telefono_entry.grid(row=1, column=1, pady=6, padx=8, sticky='ew')
        
        # Dirección
        tk.Label(fields_frame, text="Dirección:", font=('Arial', 11), 
                bg='#f8f9fa', fg='#2c3e50').grid(row=2, column=0, sticky='w', pady=6)
        direccion_entry = tk.Entry(fields_frame, width=20, font=('Arial', 11), relief='solid', bd=1)
        direccion_entry.grid(row=2, column=1, pady=6, padx=8, sticky='ew')
        
        # Configurar grid
        fields_frame.grid_columnconfigure(1, weight=1)
        
        def guardar_cliente():
            nombre = nombre_entry.get().strip()
            telefono = telefono_entry.get().strip()
            direccion = direccion_entry.get().strip()
            
            if not nombre:
                messagebox.showerror("Error", "El nombre es obligatorio")
                nombre_entry.focus()
                return
            
            if not telefono:
                messagebox.showerror("Error", "El teléfono es obligatorio")
                telefono_entry.focus()
                return
            
            query = """
            INSERT INTO clientes (nombre, telefono, direccion)
            VALUES (%s, %s, %s)
            """
            cliente_id = db.execute_one(query, (nombre, telefono, direccion))
            
            if cliente_id:
                query = "SELECT * FROM clientes WHERE id = %s"
                self.cliente_actual = db.execute_one(query, (cliente_id,))
                messagebox.showinfo("Éxito", f"Cliente '{nombre}' creado correctamente")
                dialog.destroy()
                parent_dialog.destroy()
                self.show_orden_screen()
            else:
                messagebox.showerror("Error", "No se pudo crear el cliente. Verifique que el teléfono no esté duplicado.")
        
        # Botones - más compactos
        button_frame = tk.Frame(main_frame, bg='#f8f9fa')
        button_frame.pack(pady=(0,5), fill='x')
        
        tk.Button(button_frame, text="CANCELAR", font=('Arial', 11, 'bold'),
                 bg='#95a5a6', fg='white', width=10, height=1,
                 command=dialog.destroy).pack(side='left', padx=5)
        
        tk.Button(button_frame, text="GUARDAR CLIENTE", font=('Arial', 11, 'bold'),
                 bg='#3498db', fg='white', width=15, height=1,
                 command=guardar_cliente).pack(side='right', padx=5)
        
        nombre_entry.focus()
        nombre_entry.bind('<Return>', lambda e: telefono_entry.focus())
        telefono_entry.bind('<Return>', lambda e: direccion_entry.focus())
        direccion_entry.bind('<Return>', lambda e: guardar_cliente())

    def show_orden_screen(self):
        self.clear_window()
        
        # Header con información de la orden
        header_frame = tk.Frame(self.root, bg='#34495e', height=60)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        info_text = f"Tipo: {self.tipo_orden.title()}"
        if self.cliente_actual:
            info_text += f" | Cliente: {self.cliente_actual['nombre']}"
        
        tk.Label(header_frame, text=info_text, font=('Arial', 12, 'bold'), 
                bg='#34495e', fg='white').pack(side='left', padx=20, pady=20)
        
        tk.Button(header_frame, text="Volver", command=self.show_cajero_menu).pack(side='right', padx=20, pady=15)
        
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#f5f5f5')
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        # Frame izquierdo - Menu de productos
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # Obtener productos
        self.show_productos_menu(left_frame)
        
        # Frame derecho - Resumen de orden
        right_frame = tk.Frame(main_frame, width=300)
        right_frame.pack(side='right', fill='y')
        right_frame.pack_propagate(False)
        
        self.show_orden_summary(right_frame)

    def show_productos_menu(self, parent):
        # Título
        tk.Label(parent, text="Seleccionar Productos", font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Obtener productos por categoría
        query = """
        SELECT c.nombre as categoria, p.id, p.nombre, p.precio
        FROM productos p
        JOIN categorias c ON p.categoria_id = c.id
        WHERE p.activo = 1
        ORDER BY c.nombre, p.nombre
        """
        productos = db.execute_query(query)
        
        # Crear notebook para categorías
        notebook = ttk.Notebook(parent)
        notebook.pack(fill='both', expand=True, pady=10)
        
        # Agrupar productos por categoría
        categorias = {}
        for producto in productos:
            cat = producto['categoria']
            if cat not in categorias:
                categorias[cat] = []
            categorias[cat].append(producto)
        
        # Crear tabs por categoría
        for categoria, productos_cat in categorias.items():
            tab_frame = ttk.Frame(notebook)
            notebook.add(tab_frame, text=categoria)
            
            # Crear grid de productos
            products_frame = tk.Frame(tab_frame)
            products_frame.pack(fill='both', expand=True, padx=20, pady=20)
            
            row, col = 0, 0
            for producto in productos_cat:
                btn_frame = tk.Frame(products_frame, relief='raised', bd=1, bg='white')
                btn_frame.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
                
                # Configurar grid
                products_frame.grid_columnconfigure(col, weight=1, minsize=150)
                products_frame.grid_rowconfigure(row, weight=1, minsize=80)
                
                # Información del producto
                tk.Label(btn_frame, text=producto['nombre'], font=('Arial', 11, 'bold'), 
                        bg='white').pack(pady=5)
                tk.Label(btn_frame, text=f"${producto['precio']:.2f}", font=('Arial', 10), 
                        bg='white', fg='#27ae60').pack()
                
                # Hacer clickeable
                def add_product(p=producto):
                    self.agregar_producto(p)
                
                btn_frame.bind("<Button-1>", lambda e, p=producto: self.agregar_producto(p))
                for widget in btn_frame.winfo_children():
                    widget.bind("<Button-1>", lambda e, p=producto: self.agregar_producto(p))
                
                col += 1
                if col >= 4:  # 4 productos por fila
                    col = 0
                    row += 1

    def show_orden_summary(self, parent):
        # Título
        tk.Label(parent, text="Resumen de Orden", font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Frame para nombre cliente (solo mostrador)
        if self.tipo_orden == 'mostrador':
            cliente_frame = tk.Frame(parent)
            cliente_frame.pack(fill='x', padx=10, pady=5)
            
            tk.Label(cliente_frame, text="Nombre cliente:").pack(anchor='w')
            self.cliente_nombre_entry = tk.Entry(cliente_frame)
            self.cliente_nombre_entry.pack(fill='x', pady=2)
        
        # Lista de productos
        list_frame = tk.Frame(parent)
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Scrollable listbox
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.items_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=15)
        self.items_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.items_listbox.yview)
        
        # Frame para total
        total_frame = tk.Frame(parent)
        total_frame.pack(fill='x', padx=10, pady=10)
        
        self.total_label = tk.Label(total_frame, text="TOTAL: $0.00", 
                                   font=('Arial', 16, 'bold'), fg='#27ae60')
        self.total_label.pack(anchor='center')
        
        # Botones de acción
        btn_frame = tk.Frame(parent)
        btn_frame.pack(fill='x', padx=10, pady=20)
        
        tk.Button(btn_frame, text="Eliminar Item", bg='#95a5a6', fg='white',
                 command=self.eliminar_item).pack(fill='x', pady=2)
        
        tk.Button(btn_frame, text="Procesar Pago", bg='#3498db', fg='white',
                 font=('Arial', 12, 'bold'), command=self.procesar_pago).pack(fill='x', pady=10)
        
        self.actualizar_resumen()

    def agregar_producto(self, producto):
        # Buscar si ya existe en la orden
        for item in self.orden_actual['items']:
            if item['id'] == producto['id']:
                item['cantidad'] += 1
                # Asegurar que el precio sea float
                precio_float = float(producto['precio'])
                item['subtotal'] = item['cantidad'] * precio_float
                break
        else:
            # Agregar nuevo item - convertir precio a float
            precio_float = float(producto['precio'])
            self.orden_actual['items'].append({
                'id': producto['id'],
                'nombre': producto['nombre'],
                'precio': precio_float,
                'cantidad': 1,
                'subtotal': precio_float
            })
        
        self.actualizar_resumen()

    def eliminar_item(self):
        selection = self.items_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.orden_actual['items']):
                del self.orden_actual['items'][index]
                self.actualizar_resumen()

    def actualizar_resumen(self):
        # Limpiar listbox
        self.items_listbox.delete(0, tk.END)
        
        # Agregar items
        total = 0
        for item in self.orden_actual['items']:
            text = f"{item['cantidad']}x {item['nombre']} - ${item['subtotal']:.2f}"
            self.items_listbox.insert(tk.END, text)
            total += item['subtotal']
        
        # Actualizar total
        self.orden_actual['total'] = total
        self.total_label.config(text=f"TOTAL: ${total:.2f}")

    def procesar_pago(self):
        print("DEBUG: Iniciando procesar_pago")
        print(f"DEBUG: Items en orden: {len(self.orden_actual['items'])}")
        print(f"DEBUG: Total: {self.orden_actual['total']}")
        print(f"DEBUG: Tipo de orden: {self.tipo_orden}")
        
        if not self.orden_actual['items']:
            messagebox.showerror("Error", "La orden está vacía")
            return
        
        # Validar nombre para mostrador
        cliente_nombre = None
        if self.tipo_orden == 'mostrador':
            cliente_nombre = self.cliente_nombre_entry.get().strip()
            print(f"DEBUG: Nombre cliente mostrador: '{cliente_nombre}'")
            if not cliente_nombre:
                messagebox.showerror("Error", "Por favor ingrese el nombre del cliente")
                return
        
        print(f"DEBUG: Llamando show_payment_dialog con cliente_nombre: {cliente_nombre}")
        self.show_payment_dialog(cliente_nombre)

    def show_payment_dialog(self, cliente_nombre=None):
        dialog = tk.Toplevel(self.root)
        dialog.title("Procesar Pago")
        dialog.geometry("420x400")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Configurar color de fondo
        dialog.configure(bg='#f8f9fa')
        
        # Frame principal compacto
        main_frame = tk.Frame(dialog, bg='#f8f9fa')
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Total a pagar - más compacto
        tk.Label(main_frame, text="TOTAL A PAGAR", font=('Arial', 14, 'bold'), 
                bg='#f8f9fa', fg='#2c3e50').pack(pady=(0,5))
        tk.Label(main_frame, text=f"${self.orden_actual['total']:.2f}", 
                font=('Arial', 24, 'bold'), fg='#3498db', bg='#f8f9fa').pack(pady=(0,15))
        
        # Método de pago - más compacto
        payment_frame = tk.LabelFrame(main_frame, text="Método de Pago", font=('Arial', 11), 
                                     bg='#f8f9fa', fg='#2c3e50')
        payment_frame.pack(pady=(0,10), fill='x')
        
        payment_method = tk.StringVar(value='efectivo')
        
        radio_frame = tk.Frame(payment_frame, bg='#f8f9fa')
        radio_frame.pack(pady=8)
        
        tk.Radiobutton(radio_frame, text="💵 Efectivo", variable=payment_method, 
                      value='efectivo', font=('Arial', 11), bg='#f8f9fa').pack(side='left', padx=15)
        tk.Radiobutton(radio_frame, text="💳 Tarjeta", variable=payment_method, 
                      value='tarjeta', font=('Arial', 11), bg='#f8f9fa').pack(side='left', padx=15)
        
        # Monto pagado - más compacto
        amount_frame = tk.LabelFrame(main_frame, text="Monto Pagado", font=('Arial', 11), 
                                    bg='#f8f9fa', fg='#2c3e50')
        amount_frame.pack(pady=(0,10), fill='x')
        
        entry_frame = tk.Frame(amount_frame, bg='#f8f9fa')
        entry_frame.pack(pady=8)
        
        tk.Label(entry_frame, text="$", font=('Arial', 16, 'bold'), bg='#f8f9fa').pack(side='left')
        amount_entry = tk.Entry(entry_frame, font=('Arial', 16), width=8, justify='center',
                               relief='solid', bd=1)
        amount_entry.pack(side='left', padx=5)
        amount_entry.focus()
        
        # Cambio - más compacto
        change_frame = tk.Frame(main_frame, bg='#e3f2fd', relief='solid', bd=1)
        change_frame.pack(pady=(0,15), fill='x')
        
        change_label = tk.Label(change_frame, text="Ingrese el monto pagado", 
                               font=('Arial', 12, 'bold'), fg='#3498db', bg='#e3f2fd')
        change_label.pack(pady=8)
        
        def calculate_change():
            try:
                amount_text = amount_entry.get().strip()
                if amount_text:
                    amount = float(amount_text)
                    # Convertir total a float para evitar problemas de tipo
                    total_orden = float(self.orden_actual['total'])
                    change = amount - total_orden
                    if change >= 0:
                        change_label.config(text=f"CAMBIO: ${change:.2f}", fg='#27ae60')
                    elif change >= -0.01:
                        change_label.config(text="MONTO EXACTO", fg='#27ae60')
                    else:
                        change_label.config(text="❌ MONTO INSUFICIENTE", fg='#e74c3c')
                else:
                    change_label.config(text="Ingrese el monto pagado", fg='#3498db')
            except ValueError:
                change_label.config(text="❌ MONTO INVÁLIDO", fg='#e74c3c')
            except Exception as e:
                print(f"ERROR en calculate_change: {e}")
                change_label.config(text="❌ ERROR", fg='#e74c3c')
        
        amount_entry.bind('<KeyRelease>', lambda e: calculate_change())
        
        def confirmar_pago():
            try:
                amount_text = amount_entry.get().strip()
                if not amount_text:
                    messagebox.showerror("Error", "Por favor ingrese el monto pagado")
                    amount_entry.focus()
                    return
                
                amount = float(amount_text)
                # Convertir total a float para la comparación
                total_orden = float(self.orden_actual['total'])
                
                if amount < total_orden - 0.01:
                    messagebox.showerror("Error", "Monto insuficiente")
                    amount_entry.focus()
                    return
                
                # Usar el parámetro cliente_nombre que se pasó a la función show_payment_dialog
                self.crear_orden_db(payment_method.get(), amount, cliente_nombre)
                dialog.destroy()
                
            except ValueError:
                messagebox.showerror("Error", "Por favor ingrese un monto válido")
                amount_entry.focus()
            except Exception as e:
                messagebox.showerror("Error", f"Error procesando el pago: {str(e)}")
                print(f"Error en confirmar_pago: {e}")  # Para debug
        
        # Botones - más compactos
        button_frame = tk.Frame(main_frame, bg='#f8f9fa')
        button_frame.pack(pady=(0,5), fill='x')
        
        tk.Button(button_frame, text="CANCELAR", font=('Arial', 11, 'bold'),
                 bg='#95a5a6', fg='white', width=10, height=1,
                 command=dialog.destroy).pack(side='left', padx=5)
        
        tk.Button(button_frame, text="CONFIRMAR PAGO", font=('Arial', 11, 'bold'),
                 bg='#3498db', fg='white', width=15, height=1,
                 command=confirmar_pago).pack(side='right', padx=5)
        
        amount_entry.bind('<Return>', lambda e: confirmar_pago())

    def crear_orden_db(self, metodo_pago, monto_pagado, cliente_nombre=None):
        try:
            print(f"DEBUG: Creando orden - metodo_pago: {metodo_pago}, monto_pagado: {monto_pagado}, cliente_nombre: {cliente_nombre}")
            print(f"DEBUG: Items en orden: {len(self.orden_actual['items'])}")
            print(f"DEBUG: Total orden: {self.orden_actual['total']}")
            
            # Verificar que haya items en la orden
            if not self.orden_actual['items']:
                raise Exception("La orden está vacía")
            
            # Verificar que hay un turno activo
            if not auth.current_turno:
                raise Exception("No hay turno activo")
            
            # Generar número de orden
            import time
            numero_orden = f"ORD{int(time.time())}"
            print(f"DEBUG: Número de orden generado: {numero_orden}")
            
            # Convertir a float para evitar problemas de tipo Decimal
            total_orden = float(self.orden_actual['total'])
            monto_pagado_float = float(monto_pagado)
            
            # Calcular cambio
            cambio = monto_pagado_float - total_orden
            print(f"DEBUG: Cálculo - Total: {total_orden}, Pagado: {monto_pagado_float}, Cambio: {cambio}")
            
            # Cliente ID
            cliente_id = None
            nombre_final = cliente_nombre
            
            if self.cliente_actual:
                cliente_id = self.cliente_actual['id']
                nombre_final = self.cliente_actual['nombre']
            
            print(f"DEBUG: cliente_id: {cliente_id}, nombre_final: {nombre_final}")
            
            # Crear orden
            query = """
            INSERT INTO ordenes (numero_orden, cliente_id, cliente_nombre, tipo_orden,
                               subtotal, total, metodo_pago, monto_pagado, cambio,
                               turno_id, cajero_id, fecha_orden)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """
            valores = (
                numero_orden, cliente_id, nombre_final, self.tipo_orden,
                total_orden, total_orden,
                metodo_pago, monto_pagado_float, cambio,
                auth.current_turno['id'], auth.current_user['id']
            )
            print(f"DEBUG: Valores para inserción: {valores}")
            
            orden_id = db.execute_one(query, valores)
            print(f"DEBUG: ID de orden creada: {orden_id}")
            
            if not orden_id:
                raise Exception("No se pudo crear la orden en la base de datos")
            
            # Crear detalles de la orden
            for i, item in enumerate(self.orden_actual['items']):
                print(f"DEBUG: Insertando item {i+1}: {item['nombre']}")
                
                # Convertir precios a float también
                precio_unitario = float(item['precio'])
                subtotal_item = float(item['subtotal'])
                
                query = """
                INSERT INTO orden_detalles (orden_id, producto_id, cantidad, precio_unitario, subtotal)
                VALUES (%s, %s, %s, %s, %s)
                """
                detalle_result = db.execute_one(query, (
                    orden_id, item['id'], item['cantidad'], precio_unitario, subtotal_item
                ))
                print(f"DEBUG: Detalle insertado con ID: {detalle_result}")
            
            # Imprimir tickets
            print("DEBUG: Generando tickets...")
            ticket_path = printer.print_customer_ticket(orden_id)
            comanda_path = printer.print_kitchen_ticket(orden_id)
            print(f"DEBUG: Tickets generados - Venta: {ticket_path}, Comanda: {comanda_path}")
            
            messagebox.showinfo("Éxito", f"Orden {numero_orden} creada exitosamente\nTickets generados correctamente")
            
            # Limpiar orden actual
            self.orden_actual = {'items': [], 'total': 0.0}
            self.cliente_actual = None
            
            # Volver al menú principal
            self.show_cajero_menu()
            
        except Exception as e:
            error_msg = f"Error creando la orden: {str(e)}"
            print(f"ERROR: {error_msg}")
            messagebox.showerror("Error", error_msg)

    def show_historial(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Historial de Órdenes del Día")
        dialog.geometry("900x650")
        dialog.resizable(True, True)
        dialog.transient(self.root)
        
        # Frame principal
        main_frame = tk.Frame(dialog, bg='#f8f9fa')
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Título
        tk.Label(main_frame, text="📋 HISTORIAL DE ÓRDENES DEL DÍA", font=('Arial', 14, 'bold'), 
                bg='#f8f9fa', fg='#2c3e50').pack(pady=(0,15))
        
        # Obtener órdenes del día
        query = """
        SELECT o.*, c.nombre as cliente_nombre, c.telefono
        FROM ordenes o
        LEFT JOIN clientes c ON o.cliente_id = c.id
        WHERE DATE(o.fecha_orden) = CURDATE() AND o.turno_id = %s
        ORDER BY o.fecha_orden DESC
        """
        ordenes = db.execute_query(query, (auth.current_turno['id'],))
        
        # Frame para treeview
        tree_frame = tk.Frame(main_frame)
        tree_frame.pack(fill='both', expand=True, pady=(0,15))
        
        # Crear treeview con scrollbar
        columns = ('numero_orden', 'cliente', 'tipo', 'total', 'pago', 'hora')
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        
        tree.heading('numero_orden', text='# Orden')
        tree.heading('cliente', text='Cliente')
        tree.heading('tipo', text='Tipo')
        tree.heading('total', text='Total')
        tree.heading('pago', text='Método Pago')
        tree.heading('hora', text='Hora')
        
        tree.column('numero_orden', width=120)
        tree.column('cliente', width=180)
        tree.column('tipo', width=100)
        tree.column('total', width=100)
        tree.column('pago', width=100)
        tree.column('hora', width=80)
        
        # Scrollbar para treeview
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Llenar datos
        for orden in ordenes:
            tree.insert('', 'end', values=(
                orden['numero_orden'],
                orden['cliente_nombre'] or orden['cliente_nombre'] or 'Cliente Mostrador',
                orden['tipo_orden'].title(),
                f"${orden['total']:.2f}",
                orden['metodo_pago'].title(),
                orden['fecha_orden'].strftime('%H:%M')
            ), tags=(orden['id'],))
        
        tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Frame para botones
        btn_frame = tk.Frame(main_frame, bg='#f8f9fa')
        btn_frame.pack(pady=(0,10))
        
        def get_selected_orden_id():
            selection = tree.selection()
            if selection:
                return tree.item(selection[0])['tags'][0]
            return None
        
        def preview_orden():
            orden_id = get_selected_orden_id()
            if not orden_id:
                messagebox.showwarning("Advertencia", "Por favor seleccione una orden")
                return
            self.show_orden_preview(orden_id)
        
        def reimprimir_venta():
            orden_id = get_selected_orden_id()
            if not orden_id:
                messagebox.showwarning("Advertencia", "Por favor seleccione una orden")
                return
            ticket_path = printer.print_customer_ticket(orden_id)
            if ticket_path:
                messagebox.showinfo("Éxito", f"Ticket reimpreso\nGuardado en: {ticket_path}")
        
        def reimprimir_comanda():
            orden_id = get_selected_orden_id()
            if not orden_id:
                messagebox.showwarning("Advertencia", "Por favor seleccione una orden")
                return
            comanda_path = printer.print_kitchen_ticket(orden_id)
            if comanda_path:
                messagebox.showinfo("Éxito", f"Comanda reimpresa\nGuardada en: {comanda_path}")
        
        # Botones organizados
        tk.Button(btn_frame, text="👁️ PREVISUALIZAR", font=('Arial', 11, 'bold'),
                 bg='#3498db', fg='white', width=15, height=1,
                 command=preview_orden).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="🎫 REIMPRIMIR VENTA", font=('Arial', 11, 'bold'),
                 bg='#2980b9', fg='white', width=18, height=1,
                 command=reimprimir_venta).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="📋 REIMPRIMIR COMANDA", font=('Arial', 11, 'bold'),
                 bg='#5dade2', fg='white', width=20, height=1,
                 command=reimprimir_comanda).pack(side='left', padx=5)
        
        def eliminar_orden():
            orden_id = get_selected_orden_id()
            if not orden_id:
                messagebox.showwarning("Advertencia", "Por favor seleccione una orden")
                return
            
            # Obtener información de la orden antes de eliminar
            query = "SELECT numero_orden, total FROM ordenes WHERE id = %s"
            orden_info = db.execute_one(query, (orden_id,))
            if not orden_info:
                messagebox.showerror("Error", "Orden no encontrada")
                return
            
            # Confirmar acción
            respuesta = messagebox.askyesno("Confirmar Eliminación", 
                f"⚠️ ATENCIÓN: Esta acción es IRREVERSIBLE\n\n"
                f"Orden: {orden_info['numero_orden']}\n"
                f"Total: ${float(orden_info['total']):.2f}\n\n"
                f"¿Está seguro de que desea eliminar esta orden?\n"
                f"Se eliminará completamente del sistema y no aparecerá en reportes.")
            
            if not respuesta:
                return
            
            # Pedir credenciales de administrador
            admin_user = self.admin_login_dialog("Eliminar Orden")
            if not admin_user:
                return
            
            # Proceder con la eliminación
            self.eliminar_orden_completa(orden_id, orden_info, dialog, tree)
        
        tk.Button(btn_frame, text="🗑️ ELIMINAR ORDEN", font=('Arial', 11, 'bold'),
                 bg='#e74c3c', fg='white', width=18, height=1,
                 command=eliminar_orden).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="CERRAR", font=('Arial', 11, 'bold'),
                 bg='#95a5a6', fg='white', width=10, height=1,
                 command=dialog.destroy).pack(side='right', padx=5)
        
    def show_orden_preview(self, orden_id):
        try:
            # Obtener información completa de la orden
            query = """
            SELECT o.*, c.nombre as cliente_nombre, c.telefono, c.direccion,
                   u.nombre as cajero_nombre
            FROM ordenes o
            LEFT JOIN clientes c ON o.cliente_id = c.id
            LEFT JOIN usuarios u ON o.cajero_id = u.id
            WHERE o.id = %s
            """
            orden = db.execute_one(query, (orden_id,))
            
            if not orden:
                messagebox.showerror("Error", "Orden no encontrada")
                return
            
            # Obtener detalles de productos
            query = """
            SELECT od.*, p.nombre as producto_nombre
            FROM orden_detalles od
            JOIN productos p ON od.producto_id = p.id
            WHERE od.orden_id = %s
            ORDER BY od.id
            """
            detalles = db.execute_query(query, (orden_id,))
            
            # Crear ventana de previsualización
            preview_dialog = tk.Toplevel(self.root)
            preview_dialog.title(f"Previsualización - Orden {orden['numero_orden']}")
            preview_dialog.geometry("500x650")
            preview_dialog.resizable(False, False)
            preview_dialog.transient(self.root)
            preview_dialog.grab_set()
            
            # Configurar color de fondo
            preview_dialog.configure(bg='#f8f9fa')
            
            # Frame principal con scroll
            main_frame = tk.Frame(preview_dialog, bg='#f8f9fa')
            main_frame.pack(fill='both', expand=True, padx=15, pady=15)
            
            # Título
            tk.Label(main_frame, text="🎫 PREVISUALIZACIÓN DE ORDEN", font=('Arial', 14, 'bold'), 
                    bg='#f8f9fa', fg='#2c3e50').pack(pady=(0,15))
            
            # Frame para contenido con scroll
            canvas = tk.Canvas(main_frame, bg='white', relief='solid', bd=1)
            scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg='white')
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # Contenido de la orden
            content_frame = tk.Frame(scrollable_frame, bg='white')
            content_frame.pack(fill='both', expand=True, padx=20, pady=20)
            
            # Información del encabezado
            header_frame = tk.LabelFrame(content_frame, text="Información General", font=('Arial', 11, 'bold'),
                                       bg='white', fg='#2c3e50')
            header_frame.pack(fill='x', pady=(0,15))
            
            info_frame = tk.Frame(header_frame, bg='white')
            info_frame.pack(fill='x', padx=10, pady=10)
            
            # Información en dos columnas
            # Columna izquierda
            left_col = tk.Frame(info_frame, bg='white')
            left_col.pack(side='left', fill='both', expand=True)
            
            tk.Label(left_col, text=f"📋 Orden: {orden['numero_orden']}", font=('Arial', 11, 'bold'), 
                    bg='white', fg='#3498db').pack(anchor='w', pady=2)
            tk.Label(left_col, text=f"📅 Fecha: {orden['fecha_orden'].strftime('%d/%m/%Y %H:%M')}", 
                    font=('Arial', 10), bg='white').pack(anchor='w', pady=1)
            tk.Label(left_col, text=f"👤 Cajero: {orden['cajero_nombre']}", 
                    font=('Arial', 10), bg='white').pack(anchor='w', pady=1)
            tk.Label(left_col, text=f"🏷️ Tipo: {orden['tipo_orden'].title()}", 
                    font=('Arial', 10), bg='white').pack(anchor='w', pady=1)
            
            # Columna derecha
            right_col = tk.Frame(info_frame, bg='white')
            right_col.pack(side='right', fill='both', expand=True)
            
            if orden['cliente_nombre'] and orden['cliente_nombre'] != 'Cliente Mostrador':
                tk.Label(right_col, text=f"👥 Cliente: {orden['cliente_nombre']}", 
                        font=('Arial', 10), bg='white').pack(anchor='w', pady=1)
                if orden['telefono']:
                    tk.Label(right_col, text=f"📱 Tel: {orden['telefono']}", 
                            font=('Arial', 10), bg='white').pack(anchor='w', pady=1)
                if orden['direccion']:
                    tk.Label(right_col, text=f"📍 Dir: {orden['direccion']}", 
                            font=('Arial', 10), bg='white', wraplength=200).pack(anchor='w', pady=1)
            else:
                tk.Label(right_col, text="👥 Cliente: Mostrador", 
                        font=('Arial', 10), bg='white').pack(anchor='w', pady=1)
            
            tk.Label(right_col, text=f"💳 Pago: {orden['metodo_pago'].title()}", 
                    font=('Arial', 10), bg='white').pack(anchor='w', pady=1)
            
            # Productos
            productos_frame = tk.LabelFrame(content_frame, text="Productos Ordenados", font=('Arial', 11, 'bold'),
                                          bg='white', fg='#2c3e50')
            productos_frame.pack(fill='x', pady=(0,15))
            
            # Headers de tabla
            table_header = tk.Frame(productos_frame, bg='#3498db')
            table_header.pack(fill='x', padx=10, pady=(10,0))
            
            tk.Label(table_header, text="Cant.", font=('Arial', 10, 'bold'), bg='#3498db', fg='white', width=6).pack(side='left')
            tk.Label(table_header, text="Producto", font=('Arial', 10, 'bold'), bg='#3498db', fg='white', width=25).pack(side='left')
            tk.Label(table_header, text="Precio", font=('Arial', 10, 'bold'), bg='#3498db', fg='white', width=10).pack(side='left')
            tk.Label(table_header, text="Subtotal", font=('Arial', 10, 'bold'), bg='#3498db', fg='white', width=10).pack(side='left')
            
            # Productos
            for i, detalle in enumerate(detalles):
                bg_color = '#f8f9fa' if i % 2 == 0 else 'white'
                product_row = tk.Frame(productos_frame, bg=bg_color)
                product_row.pack(fill='x', padx=10)
                
                tk.Label(product_row, text=str(detalle['cantidad']), font=('Arial', 10), 
                        bg=bg_color, width=6).pack(side='left', pady=2)
                tk.Label(product_row, text=detalle['producto_nombre'], font=('Arial', 10), 
                        bg=bg_color, width=25, anchor='w').pack(side='left', pady=2)
                tk.Label(product_row, text=f"${float(detalle['precio_unitario']):.2f}", font=('Arial', 10), 
                        bg=bg_color, width=10).pack(side='left', pady=2)
                tk.Label(product_row, text=f"${float(detalle['subtotal']):.2f}", font=('Arial', 10), 
                        bg=bg_color, width=10).pack(side='left', pady=2)
            
            # Total y pago
            totales_frame = tk.LabelFrame(content_frame, text="Totales y Pago", font=('Arial', 11, 'bold'),
                                        bg='white', fg='#2c3e50')
            totales_frame.pack(fill='x', pady=(0,15))
            
            totales_content = tk.Frame(totales_frame, bg='white')
            totales_content.pack(fill='x', padx=20, pady=15)
            
            # Total
            total_frame = tk.Frame(totales_content, bg='#e8f5e8', relief='solid', bd=1)
            total_frame.pack(fill='x', pady=2)
            tk.Label(total_frame, text=f"💰 TOTAL: ${float(orden['total']):.2f}", 
                    font=('Arial', 14, 'bold'), bg='#e8f5e8', fg='#27ae60').pack(pady=8)
            
            # Pago
            tk.Label(totales_content, text=f"Método de pago: {orden['metodo_pago'].title()}", 
                    font=('Arial', 11), bg='white').pack(anchor='w', pady=2)
            tk.Label(totales_content, text=f"Monto pagado: ${float(orden['monto_pagado']):.2f}", 
                    font=('Arial', 11), bg='white').pack(anchor='w', pady=2)
            
            if float(orden['cambio']) > 0:
                tk.Label(totales_content, text=f"Cambio entregado: ${float(orden['cambio']):.2f}", 
                        font=('Arial', 11), bg='white', fg='#3498db').pack(anchor='w', pady=2)
            
            # Empacar canvas y scrollbar
            canvas.pack(side='left', fill='both', expand=True)
            scrollbar.pack(side='right', fill='y')
            
            # Botón cerrar
            tk.Button(main_frame, text="CERRAR", font=('Arial', 11, 'bold'),
                     bg='#95a5a6', fg='white', width=15, height=1,
                     command=preview_dialog.destroy).pack(pady=(10,0))
            
            # Configurar scroll con rueda del mouse
            def _on_mousewheel(event):
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            
            # Limpiar binding cuando se cierre la ventana
            def on_closing():
                canvas.unbind_all("<MouseWheel>")
                preview_dialog.destroy()
            
            preview_dialog.protocol("WM_DELETE_WINDOW", on_closing)
            
        except Exception as e:
            print(f"ERROR en show_orden_preview: {e}")
            messagebox.showerror("Error", f"Error mostrando previsualización: {str(e)}")

    def eliminar_orden_completa(self, orden_id, orden_info, parent_dialog, tree):
        try:
            print(f"DEBUG: Iniciando eliminación de orden {orden_id}")
            
            # Crear ventana de confirmación final
            confirm_dialog = tk.Toplevel(self.root)
            confirm_dialog.title("Confirmación Final - Eliminar Orden")
            confirm_dialog.geometry("450x400")
            confirm_dialog.resizable(False, False)
            confirm_dialog.transient(parent_dialog)
            confirm_dialog.grab_set()
            
            # Configurar color de fondo
            confirm_dialog.configure(bg='#f8f9fa')
            
            # Frame principal
            main_frame = tk.Frame(confirm_dialog, bg='#f8f9fa')
            main_frame.pack(fill='both', expand=True, padx=15, pady=15)
            
            # Título de advertencia
            tk.Label(main_frame, text="⚠️ ELIMINACIÓN DE ORDEN", font=('Arial', 14, 'bold'), 
                    bg='#f8f9fa', fg='#e74c3c').pack(pady=(0,15))
            
            # Frame de advertencia
            warning_frame = tk.LabelFrame(main_frame, text="ADVERTENCIA IMPORTANTE", font=('Arial', 11, 'bold'),
                                        bg='#f8f9fa', fg='#e74c3c')
            warning_frame.pack(fill='x', pady=(0,15))
            
            warning_text = """
Esta acción eliminará COMPLETAMENTE la orden del sistema:

• Se eliminará la orden principal
• Se eliminarán todos los productos de la orden  
• No aparecerá en ningún reporte o historial
• No se podrá recuperar después de eliminar
• Puede afectar los cálculos si ya se hizo corte de caja

SOLO use esta función para corregir errores graves.
            """
            
            tk.Label(warning_frame, text=warning_text, font=('Arial', 10), 
                    bg='#f8f9fa', fg='#2c3e50', justify='left').pack(padx=10, pady=10)
            
            # Información de la orden
            info_frame = tk.LabelFrame(main_frame, text="Información de la Orden", font=('Arial', 11, 'bold'),
                                     bg='#f8f9fa', fg='#2c3e50')
            info_frame.pack(fill='x', pady=(0,15))
            
            info_content = tk.Frame(info_frame, bg='#f8f9fa')
            info_content.pack(fill='x', padx=10, pady=10)
            
            tk.Label(info_content, text=f"📋 Orden: {orden_info['numero_orden']}", 
                    font=('Arial', 11, 'bold'), bg='#f8f9fa', fg='#3498db').pack(anchor='w', pady=2)
            tk.Label(info_content, text=f"💰 Total: ${float(orden_info['total']):.2f}", 
                    font=('Arial', 11), bg='#f8f9fa').pack(anchor='w', pady=2)
            tk.Label(info_content, text=f"👤 Turno: #{auth.current_turno['id'] if auth.current_turno else 'N/A'}", 
                    font=('Arial', 11), bg='#f8f9fa').pack(anchor='w', pady=2)
            
            # Razón de eliminación
            reason_frame = tk.LabelFrame(main_frame, text="Razón de Eliminación (Obligatorio)", font=('Arial', 11, 'bold'),
                                       bg='#f8f9fa', fg='#2c3e50')
            reason_frame.pack(fill='x', pady=(0,15))
            
            reason_entry = tk.Text(reason_frame, height=3, font=('Arial', 10), relief='solid', bd=1)
            reason_entry.pack(fill='x', padx=10, pady=10)
            reason_entry.insert('1.0', 'Motivo: ')
            
            def ejecutar_eliminacion():
                reason = reason_entry.get('1.0', tk.END).strip()
                if len(reason) < 10 or reason == 'Motivo:':
                    messagebox.showerror("Error", "Por favor proporcione una razón detallada para la eliminación (mínimo 10 caracteres)")
                    reason_entry.focus()
                    return
                
                try:
                    print(f"DEBUG: Eliminando orden {orden_id} - Razón: {reason}")
                    
                    # Iniciar transacción para eliminar todo
                    # Primero eliminar detalles de la orden
                    query = "DELETE FROM orden_detalles WHERE orden_id = %s"
                    result_detalles = db.execute_query(query, (orden_id,))
                    print(f"DEBUG: Detalles eliminados: {result_detalles}")
                    
                    # Luego eliminar la orden principal
                    query = "DELETE FROM ordenes WHERE id = %s"
                    result_orden = db.execute_query(query, (orden_id,))
                    print(f"DEBUG: Orden eliminada: {result_orden}")
                    
                    if result_orden:
                        # Registrar la eliminación en un log (opcional - podrías crear tabla de auditoría)
                        print(f"AUDIT: Orden {orden_info['numero_orden']} eliminada por admin {auth.current_user['nombre']} - Razón: {reason}")
                        
                        messagebox.showinfo("Éxito", 
                            f"Orden {orden_info['numero_orden']} eliminada exitosamente\n\n"
                            f"La orden ya no aparecerá en reportes ni historiales.")
                        
                        # Cerrar diálogos
                        confirm_dialog.destroy()
                        
                        # Actualizar el historial eliminando la fila
                        selection = tree.selection()
                        if selection:
                            tree.delete(selection[0])
                    else:
                        messagebox.showerror("Error", "No se pudo eliminar la orden de la base de datos")
                        
                except Exception as e:
                    print(f"ERROR eliminando orden: {e}")
                    messagebox.showerror("Error", f"Error eliminando orden: {str(e)}")
            
            def cancelar_eliminacion():
                confirm_dialog.destroy()
            
            # Botones
            button_frame = tk.Frame(main_frame, bg='#f8f9fa')
            button_frame.pack(fill='x', pady=(0,5))
            
            tk.Button(button_frame, text="CANCELAR", font=('Arial', 11, 'bold'),
                     bg='#95a5a6', fg='white', width=12, height=1,
                     command=cancelar_eliminacion).pack(side='left', padx=5)
            
            tk.Button(button_frame, text="⚠️ ELIMINAR DEFINITIVAMENTE", font=('Arial', 11, 'bold'),
                     bg='#e74c3c', fg='white', width=25, height=1,
                     command=ejecutar_eliminacion).pack(side='right', padx=5)
            
            reason_entry.focus()
            reason_entry.mark_set(tk.INSERT, '1.8')  # Posicionar cursor después de "Motivo: "
            
        except Exception as e:
            print(f"ERROR en eliminar_orden_completa: {e}")
            messagebox.showerror("Error", f"Error preparando eliminación: {str(e)}")

    def show_arqueo(self):
        # Pedir credenciales de administrador
        admin_dialog = self.admin_login_dialog("Arqueo de Caja")
        if not admin_dialog:
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Arqueo de Caja")
        dialog.geometry("380x280")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Configurar color de fondo
        dialog.configure(bg='#f8f9fa')
        
        # Frame principal compacto
        main_frame = tk.Frame(dialog, bg='#f8f9fa')
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        tk.Label(main_frame, text="💰 ARQUEO DE CAJA", font=('Arial', 14, 'bold'), 
                bg='#f8f9fa', fg='#2c3e50').pack(pady=(0,8))
        
        tk.Label(main_frame, text="Retirar efectivo durante el turno", font=('Arial', 10), 
                bg='#f8f9fa', fg='#7f8c8d').pack(pady=(0,15))
        
        # Frame para monto - más compacto
        monto_frame = tk.LabelFrame(main_frame, text="Monto a Retirar", font=('Arial', 11),
                                   bg='#f8f9fa', fg='#2c3e50')
        monto_frame.pack(pady=(0,15), fill='x')
        
        entry_frame = tk.Frame(monto_frame, bg='#f8f9fa')
        entry_frame.pack(pady=10)
        
        tk.Label(entry_frame, text="$", font=('Arial', 16, 'bold'), bg='#f8f9fa').pack(side='left')
        amount_entry = tk.Entry(entry_frame, font=('Arial', 16), width=8, justify='center',
                               relief='solid', bd=1)
        amount_entry.pack(side='left', padx=5)
        
        def procesar_arqueo():
            try:
                amount_text = amount_entry.get().strip()
                if not amount_text:
                    messagebox.showerror("Error", "Por favor ingrese el monto a retirar")
                    amount_entry.focus()
                    return
                
                monto = float(amount_text)
                if monto <= 0:
                    messagebox.showerror("Error", "El monto debe ser mayor a 0")
                    amount_entry.focus()
                    return
                
                query = """
                INSERT INTO arqueos (turno_id, monto, administrador_id)
                VALUES (%s, %s, %s)
                """
                result = db.execute_one(query, (
                    auth.current_turno['id'], monto, admin_dialog['id']
                ))
                
                if result:
                    messagebox.showinfo("Éxito", f"Arqueo registrado exitosamente\nMonto retirado: ${monto:.2f}")
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", "No se pudo registrar el arqueo")
            except ValueError:
                messagebox.showerror("Error", "Por favor ingrese un monto válido")
                amount_entry.focus()
        
        # Botones - más compactos
        button_frame = tk.Frame(main_frame, bg='#f8f9fa')
        button_frame.pack(pady=(0,5), fill='x')
        
        tk.Button(button_frame, text="CANCELAR", font=('Arial', 11, 'bold'),
                 bg='#95a5a6', fg='white', width=10, height=1,
                 command=dialog.destroy).pack(side='left', padx=5)
        
        tk.Button(button_frame, text="PROCESAR ARQUEO", font=('Arial', 11, 'bold'),
                 bg='#3498db', fg='white', width=15, height=1,
                 command=procesar_arqueo).pack(side='right', padx=5)
        
        amount_entry.focus()
        amount_entry.bind('<Return>', lambda e: procesar_arqueo())

    def show_corte_caja(self):
        # Pedir credenciales de administrador
        admin_user = self.admin_login_dialog("Corte de Caja")
        if not admin_user:
            return
        
        self.procesar_corte_caja(admin_user)

    def procesar_corte_caja(self, admin_user):
        dialog = tk.Toplevel(self.root)
        dialog.title("Corte de Caja")
        dialog.geometry("420x350")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Configurar color de fondo
        dialog.configure(bg='#f8f9fa')
        
        # Frame principal
        main_frame = tk.Frame(dialog, bg='#f8f9fa')
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        tk.Label(main_frame, text="🏦 CORTE DE CAJA", font=('Arial', 14, 'bold'), 
                bg='#f8f9fa', fg='#2c3e50').pack(pady=(0,15))
        
        # Paso 1: Cajero ingresa cantidades
        step1_frame = tk.LabelFrame(main_frame, text="Paso 1: Cantidades Finales", font=('Arial', 11),
                                   bg='#f8f9fa', fg='#2c3e50')
        step1_frame.pack(fill='x', pady=(0,15))
        
        tk.Label(step1_frame, text="Ingrese las cantidades que tiene al final del turno:", 
                font=('Arial', 10), bg='#f8f9fa', fg='#7f8c8d').pack(pady=(10,15))
        
        # Efectivo
        efectivo_frame = tk.Frame(step1_frame, bg='#f8f9fa')
        efectivo_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(efectivo_frame, text="💵 Efectivo en caja:", font=('Arial', 11), 
                bg='#f8f9fa').pack(side='left')
        tk.Label(efectivo_frame, text="$", font=('Arial', 12, 'bold'), 
                bg='#f8f9fa').pack(side='right', padx=(5,0))
        efectivo_entry = tk.Entry(efectivo_frame, font=('Arial', 11), width=10, 
                                 relief='solid', bd=1, justify='right')
        efectivo_entry.pack(side='right')
        
        # Tarjeta
        tarjeta_frame = tk.Frame(step1_frame, bg='#f8f9fa')
        tarjeta_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(tarjeta_frame, text="💳 Total tarjetas:", font=('Arial', 11), 
                bg='#f8f9fa').pack(side='left')
        tk.Label(tarjeta_frame, text="$", font=('Arial', 12, 'bold'), 
                bg='#f8f9fa').pack(side='right', padx=(5,0))
        tarjeta_entry = tk.Entry(tarjeta_frame, font=('Arial', 11), width=10, 
                                relief='solid', bd=1, justify='right')
        tarjeta_entry.pack(side='right')
        
        # Advertencia
        warning_frame = tk.Frame(step1_frame, bg='#fff2cd', relief='solid', bd=1)
        warning_frame.pack(fill='x', padx=10, pady=(15,10))
        
        warning_label = tk.Label(warning_frame, 
                               text="⚠️ PRECAUCIÓN: Cualquier faltante será cobrado",
                               font=('Arial', 10, 'bold'), bg='#fff2cd', fg='#856404')
        warning_label.pack(pady=8)
        
        def paso2():
            try:
                efectivo_text = efectivo_entry.get().strip()
                tarjeta_text = tarjeta_entry.get().strip()
                
                if not efectivo_text:
                    messagebox.showerror("Error", "Por favor ingrese el monto de efectivo")
                    efectivo_entry.focus()
                    return
                
                if not tarjeta_text:
                    messagebox.showerror("Error", "Por favor ingrese el monto de tarjetas")
                    tarjeta_entry.focus()
                    return
                
                efectivo = float(efectivo_text)
                tarjeta = float(tarjeta_text)
                
                if efectivo < 0:
                    messagebox.showerror("Error", "El monto de efectivo no puede ser negativo")
                    efectivo_entry.focus()
                    return
                
                if tarjeta < 0:
                    messagebox.showerror("Error", "El monto de tarjetas no puede ser negativo")
                    tarjeta_entry.focus()
                    return
                
                print(f"DEBUG: Procediendo a paso 2 con efectivo: {efectivo}, tarjeta: {tarjeta}")
                self.show_corte_paso2(dialog, admin_user, efectivo, tarjeta)
                
            except ValueError:
                messagebox.showerror("Error", "Por favor ingrese montos válidos (solo números)")
        
        # Botones
        button_frame = tk.Frame(main_frame, bg='#f8f9fa')
        button_frame.pack(fill='x', pady=(0,5))
        
        tk.Button(button_frame, text="CANCELAR", font=('Arial', 11, 'bold'),
                 bg='#95a5a6', fg='white', width=12, height=1,
                 command=dialog.destroy).pack(side='left', padx=5)
        
        tk.Button(button_frame, text="CONTINUAR", font=('Arial', 11, 'bold'),
                 bg='#3498db', fg='white', width=12, height=1,
                 command=paso2).pack(side='right', padx=5)
        
        efectivo_entry.focus()
        efectivo_entry.bind('<Return>', lambda e: tarjeta_entry.focus())
        tarjeta_entry.bind('<Return>', lambda e: paso2())

    def show_corte_paso2(self, parent_dialog, admin_user, efectivo_cajero, tarjeta_cajero):
        parent_dialog.destroy()
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Corte de Caja - Confirmación")
        dialog.geometry("520x650")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Configurar color de fondo
        dialog.configure(bg='#f8f9fa')
        
        # Frame principal
        main_frame = tk.Frame(dialog, bg='#f8f9fa')
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        tk.Label(main_frame, text="💰 CONFIRMACIÓN DE CORTE", font=('Arial', 14, 'bold'), 
                bg='#f8f9fa', fg='#2c3e50').pack(pady=(0,15))
        
        try:
            print("DEBUG: Iniciando cálculo de corte de caja")
            print(f"DEBUG: Turno ID: {auth.current_turno['id'] if auth.current_turno else 'None'}")
            
            # Calcular totales esperados - convertir todo a float
            # Obtener total de ventas
            query = """
            SELECT 
                COALESCE(SUM(CASE WHEN metodo_pago = 'efectivo' THEN total ELSE 0 END), 0) as ventas_efectivo,
                COALESCE(SUM(CASE WHEN metodo_pago = 'tarjeta' THEN total ELSE 0 END), 0) as ventas_tarjeta,
                COALESCE(SUM(total), 0) as total_ventas
            FROM ordenes 
            WHERE turno_id = %s
            """
            ventas = db.execute_one(query, (auth.current_turno['id'],))
            print(f"DEBUG: Ventas obtenidas: {ventas}")
            
            # Convertir a float para evitar problemas de tipo
            ventas_efectivo = float(ventas['ventas_efectivo']) if ventas else 0.0
            ventas_tarjeta = float(ventas['ventas_tarjeta']) if ventas else 0.0
            total_ventas = float(ventas['total_ventas']) if ventas else 0.0
            
            # Obtener arqueos
            query = "SELECT COALESCE(SUM(monto), 0) as total_arqueos FROM arqueos WHERE turno_id = %s"
            arqueos_result = db.execute_one(query, (auth.current_turno['id'],))
            total_arqueos = float(arqueos_result['total_arqueos']) if arqueos_result else 0.0
            
            print(f"DEBUG: Arqueos: {total_arqueos}")
            
            # Obtener fondo inicial y convertir a float
            fondo_inicial = float(auth.current_turno['fondo_inicial'])
            print(f"DEBUG: Fondo inicial: {fondo_inicial}")
            
            # Calcular esperados
            efectivo_esperado = fondo_inicial + ventas_efectivo - total_arqueos
            tarjeta_esperada = ventas_tarjeta
            total_esperado = efectivo_esperado + tarjeta_esperada
            total_real = efectivo_cajero + tarjeta_cajero
            diferencia = total_esperado - total_real
            
            print(f"DEBUG: Cálculos - Efectivo esperado: {efectivo_esperado}, Tarjeta esperada: {tarjeta_esperada}")
            print(f"DEBUG: Total esperado: {total_esperado}, Total real: {total_real}, Diferencia: {diferencia}")
            
            # Mostrar resumen
            info_frame = tk.LabelFrame(main_frame, text="Resumen del Turno", font=('Arial', 12), 
                                     bg='#f8f9fa', fg='#2c3e50')
            info_frame.pack(fill='both', expand=True, pady=(0,15))
            
            # Crear texto del resumen
            info_text = f"""INFORMACIÓN DEL TURNO:
Turno #{auth.current_turno['id']}
Fondo inicial: ${fondo_inicial:.2f}
Ventas efectivo: ${ventas_efectivo:.2f}
Ventas tarjeta: ${ventas_tarjeta:.2f}
Total arqueos: ${total_arqueos:.2f}

CANTIDADES ESPERADAS:
Efectivo esperado: ${efectivo_esperado:.2f}
Tarjeta esperada: ${tarjeta_esperada:.2f}
Total esperado: ${total_esperado:.2f}

CANTIDADES REPORTADAS:
Efectivo reportado: ${efectivo_cajero:.2f}
Tarjeta reportada: ${tarjeta_cajero:.2f}
Total reportado: ${total_real:.2f}

DIFERENCIA: ${diferencia:.2f}"""

            if diferencia > 0.01:
                info_text += f"\n\n⚠️ FALTANTE DE: ${diferencia:.2f}"
            elif diferencia < -0.01:
                info_text += f"\n\n✅ SOBRANTE DE: ${abs(diferencia):.2f}"
            else:
                info_text += f"\n\n✅ CORTE CUADRADO"
            
            text_widget = tk.Text(info_frame, height=18, width=55, font=('Arial', 10),
                                 wrap=tk.WORD, relief='solid', bd=1)
            text_widget.insert('1.0', info_text)
            text_widget.config(state='disabled')
            text_widget.pack(padx=10, pady=10, fill='both', expand=True)
            
            # Pedir confirmación del administrador
            admin_frame = tk.LabelFrame(main_frame, text="Confirmación de Administrador", font=('Arial', 11),
                                       bg='#f8f9fa', fg='#2c3e50')
            admin_frame.pack(fill='x', pady=(0,10))
            
            tk.Label(admin_frame, text="Contraseña de administrador:", font=('Arial', 10), 
                    bg='#f8f9fa').pack(anchor='w', padx=10, pady=(10,2))
            
            admin_pass_entry = tk.Entry(admin_frame, show='*', font=('Arial', 11), relief='solid', bd=1)
            admin_pass_entry.pack(fill='x', padx=10, pady=(0,10))
            
            def finalizar_corte():
                try:
                    password = admin_pass_entry.get().strip()
                    if not password:
                        messagebox.showerror("Error", "Por favor ingrese la contraseña")
                        admin_pass_entry.focus()
                        return
                    
                    # Verificar contraseña del administrador nuevamente
                    query = "SELECT * FROM usuarios WHERE id = %s AND password = %s"
                    admin_check = db.execute_one(query, (admin_user['id'], password))
                    
                    if not admin_check:
                        messagebox.showerror("Error", "Contraseña de administrador incorrecta")
                        admin_pass_entry.focus()
                        return
                    
                    print("DEBUG: Contraseña verificada, procediendo a cerrar turno...")
                    print(f"DEBUG: Valores - Efectivo: {efectivo_cajero}, Tarjeta: {tarjeta_cajero}")
                    
                    # Guardar el ID del turno antes de cerrarlo
                    turno_id_para_corte = auth.current_turno['id'] if auth.current_turno else None
                    
                    # Cerrar turno
                    resultado_cerrar = auth.cerrar_turno(efectivo_cajero, tarjeta_cajero)
                    print(f"DEBUG: Resultado cerrar_turno: {resultado_cerrar}")
                    
                    if resultado_cerrar:
                        # Imprimir corte
                        print(f"DEBUG: Imprimiendo corte para turno: {turno_id_para_corte}")
                        
                        if turno_id_para_corte:
                            corte_path = printer.print_corte_caja(turno_id_para_corte)
                            print(f"DEBUG: Corte impreso en: {corte_path}")
                        
                        messagebox.showinfo("Éxito", "Corte de caja realizado correctamente\nSesión cerrada automáticamente")
                        dialog.destroy()
                        
                        # Hacer logout después del corte
                        auth.logout()
                        self.show_login()
                    else:
                        messagebox.showerror("Error", "No se pudo procesar el corte de caja.\nVerifique la conexión a la base de datos.")
                        
                except Exception as e:
                    print(f"ERROR en finalizar_corte: {e}")
                    import traceback
                    traceback.print_exc()
                    messagebox.showerror("Error", f"Error finalizando corte: {str(e)}")
            
            # Botones
            button_frame = tk.Frame(main_frame, bg='#f8f9fa')
            button_frame.pack(fill='x', pady=(0,5))
            
            tk.Button(button_frame, text="CANCELAR", font=('Arial', 11, 'bold'),
                     bg='#95a5a6', fg='white', width=12, height=1,
                     command=dialog.destroy).pack(side='left', padx=5)
            
            tk.Button(button_frame, text="FINALIZAR CORTE", font=('Arial', 11, 'bold'),
                     bg='#3498db', fg='white', width=15, height=1,
                     command=finalizar_corte).pack(side='right', padx=5)
            
            admin_pass_entry.focus()
            admin_pass_entry.bind('<Return>', lambda e: finalizar_corte())
            
        except Exception as e:
            print(f"ERROR en show_corte_paso2: {e}")
            error_frame = tk.Frame(main_frame, bg='#f8f9fa')
            error_frame.pack(fill='both', expand=True)
            
            tk.Label(error_frame, text="❌ ERROR CALCULANDO CORTE", font=('Arial', 14, 'bold'),
                    bg='#f8f9fa', fg='#e74c3c').pack(pady=20)
            
            tk.Label(error_frame, text=f"Error: {str(e)}", font=('Arial', 10),
                    bg='#f8f9fa', fg='#7f8c8d', wraplength=400).pack(pady=10)
            
            tk.Button(error_frame, text="CERRAR", font=('Arial', 11, 'bold'),
                     bg='#95a5a6', fg='white', command=dialog.destroy).pack(pady=20)

    def admin_login_dialog(self, title):
        dialog = tk.Toplevel(self.root)
        dialog.title(f"{title} - Login Administrador")
        dialog.geometry("350x250")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Configurar color de fondo
        dialog.configure(bg='#f8f9fa')
        
        result = None
        
        # Frame principal compacto
        main_frame = tk.Frame(dialog, bg='#f8f9fa')
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        tk.Label(main_frame, text="🔐 CREDENCIALES DE ADMINISTRADOR", font=('Arial', 12, 'bold'), 
                bg='#f8f9fa', fg='#2c3e50').pack(pady=(0,15))
        
        # Campos
        fields_frame = tk.Frame(main_frame, bg='#f8f9fa')
        fields_frame.pack(pady=(0,15))
        
        tk.Label(fields_frame, text="Usuario:", font=('Arial', 11), 
                bg='#f8f9fa', fg='#2c3e50').grid(row=0, column=0, sticky='w', pady=6)
        user_entry = tk.Entry(fields_frame, font=('Arial', 11), width=15, relief='solid', bd=1)
        user_entry.grid(row=0, column=1, pady=6, padx=8)
        
        tk.Label(fields_frame, text="Contraseña:", font=('Arial', 11), 
                bg='#f8f9fa', fg='#2c3e50').grid(row=1, column=0, sticky='w', pady=6)
        pass_entry = tk.Entry(fields_frame, show='*', font=('Arial', 11), width=15, relief='solid', bd=1)
        pass_entry.grid(row=1, column=1, pady=6, padx=8)
        
        def verificar():
            nonlocal result
            username = user_entry.get()
            password = pass_entry.get()
            
            query = """
            SELECT * FROM usuarios 
            WHERE username = %s AND password = %s AND tipo IN ('administrador', 'superusuario')
            """
            user = db.execute_one(query, (username, password))
            
            if user:
                result = user
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Credenciales incorrectas")
        
        # Botones - más compactos
        button_frame = tk.Frame(main_frame, bg='#f8f9fa')
        button_frame.pack(pady=(0,5), fill='x')
        
        tk.Button(button_frame, text="CANCELAR", font=('Arial', 11, 'bold'),
                 bg='#95a5a6', fg='white', width=10, height=1,
                 command=dialog.destroy).pack(side='left', padx=5)
        
        tk.Button(button_frame, text="VERIFICAR", font=('Arial', 11, 'bold'),
                 bg='#3498db', fg='white', width=12, height=1,
                 command=verificar).pack(side='right', padx=5)
        
        user_entry.focus()
        user_entry.bind('<Return>', lambda e: pass_entry.focus())
        pass_entry.bind('<Return>', lambda e: verificar())
        
        dialog.wait_window()
        return result

    def show_admin_menu(self):
        self.clear_window()
        
        # Header
        header_frame = tk.Frame(self.root, bg='#34495e', height=60)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        user_info = f"Administrador: {auth.current_user['nombre']}"
        tk.Label(header_frame, text=user_info, font=('Arial', 12, 'bold'), 
                bg='#34495e', fg='white').pack(side='left', padx=20, pady=20)
        
        tk.Button(header_frame, text="Cerrar Sesión", command=self.logout).pack(side='right', padx=20, pady=15)
        
        # Menú principal
        main_frame = tk.Frame(self.root, bg='#f5f5f5')
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        tk.Label(main_frame, text="Panel de Administración", 
                font=('Arial', 18, 'bold'), bg='#f5f5f5').pack(pady=20)
        
        # Grid de botones
        buttons_frame = tk.Frame(main_frame, bg='#f5f5f5')
        buttons_frame.pack(expand=True)
        
        # Fila 1
        row1 = tk.Frame(buttons_frame, bg='#f5f5f5')
        row1.pack(pady=10)
        
        tk.Button(row1, text="Administrar Menú", font=('Arial', 12, 'bold'),
                 bg='#3498db', fg='white', width=20, height=3,
                 command=self.admin_menu).pack(side='left', padx=10)
        
        tk.Button(row1, text="Administrar Usuarios", font=('Arial', 12, 'bold'),
                 bg='#2980b9', fg='white', width=20, height=3,
                 command=self.admin_usuarios).pack(side='left', padx=10)
        
        # Fila 2
        row2 = tk.Frame(buttons_frame, bg='#f5f5f5')
        row2.pack(pady=10)
        
        tk.Button(row2, text="Administrar Ventas", font=('Arial', 12, 'bold'),
                 bg='#5dade2', fg='white', width=20, height=3,
                 command=self.admin_ventas).pack(side='left', padx=10)
        
        tk.Button(row2, text="Administrar Clientes", font=('Arial', 12, 'bold'),
                 bg='#85c1e9', fg='white', width=20, height=3,
                 command=self.admin_clientes).pack(side='left', padx=10)

    def admin_menu(self):
        messagebox.showinfo("Información", "Funcionalidad en desarrollo")

    def admin_usuarios(self):
        messagebox.showinfo("Información", "Funcionalidad en desarrollo")

    def admin_ventas(self):
        messagebox.showinfo("Información", "Funcionalidad en desarrollo")

    def admin_clientes(self):
        messagebox.showinfo("Información", "Funcionalidad en desarrollo")

    def logout(self):
        if auth.current_user and auth.current_user['tipo'] == 'cajero' and auth.current_turno:
            response = messagebox.askyesno(
                "Cerrar Sesión", 
                "Tiene un turno abierto. ¿Desea cerrar sesión sin cerrar el turno?\n\n"
                "Recuerde que deberá volver para cerrar su turno al final del día."
            )
            if not response:
                return
        
        auth.logout()
        self.show_login()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = RestaurantPOS()
    app.run()
