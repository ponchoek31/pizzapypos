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
                item['subtotal'] = item['cantidad'] * item['precio']
                break
        else:
            # Agregar nuevo item
            self.orden_actual['items'].append({
                'id': producto['id'],
                'nombre': producto['nombre'],
                'precio': producto['precio'],
                'cantidad': 1,
                'subtotal': producto['precio']
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
                    change = amount - self.orden_actual['total']
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
        
        amount_entry.bind('<KeyRelease>', lambda e: calculate_change())
        
        def confirmar_pago():
            try:
                amount_text = amount_entry.get().strip()
                if not amount_text:
                    messagebox.showerror("Error", "Por favor ingrese el monto pagado")
                    amount_entry.focus()
                    return
                
                amount = float(amount_text)
                if amount < self.orden_actual['total'] - 0.01:
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
            
            # Calcular cambio
            cambio = monto_pagado - self.orden_actual['total']
            
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
                self.orden_actual['total'], self.orden_actual['total'],
                metodo_pago, monto_pagado, cambio,
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
                query = """
                INSERT INTO orden_detalles (orden_id, producto_id, cantidad, precio_unitario, subtotal)
                VALUES (%s, %s, %s, %s, %s)
                """
                detalle_result = db.execute_one(query, (
                    orden_id, item['id'], item['cantidad'], item['precio'], item['subtotal']
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
        dialog.geometry("800x600")
        dialog.transient(self.root)
        
        # Obtener órdenes del día
        query = """
        SELECT o.*, c.nombre as cliente_nombre
        FROM ordenes o
        LEFT JOIN clientes c ON o.cliente_id = c.id
        WHERE DATE(o.fecha_orden) = CURDATE() AND o.turno_id = %s
        ORDER BY o.fecha_orden DESC
        """
        ordenes = db.execute_query(query, (auth.current_turno['id'],))
        
        # Crear treeview
        columns = ('numero_orden', 'cliente', 'tipo', 'total', 'hora')
        tree = ttk.Treeview(dialog, columns=columns, show='headings', height=20)
        
        tree.heading('numero_orden', text='# Orden')
        tree.heading('cliente', text='Cliente')
        tree.heading('tipo', text='Tipo')
        tree.heading('total', text='Total')
        tree.heading('hora', text='Hora')
        
        tree.column('numero_orden', width=100)
        tree.column('cliente', width=200)
        tree.column('tipo', width=100)
        tree.column('total', width=100)
        tree.column('hora', width=100)
        
        # Llenar datos
        for orden in ordenes:
            tree.insert('', 'end', values=(
                orden['numero_orden'],
                orden['cliente_nombre'] or orden['cliente_nombre'] or 'N/A',
                orden['tipo_orden'].title(),
                f"${orden['total']:.2f}",
                orden['fecha_orden'].strftime('%H:%M')
            ), tags=(orden['id'],))
        
        tree.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Botones
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)
        
        def reimprimir_venta():
            selection = tree.selection()
            if selection:
                orden_id = tree.item(selection[0])['tags'][0]
                printer.print_customer_ticket(orden_id)
        
        def reimprimir_comanda():
            selection = tree.selection()
            if selection:
                orden_id = tree.item(selection[0])['tags'][0]
                printer.print_kitchen_ticket(orden_id)
        
        tk.Button(btn_frame, text="Reimprimir Venta", command=reimprimir_venta).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Reimprimir Comanda", command=reimprimir_comanda).pack(side='left', padx=5)

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
        dialog.geometry("400x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Corte de Caja", font=('Arial', 16, 'bold')).pack(pady=20)
        
        # Paso 1: Cajero ingresa cantidades
        step1_frame = tk.Frame(dialog)
        step1_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(step1_frame, text="1. Cajero - Ingrese las cantidades finales:", 
                font=('Arial', 12, 'bold')).pack(anchor='w')
        
        tk.Label(step1_frame, text="Efectivo en caja:").pack(anchor='w', pady=(10,0))
        efectivo_entry = tk.Entry(step1_frame, font=('Arial', 12))
        efectivo_entry.pack(fill='x', pady=2)
        
        tk.Label(step1_frame, text="Total tarjetas:").pack(anchor='w', pady=(5,0))
        tarjeta_entry = tk.Entry(step1_frame, font=('Arial', 12))
        tarjeta_entry.pack(fill='x', pady=2)
        
        warning_label = tk.Label(step1_frame, 
                               text="⚠️ Precaución: Cualquier faltante será cobrado",
                               font=('Arial', 10), fg='#e74c3c')
        warning_label.pack(pady=10)
        
        def paso2():
            try:
                efectivo = float(efectivo_entry.get())
                tarjeta = float(tarjeta_entry.get())
                self.show_corte_paso2(dialog, admin_user, efectivo, tarjeta)
            except ValueError:
                messagebox.showerror("Error", "Por favor ingrese montos válidos")
        
        tk.Button(step1_frame, text="Continuar", bg='#3498db', fg='white',
                 command=paso2).pack(pady=20)
        
        efectivo_entry.focus()

    def show_corte_paso2(self, parent_dialog, admin_user, efectivo_cajero, tarjeta_cajero):
        parent_dialog.destroy()
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Corte de Caja - Confirmación")
        dialog.geometry("500x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Confirmación de Corte", font=('Arial', 16, 'bold')).pack(pady=20)
        
        # Calcular totales esperados
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
        
        # Obtener arqueos
        query = "SELECT COALESCE(SUM(monto), 0) as total_arqueos FROM arqueos WHERE turno_id = %s"
        arqueos_result = db.execute_one(query, (auth.current_turno['id'],))
        total_arqueos = arqueos_result['total_arqueos'] if arqueos_result else 0
        
        # Calcular esperados
        efectivo_esperado = auth.current_turno['fondo_inicial'] + ventas['ventas_efectivo'] - total_arqueos
        tarjeta_esperada = ventas['ventas_tarjeta']
        total_esperado = efectivo_esperado + tarjeta_esperada
        total_real = efectivo_cajero + tarjeta_cajero
        diferencia = total_esperado - total_real
        
        # Mostrar resumen
        info_frame = tk.Frame(dialog)
        info_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(info_frame, text="RESUMEN DEL TURNO", font=('Arial', 14, 'bold')).pack()
        
        # Tabla de información
        info_text = f"""
Fondo inicial: ${auth.current_turno['fondo_inicial']:.2f}
Ventas efectivo: ${ventas['ventas_efectivo']:.2f}
Ventas tarjeta: ${ventas['ventas_tarjeta']:.2f}
Total arqueos: ${total_arqueos:.2f}

CANTIDADES ESPERADAS:
Efectivo esperado: ${efectivo_esperado:.2f}
Tarjeta esperada: ${tarjeta_esperada:.2f}
Total esperado: ${total_esperado:.2f}

CANTIDADES REPORTADAS:
Efectivo reportado: ${efectivo_cajero:.2f}
Tarjeta reportada: ${tarjeta_cajero:.2f}
Total reportado: ${total_real:.2f}

DIFERENCIA: ${diferencia:.2f}
"""
        
        text_widget = tk.Text(info_frame, height=15, width=50, font=('Arial', 10))
        text_widget.insert('1.0', info_text)
        text_widget.config(state='disabled')
        text_widget.pack(pady=10)
        
        # Pedir confirmación del administrador
        admin_frame = tk.Frame(dialog)
        admin_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(admin_frame, text="Administrador - Confirme con su contraseña:", 
                font=('Arial', 12, 'bold')).pack(anchor='w')
        
        admin_pass_entry = tk.Entry(admin_frame, show='*', font=('Arial', 12))
        admin_pass_entry.pack(fill='x', pady=5)
        
        def finalizar_corte():
            # Verificar contraseña del administrador nuevamente
            query = "SELECT * FROM usuarios WHERE id = %s AND password = %s"
            admin_check = db.execute_one(query, (admin_user['id'], admin_pass_entry.get()))
            
            if not admin_check:
                messagebox.showerror("Error", "Contraseña de administrador incorrecta")
                return
            
            # Cerrar turno
            if auth.cerrar_turno(efectivo_cajero, tarjeta_cajero):
                # Imprimir corte
                corte_path = printer.print_corte_caja(auth.current_turno['id'] if auth.current_turno else None)
                
                messagebox.showinfo("Éxito", "Corte de caja realizado correctamente")
                dialog.destroy()
                
                # Hacer logout después del corte
                auth.logout()
                self.show_login()
            else:
                messagebox.showerror("Error", "No se pudo procesar el corte de caja")
        
        tk.Button(admin_frame, text="FINALIZAR CORTE", bg='#e74c3c', fg='white',
                 font=('Arial', 12, 'bold'), command=finalizar_corte).pack(pady=20)
        
        admin_pass_entry.focus()

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
