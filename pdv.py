import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
import datetime
import os
import tempfile
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import random
import threading
import time
import keyboard  # Para simular escaneo de código de barras
from PIL import Image, ImageTk  # Para mostrar imagen de código de barras
# --------------------------
# Configuración de la base de datos
# --------------------------
class Database:
    def __init__(self):
        self.conn = sqlite3.connect('punto_venta.db')
        self.create_tables()
        self.insert_default_data()
        
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Tabla de usuarios
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            usuario TEXT UNIQUE NOT NULL,
            contrasena TEXT NOT NULL,
            rol TEXT NOT NULL
        )
        ''')
        
        # Tabla de productos
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            precio REAL NOT NULL,
            por_peso INTEGER NOT NULL,
            stock REAL NOT NULL
        )
        ''')
        
        # Tabla de ventas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            total REAL NOT NULL,
            usuario_id INTEGER NOT NULL,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        )
        ''')
        
        # Tabla de detalle_venta
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS detalle_venta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id INTEGER NOT NULL,
            producto_id INTEGER NOT NULL,
            cantidad REAL NOT NULL,
            precio_unitario REAL NOT NULL,
            total_linea REAL NOT NULL,
            FOREIGN KEY(venta_id) REFERENCES ventas(id),
            FOREIGN KEY(producto_id) REFERENCES productos(id)
        )
        ''')
        
        self.conn.commit()
    
    def insert_default_data(self):
        cursor = self.conn.cursor()
        
        # Insertar usuario administrador si no existe
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = 'admin'")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
            INSERT INTO usuarios (nombre, usuario, contrasena, rol)
            VALUES (?, ?, ?, ?)
            ''', ('Administrador', 'admin', 'admin123', 'admin'))
        
        # Insertar productos de ejemplo si no existen
        cursor.execute("SELECT COUNT(*) FROM productos")
        if cursor.fetchone()[0] == 0:
            productos = [
                ('001', 'Manzanas', 2.99, 1, 100.0),
                ('002', 'Leche Entera', 1.99, 0, 50),
                ('003', 'Pan Integral', 3.49, 0, 30),
                ('004', 'Pechuga de Pollo', 8.99, 1, 50.0),
                ('005', 'Arroz 1kg', 4.25, 0, 40)
            ]
            cursor.executemany('''
            INSERT INTO productos (codigo, nombre, precio, por_peso, stock)
            VALUES (?, ?, ?, ?, ?)
            ''', productos)
        
        self.conn.commit()
    
    def get_productos(self, filtro=None):
        cursor = self.conn.cursor()
        if filtro:
            cursor.execute('''
            SELECT id, codigo, nombre, precio, por_peso, stock 
            FROM productos 
            WHERE nombre LIKE ? OR codigo LIKE ?
            ''', (f'%{filtro}%', f'%{filtro}%'))
        else:
            cursor.execute('SELECT id, codigo, nombre, precio, por_peso, stock FROM productos')
        return cursor.fetchall()
    
    def actualizar_stock(self, producto_id, cantidad):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE productos SET stock = stock - ? WHERE id = ?', (cantidad, producto_id))
        self.conn.commit()
    
    def registrar_venta(self, usuario_id, carrito):
        cursor = self.conn.cursor()
        total = sum(item['precio'] * item['cantidad'] for item in carrito)
        fecha = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Registrar venta
        cursor.execute('''
        INSERT INTO ventas (fecha, total, usuario_id)
        VALUES (?, ?, ?)
        ''', (fecha, total, usuario_id))
        venta_id = cursor.lastrowid
        
        # Registrar detalles de venta
        for item in carrito:
            cursor.execute('''
            INSERT INTO detalle_venta (venta_id, producto_id, cantidad, precio_unitario, total_linea)
            VALUES (?, ?, ?, ?, ?)
            ''', (venta_id, item['id'], item['cantidad'], item['precio'], item['precio'] * item['cantidad']))
            
            # Actualizar stock
            self.actualizar_stock(item['id'], item['cantidad'])
        
        self.conn.commit()
        return venta_id
    
    def verificar_usuario(self, usuario, contrasena):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT id, nombre, rol 
        FROM usuarios 
        WHERE usuario = ? AND contrasena = ?
        ''', (usuario, contrasena))
        return cursor.fetchone()
    
    def get_ventas_diarias(self):
        cursor = self.conn.cursor()
        hoy = datetime.datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
        SELECT v.id, v.fecha, u.nombre, v.total 
        FROM ventas v
        JOIN usuarios u ON v.usuario_id = u.id
        WHERE DATE(v.fecha) = ?
        ORDER BY v.fecha DESC
        ''', (hoy,))
        return cursor.fetchall()
    
    def get_detalle_venta(self, venta_id):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT p.nombre, dv.cantidad, dv.precio_unitario, dv.total_linea
        FROM detalle_venta dv
        JOIN productos p ON dv.producto_id = p.id
        WHERE dv.venta_id = ?
        ''', (venta_id,))
        return cursor.fetchall()

# --------------------------
# Autenticación de usuarios
# --------------------------
class LoginWindow:
    def __init__(self, root, db, on_login):
        self.root = root
        self.root.title("Inicio de Sesión")
        self.root.geometry("400x300")
        self.db = db
        self.on_login = on_login
        
        self.frame = ttk.Frame(root)
        self.frame.pack(expand=True, padx=50, pady=50)
        
        ttk.Label(self.frame, text="Sistema de Punto de Venta", font=('Helvetica', 16, 'bold')).pack(pady=20)
        
        ttk.Label(self.frame, text="Usuario:").pack(anchor='w', pady=(10, 0))
        self.usuario_entry = ttk.Entry(self.frame)
        self.usuario_entry.pack(fill=tk.X, pady=5)
        self.usuario_entry.insert(0, 'admin')
        
        ttk.Label(self.frame, text="Contraseña:").pack(anchor='w')
        self.contrasena_entry = ttk.Entry(self.frame, show='*')
        self.contrasena_entry.pack(fill=tk.X, pady=5)
        self.contrasena_entry.insert(0, 'admin123')
        
        ttk.Button(self.frame, text="Iniciar Sesión", command=self.verificar_credenciales).pack(pady=20)
        
        self.mensaje_label = ttk.Label(self.frame, text="", foreground='red')
        self.mensaje_label.pack()
    
    def verificar_credenciales(self):
        usuario = self.usuario_entry.get()
        contrasena = self.contrasena_entry.get()
        
        resultado = self.db.verificar_usuario(usuario, contrasena)
        
        if resultado:
            self.root.destroy()
            self.on_login(*resultado)
        else:
            self.mensaje_label.config(text="Usuario o contraseña incorrectos")

# --------------------------
# Generación de tickets PDF
# --------------------------
class TicketGenerator:
    @staticmethod
    def generar_ticket(venta_id, detalles, total, fecha, usuario):
        filename = tempfile.mktemp(prefix=f"ticket_{venta_id}_", suffix=".pdf")
        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter
        
        # Encabezado
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(width/2, height - 50, "TIENDA DE ABARROTES")
        c.setFont("Helvetica", 10)
        c.drawCentredString(width/2, height - 70, "Av. Principal 123, Ciudad")
        c.drawCentredString(width/2, height - 85, "Tel: (555) 123-4567")
        
        # Información de la venta
        c.setFont("Helvetica-Bold", 12)
        c.drawString(100, height - 120, f"Ticket #: {venta_id}")
        c.drawString(100, height - 140, f"Fecha: {fecha}")
        c.drawString(100, height - 160, f"Atendido por: {usuario}")
        
        # Detalles
        c.line(50, height - 180, width - 50, height - 180)
        
        y_position = height - 200
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y_position, "Producto")
        c.drawString(300, y_position, "Cantidad")
        c.drawString(350, y_position, "Precio")
        c.drawString(450, y_position, "Total")
        
        y_position -= 25
        c.setFont("Helvetica", 10)
        
        for detalle in detalles:
            nombre, cantidad, precio_unitario, total_linea = detalle
            
            # Ajustar nombre si es muy largo
            nombre = nombre[:25] + "..." if len(nombre) > 25 else nombre
            
            c.drawString(50, y_position, nombre)
            c.drawString(300, y_position, f"{cantidad}")
            c.drawString(350, y_position, f"${precio_unitario:.2f}")
            c.drawString(450, y_position, f"${total_linea:.2f}")
            y_position -= 20
        
        # Total
        c.line(50, y_position - 10, width - 50, y_position - 10)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(400, y_position - 30, f"TOTAL: ${total:.2f}")
        
        # Pie de página
        c.setFont("Helvetica", 8)
        c.drawCentredString(width/2, 50, "¡Gracias por su compra!")
        c.drawCentredString(width/2, 30, "Vuelva pronto")
        
        c.save()
        return filename

# --------------------------
# Simulación de báscula
# --------------------------
class Bascula:
    def __init__(self):
        self.peso = 0.0
        self.activa = False
        
    def iniciar(self, callback):
        self.activa = True
        threading.Thread(target=self._simular_peso, args=(callback,), daemon=True).start()
    
    def detener(self):
        self.activa = False
        
    def _simular_peso(self, callback):
        while self.activa:
            self.peso = round(random.uniform(0.1, 5.0), 2)
            callback(self.peso)
            time.sleep(1)

# --------------------------
# Configuración de estilos
# --------------------------
def configurar_estilos():
    estilo = ttk.Style()
    estilo.theme_use('clam')
    
    # Colores Tailwind
    colores = {
        'azul': '#3b82f6',
        'gris': '#f3f4f6',
        'gris-oscuro': '#4b5563',
        'rojo': '#ef4444',
        'verde': '#10b981',
        'amarillo': '#f59e0b',
    }
    
    # Configurar estilos
    estilo.configure('TFrame', background=colores['gris'])
    estilo.configure('TButton', 
                    font=('Helvetica', 11, 'bold'),
                    padding=8,
                    background=colores['azul'],
                    foreground='white')
    estilo.map('TButton', 
              background=[('active', colores['azul']), ('pressed', colores['azul'])])
    
    estilo.configure('Rojo.TButton', background=colores['rojo'])
    estilo.configure('Verde.TButton', background=colores['verde'])
    estilo.configure('Amarillo.TButton', background=colores['amarillo'])
    estilo.configure('TLabel', 
                    background=colores['gris'],
                    foreground=colores['gris-oscuro'],
                    font=('Helvetica', 10))
    estilo.configure('Titulo.TLabel', 
                    font=('Helvetica', 14, 'bold'),
                    foreground=colores['gris-oscuro'])
    estilo.configure('TEntry', padding=5)
    estilo.configure('Treeview', 
                    font=('Helvetica', 10),
                    rowheight=25)
    estilo.configure('Treeview.Heading', 
                    font=('Helvetica', 10, 'bold'))
    estilo.map('Treeview', background=[('selected', colores['azul'])])
    
    return colores

# --------------------------
# Sistema de punto de venta
# --------------------------
class PuntoVenta:
    def __init__(self, root, usuario_id, nombre_usuario, rol_usuario):
        self.root = root
        self.root.title("Sistema de Punto de Venta")
        self.root.geometry("1400x800")
        self.colores = configurar_estilos()
        
        self.usuario_id = usuario_id
        self.nombre_usuario = nombre_usuario
        self.rol_usuario = rol_usuario
        
        self.db = Database()
        self.bascula = Bascula()
        self.carrito = []
        
        self.crear_interfaz()
        self.cargar_productos()
        
        self.codigo_barras_buffer = ""
        self.codigo_barras_activo = False
        # Mostrar nombre de usuario
        self.usuario_label.config(text=f"Usuario: {self.nombre_usuario} ({self.rol_usuario})")
        
    def crear_interfaz(self):
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Cabecera
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(header_frame, 
                 text="Sistema de Punto de Venta", 
                 style='Titulo.TLabel').pack(side=tk.LEFT)
        
        self.usuario_label = ttk.Label(header_frame, style='Titulo.TLabel')
        self.usuario_label.pack(side=tk.RIGHT)
        
        # Contenedor principal
        container = ttk.Frame(main_frame)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Panel izquierdo (Productos)
        left_panel = ttk.Frame(container)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Búsqueda y acciones
        top_frame = ttk.Frame(left_panel)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(top_frame, text="Buscar Producto:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(top_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind('<KeyRelease>', self.buscar_producto)
        
        # Botones de administración (solo para admin)
        if self.rol_usuario == 'admin':
            ttk.Button(top_frame, 
                      text="Administrar Productos", 
                      style='Amarillo.TButton',
                      command=self.abrir_admin_productos).pack(side=tk.RIGHT, padx=5)
            
            ttk.Button(top_frame, 
                      text="Reportes", 
                      style='Amarillo.TButton',
                      command=self.mostrar_reportes).pack(side=tk.RIGHT, padx=5)
        
        # Lista de productos
        self.product_tree = ttk.Treeview(left_panel, columns=('codigo', 'nombre', 'precio', 'stock'), show='headings')
        self.product_tree.heading('codigo', text='Código')
        self.product_tree.heading('nombre', text='Producto')
        self.product_tree.heading('precio', text='Precio')
        self.product_tree.heading('stock', text='Stock')
        self.product_tree.column('codigo', width=80)
        self.product_tree.column('nombre', width=200)
        self.product_tree.column('precio', width=80)
        self.product_tree.column('stock', width=80)
        
        scrollbar = ttk.Scrollbar(left_panel, orient=tk.VERTICAL, command=self.product_tree.yview)
        self.product_tree.configure(yscrollcommand=scrollbar.set)
        
        self.product_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.product_tree.bind('<<TreeviewSelect>>', self.seleccionar_producto)
        
        # Panel derecho (Carrito y Báscula)
        right_panel = ttk.Frame(container)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        
        # Carrito
        cart_frame = ttk.LabelFrame(right_panel, text="Carrito de Compras")
        cart_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.cart_tree = ttk.Treeview(cart_frame, columns=('producto', 'cantidad', 'precio', 'total'), show='headings')
        self.cart_tree.heading('producto', text='Producto')
        self.cart_tree.heading('cantidad', text='Cantidad')
        self.cart_tree.heading('precio', text='Precio Unit.')
        self.cart_tree.heading('total', text='Total')
        self.cart_tree.column('producto', width=150)
        self.cart_tree.column('cantidad', width=80)
        self.cart_tree.column('precio', width=100)
        self.cart_tree.column('total', width=100)
        
        cart_scroll = ttk.Scrollbar(cart_frame, orient=tk.VERTICAL, command=self.cart_tree.yview)
        self.cart_tree.configure(yscrollcommand=cart_scroll.set)
        
        self.cart_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        cart_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Totales
        total_frame = ttk.Frame(right_panel)
        total_frame.pack(fill=tk.X, pady=(5, 10))
        
        ttk.Label(total_frame, text="Total:", font=('Helvetica', 12, 'bold')).pack(side=tk.LEFT)
        self.total_var = tk.StringVar(value="$0.00")
        ttk.Label(total_frame, textvariable=self.total_var, font=('Helvetica', 12, 'bold')).pack(side=tk.RIGHT)
        
        # Báscula
        scale_frame = ttk.LabelFrame(right_panel, text="Báscula")
        scale_frame.pack(fill=tk.X)
        
        self.scale_var = tk.StringVar(value="0.00 kg")
        ttk.Label(scale_frame, 
                 textvariable=self.scale_var, 
                 font=('Helvetica', 24, 'bold'),
                 anchor=tk.CENTER).pack(pady=20)
        
        btn_frame = ttk.Frame(scale_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, 
                  text="Iniciar Báscula", 
                  command=self.iniciar_bascula).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, 
                  text="Detener Báscula", 
                  command=self.detener_bascula).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, 
                  text="Agregar por Peso", 
                  style='Verde.TButton',
                  command=self.agregar_por_peso).pack(side=tk.RIGHT, padx=5)
        
        # Botones de acciones
        action_frame = ttk.Frame(right_panel)
        action_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(action_frame, 
                  text="Finalizar Venta", 
                  style='Verde.TButton',
                  command=self.finalizar_venta).pack(side=tk.RIGHT, padx=5)
        ttk.Button(action_frame, 
                  text="Cancelar Venta", 
                  style='Rojo.TButton',
                  command=self.cancelar_venta).pack(side=tk.RIGHT, padx=5)
        ttk.Button(action_frame, 
                  text="Eliminar Producto", 
                  command=self.eliminar_producto).pack(side=tk.RIGHT, padx=5)
        # Añadir sección de código de barras
        barcode_frame = ttk.LabelFrame(left_panel, text="Escaneo de Código de Barras")
        barcode_frame.pack(fill=tk.X, pady=(10, 5))
        
        self.barcode_image_label = ttk.Label(barcode_frame)
        self.barcode_image_label.pack()
        
        ttk.Button(barcode_frame, 
                text="Activar Escáner (F2)", 
                command=self.toggle_barcode_scanner).pack(pady=5)
        
        self.barcode_status = ttk.Label(barcode_frame, text="Escáner: INACTIVO", foreground='red')
        self.barcode_status.pack()
        
        # Modificar la función de agregar producto para incluir multiplicador
        add_frame = ttk.Frame(left_panel)
        add_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(add_frame, text="Multiplicador:").pack(side=tk.LEFT)
        self.multiplier_var = tk.IntVar(value=1)
        multiplier_spin = ttk.Spinbox(add_frame, from_=1, to=100, textvariable=self.multiplier_var, width=5)
        multiplier_spin.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(add_frame, 
              text="Agregar al Carrito", 
              command=self.agregar_con_multiplicador).pack(side=tk.RIGHT)
    
    # Configurar evento de teclado para código de barras
    keyboard.on_press(self.on_key_press)
    
    def cargar_productos(self, filtro=None):
        self.product_tree.delete(*self.product_tree.get_children())
        productos = self.db.get_productos(filtro)
        
        for prod in productos:
            id_prod, codigo, nombre, precio, por_peso, stock = prod
            precio_str = f"${precio}" 
            if por_peso:
                precio_str += "/kg"
            
            stock_str = f"{stock} kg" if por_peso else f"{int(stock)} u"
            
            self.product_tree.insert('', tk.END, values=(codigo, nombre, precio_str, stock_str), iid=id_prod)
    
    def buscar_producto(self, event):
        filtro = self.search_var.get()
        self.cargar_productos(filtro)
    
    def seleccionar_producto(self, event):
        item = self.product_tree.selection()
        if item:
            id_prod = item[0]
            self.agregar_a_carrito(id_prod)
    
    def agregar_a_carrito(self, id_prod, cantidad=1.0):
        # Obtener detalles del producto
        item = self.product_tree.item(id_prod)
        valores = item['values']
        codigo, nombre, precio_str, stock_str = valores
        
        # Convertir precio a número
        precio = float(precio_str.replace('$', '').replace('/kg', ''))
        
        # Verificar stock
        por_peso = '/kg' in precio_str
        stock = float(stock_str.split()[0])
        
        if stock < cantidad:
            messagebox.showwarning("Stock insuficiente", f"No hay suficiente stock de {nombre}")
            return
        
        # Verificar si ya está en el carrito
        for item in self.carrito:
            if item['id'] == int(id_prod):
                if item['stock'] < item['cantidad'] + cantidad:
                    messagebox.showwarning("Stock insuficiente", f"No hay suficiente stock de {nombre}")
                    return
                item['cantidad'] += cantidad
                self.actualizar_carrito()
                return
        
        # Agregar nuevo producto al carrito
        self.carrito.append({
            'id': int(id_prod),
            'codigo': codigo,
            'nombre': nombre,
            'precio': precio,
            'cantidad': cantidad,
            'por_peso': por_peso,
            'stock': stock
        })
        self.actualizar_carrito()
    
    def agregar_por_peso(self):
        item = self.product_tree.selection()
        if not item:
            messagebox.showwarning("Error", "Seleccione un producto de la lista")
            return
            
        try:
            peso = float(self.scale_var.get().split()[0])
        except:
            messagebox.showwarning("Error", "Peso inválido")
            return
            
        if peso <= 0:
            messagebox.showwarning("Error", "Peso inválido")
            return
            
        id_prod = item[0]
        self.agregar_a_carrito(id_prod, peso)
    
    def actualizar_carrito(self):
        self.cart_tree.delete(*self.cart_tree.get_children())
        total_venta = 0.0
        
        for item in self.carrito:
            total_item = item['precio'] * item['cantidad']
            total_venta += total_item
            
            cantidad = f"{item['cantidad']} kg" if item['por_peso'] else f"{int(item['cantidad'])} u"
            
            self.cart_tree.insert('', tk.END, values=(
                item['nombre'],
                cantidad,
                f"${item['precio']:.2f}",
                f"${total_item:.2f}"
            ))
        
        self.total_var.set(f"${total_venta:.2f}")
    
    def eliminar_producto(self):
        item = self.cart_tree.selection()
        if item:
            index = self.cart_tree.index(item[0])
            del self.carrito[index]
            self.actualizar_carrito()
    
    def iniciar_bascula(self):
        self.bascula.iniciar(self.actualizar_peso)
    
    def detener_bascula(self):
        self.bascula.detener()
    
    def actualizar_peso(self, peso):
        self.scale_var.set(f"{peso} kg")
    
    def finalizar_venta(self):
        if not self.carrito:
            messagebox.showwarning("Error", "El carrito está vacío")
            return
        
        # Registrar venta en la base de datos
        venta_id = self.db.registrar_venta(self.usuario_id, self.carrito)
        
        # Generar ticket
        detalles = []
        total = 0.0
        for item in self.carrito:
            total_linea = item['precio'] * item['cantidad']
            detalles.append((
                item['nombre'],
                item['cantidad'],
                item['precio'],
                total_linea
            ))
            total += total_linea
        
        fecha = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ticket_path = TicketGenerator.generar_ticket(venta_id, detalles, total, fecha, self.nombre_usuario)
        
        # Mostrar mensaje con opción para abrir ticket
        respuesta = messagebox.askyesno(
            "Venta Finalizada", 
            f"Venta completada!\nTotal: ${total:.2f}\n\n¿Desea abrir el ticket?"
        )
        
        if respuesta:
            try:
                os.startfile(ticket_path)  # Windows
            except:
                os.system(f'open "{ticket_path}"')  # macOS
        
        self.cancelar_venta()
    
    def cancelar_venta(self):
        self.carrito = []
        self.actualizar_carrito()
        self.bascula.detener()
        self.scale_var.set("0.00 kg")
    
    def abrir_admin_productos(self):
        # Ventana para administrar productos
        admin_window = tk.Toplevel(self.root)
        admin_window.title("Administración de Productos")
        admin_window.geometry("800x600")
        
        frame = ttk.Frame(admin_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Lista de productos
        tree = ttk.Treeview(frame, columns=('id', 'codigo', 'nombre', 'precio', 'tipo', 'stock'), show='headings')
        tree.heading('id', text='ID')
        tree.heading('codigo', text='Código')
        tree.heading('nombre', text='Nombre')
        tree.heading('precio', text='Precio')
        tree.heading('tipo', text='Tipo')
        tree.heading('stock', text='Stock')
        
        tree.column('id', width=50)
        tree.column('codigo', width=80)
        tree.column('nombre', width=200)
        tree.column('precio', width=80)
        tree.column('tipo', width=100)
        tree.column('stock', width=80)
        
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Botones
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="Agregar Producto", command=lambda: self.agregar_producto(tree)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Editar", command=lambda: self.editar_producto(tree)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Eliminar", style='Rojo.TButton', command=lambda: self.eliminar_producto_db(tree)).pack(side=tk.LEFT, padx=5)
        
        # Cargar productos
        self.cargar_productos_admin(tree)
    
    def cargar_productos_admin(self, tree):
        for item in tree.get_children():
            tree.delete(item)
            
        productos = self.db.get_productos()
        for prod in productos:
            id_prod, codigo, nombre, precio, por_peso, stock = prod
            tipo = "Por peso" if por_peso else "Por unidad"
            tree.insert('', tk.END, values=(id_prod, codigo, nombre, precio, tipo, stock))
    
    def agregar_producto(self, tree):
        # Ventana para agregar producto
        add_window = tk.Toplevel(self.root)
        add_window.title("Agregar Producto")
        add_window.geometry("400x300")
        
        frame = ttk.Frame(add_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ttk.Label(frame, text="Código:").grid(row=0, column=0, sticky='w', pady=5)
        codigo_entry = ttk.Entry(frame)
        codigo_entry.grid(row=0, column=1, sticky='ew', pady=5, padx=5)
        
        ttk.Label(frame, text="Nombre:").grid(row=1, column=0, sticky='w', pady=5)
        nombre_entry = ttk.Entry(frame)
        nombre_entry.grid(row=1, column=1, sticky='ew', pady=5, padx=5)
        
        ttk.Label(frame, text="Precio:").grid(row=2, column=0, sticky='w', pady=5)
        precio_entry = ttk.Entry(frame)
        precio_entry.grid(row=2, column=1, sticky='ew', pady=5, padx=5)
        
        ttk.Label(frame, text="Tipo:").grid(row=3, column=0, sticky='w', pady=5)
        tipo_var = tk.StringVar(value="unidad")
        ttk.Radiobutton(frame, text="Por unidad", variable=tipo_var, value="unidad").grid(row=3, column=1, sticky='w', pady=5, padx=5)
        ttk.Radiobutton(frame, text="Por peso", variable=tipo_var, value="peso").grid(row=4, column=1, sticky='w', pady=5, padx=5)
        
        ttk.Label(frame, text="Stock inicial:").grid(row=5, column=0, sticky='w', pady=5)
        stock_entry = ttk.Entry(frame)
        stock_entry.grid(row=5, column=1, sticky='ew', pady=5, padx=5)
        
        def guardar_producto():
            try:
                codigo = codigo_entry.get()
                nombre = nombre_entry.get()
                precio = float(precio_entry.get())
                por_peso = 1 if tipo_var.get() == "peso" else 0
                stock = float(stock_entry.get())
                
                cursor = self.db.conn.cursor()
                cursor.execute('''
                INSERT INTO productos (codigo, nombre, precio, por_peso, stock)
                VALUES (?, ?, ?, ?, ?)
                ''', (codigo, nombre, precio, por_peso, stock))
                self.db.conn.commit()
                
                messagebox.showinfo("Éxito", "Producto agregado correctamente")
                self.cargar_productos_admin(tree)
                self.cargar_productos()  # Actualizar lista principal
                add_window.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Error al agregar producto: {str(e)}")
        
        ttk.Button(frame, text="Guardar", command=guardar_producto).grid(row=6, column=0, columnspan=2, pady=10)
    
    def editar_producto(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Error", "Seleccione un producto")
            return
            
        valores = tree.item(selected[0])['values']
        id_prod = valores[0]
        
        # Obtener producto de la base de datos
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT * FROM productos WHERE id = ?', (id_prod,))
        producto = cursor.fetchone()
        
        # Ventana para editar producto
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Editar Producto")
        edit_window.geometry("400x300")
        
        frame = ttk.Frame(edit_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ttk.Label(frame, text="Código:").grid(row=0, column=0, sticky='w', pady=5)
        codigo_entry = ttk.Entry(frame)
        codigo_entry.insert(0, producto[1])
        codigo_entry.grid(row=0, column=1, sticky='ew', pady=5, padx=5)
        
        ttk.Label(frame, text="Nombre:").grid(row=1, column=0, sticky='w', pady=5)
        nombre_entry = ttk.Entry(frame)
        nombre_entry.insert(0, producto[2])
        nombre_entry.grid(row=1, column=1, sticky='ew', pady=5, padx=5)
        
        ttk.Label(frame, text="Precio:").grid(row=2, column=0, sticky='w', pady=5)
        precio_entry = ttk.Entry(frame)
        precio_entry.insert(0, str(producto[3]))
        precio_entry.grid(row=2, column=1, sticky='ew', pady=5, padx=5)
        
        ttk.Label(frame, text="Tipo:").grid(row=3, column=0, sticky='w', pady=5)
        tipo_var = tk.StringVar(value="peso" if producto[4] else "unidad")
        ttk.Radiobutton(frame, text="Por unidad", variable=tipo_var, value="unidad").grid(row=3, column=1, sticky='w', pady=5, padx=5)
        ttk.Radiobutton(frame, text="Por peso", variable=tipo_var, value="peso").grid(row=4, column=1, sticky='w', pady=5, padx=5)
        
        ttk.Label(frame, text="Stock:").grid(row=5, column=0, sticky='w', pady=5)
        stock_entry = ttk.Entry(frame)
        stock_entry.insert(0, str(producto[5]))
        stock_entry.grid(row=5, column=1, sticky='ew', pady=5, padx=5)
        
        def actualizar_producto():
            try:
                codigo = codigo_entry.get()
                nombre = nombre_entry.get()
                precio = float(precio_entry.get())
                por_peso = 1 if tipo_var.get() == "peso" else 0
                stock = float(stock_entry.get())
                
                cursor = self.db.conn.cursor()
                cursor.execute('''
                UPDATE productos 
                SET codigo = ?, nombre = ?, precio = ?, por_peso = ?, stock = ?
                WHERE id = ?
                ''', (codigo, nombre, precio, por_peso, stock, id_prod))
                self.db.conn.commit()
                
                messagebox.showinfo("Éxito", "Producto actualizado correctamente")
                self.cargar_productos_admin(tree)
                self.cargar_productos()  # Actualizar lista principal
                edit_window.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Error al actualizar producto: {str(e)}")
        
        ttk.Button(frame, text="Actualizar", command=actualizar_producto).grid(row=6, column=0, columnspan=2, pady=10)
    
    def eliminar_producto_db(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Error", "Seleccione un producto")
            return
            
        valores = tree.item(selected[0])['values']
        id_prod = valores[0]
        nombre = valores[2]
        
        respuesta = messagebox.askyesno("Confirmar", f"¿Eliminar el producto '{nombre}'?")
        if respuesta:
            cursor = self.db.conn.cursor()
            cursor.execute('DELETE FROM productos WHERE id = ?', (id_prod,))
            self.db.conn.commit()
            self.cargar_productos_admin(tree)
            self.cargar_productos()  # Actualizar lista principal
    
    def mostrar_reportes(self):
        # Ventana de reportes
        reportes_window = tk.Toplevel(self.root)
        reportes_window.title("Reportes de Ventas")
        reportes_window.geometry("1000x600")
        
        frame = ttk.Frame(reportes_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ttk.Label(frame, text="Reporte de Ventas Diarias", style='Titulo.TLabel').pack(pady=10)
        
        # Lista de ventas
        tree = ttk.Treeview(frame, columns=('id', 'fecha', 'usuario', 'total'), show='headings')
        tree.heading('id', text='ID Venta')
        tree.heading('fecha', text='Fecha y Hora')
        tree.heading('usuario', text='Usuario')
        tree.heading('total', text='Total')
        
        tree.column('id', width=80)
        tree.column('fecha', width=150)
        tree.column('usuario', width=150)
        tree.column('total', width=100)
        
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Cargar ventas
        ventas = self.db.get_ventas_diarias()
        for venta in ventas:
            id_venta, fecha, usuario, total = venta
            tree.insert('', tk.END, values=(id_venta, fecha, usuario, f"${total:.2f}"), iid=id_venta)
        
        # Botón para ver detalle
        ttk.Button(frame, 
                  text="Ver Detalle de Venta", 
                  command=lambda: self.mostrar_detalle_venta(tree)).pack(pady=10)
    
    def mostrar_detalle_venta(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Error", "Seleccione una venta")
            return
            
        venta_id = selected[0]
        
        # Ventana de detalle
        detalle_window = tk.Toplevel(self.root)
        detalle_window.title(f"Detalle de Venta #{venta_id}")
        detalle_window.geometry("600x400")
        
        frame = ttk.Frame(detalle_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ttk.Label(frame, text=f"Detalle de Venta #{venta_id}", style='Titulo.TLabel').pack(pady=10)
        
        # Lista de productos
        tree_detalle = ttk.Treeview(frame, columns=('producto', 'cantidad', 'precio', 'total'), show='headings')
        tree_detalle.heading('producto', text='Producto')
        tree_detalle.heading('cantidad', text='Cantidad')
        tree_detalle.heading('precio', text='Precio Unit.')
        tree_detalle.heading('total', text='Total')
        
        tree_detalle.column('producto', width=200)
        tree_detalle.column('cantidad', width=80)
        tree_detalle.column('precio', width=100)
        tree_detalle.column('total', width=100)
        
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree_detalle.yview)
        tree_detalle.configure(yscrollcommand=scrollbar.set)
        
        tree_detalle.pack(fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Cargar detalle
        detalles = self.db.get_detalle_venta(venta_id)
        for detalle in detalles:
            nombre, cantidad, precio, total = detalle
            cantidad_str = f"{cantidad} kg" if cantidad % 1 != 0 else f"{int(cantidad)} u"
            tree_detalle.insert('', tk.END, values=(
                nombre,
                cantidad_str,
                f"${precio:.2f}",
                f"${total:.2f}"
            ))
def toggle_barcode_scanner(self):
    self.codigo_barras_activo = not self.codigo_barras_activo
    if self.codigo_barras_activo:
        self.barcode_status.config(text="Escáner: ACTIVO (Esperando código...)", foreground='green')
        self.mostrar_imagen_barcode(True)
    else:
        self.barcode_status.config(text="Escáner: INACTIVO", foreground='red')
        self.mostrar_imagen_barcode(False)
        self.codigo_barras_buffer = ""

def on_key_press(self, event):
    if not self.codigo_barras_activo:
        return
    
    if event.name == 'enter':
        if len(self.codigo_barras_buffer) >= 8:  # Longitud mínima de código de barras
            self.buscar_por_codigo_barras(self.codigo_barras_buffer)
        self.codigo_barras_buffer = ""
    elif event.name.isdigit():
        self.codigo_barras_buffer += event.name

def mostrar_imagen_barcode(self, activo):
    if activo:
        image = Image.open("barcode_active.png")  # Usar tu propia imagen
    else:
        image = Image.open("barcode_inactive.png")  # Usar tu propia imagen
    
    image = image.resize((200, 80), Image.LANCZOS)
    photo = ImageTk.PhotoImage(image)
    self.barcode_image_label.config(image=photo)
    self.barcode_image_label.image = photo

def buscar_por_codigo_barras(self, codigo):
    # Buscar producto por código de barras (asumiendo que el código de producto es el de barras)
    for item in self.product_tree.get_children():
        if self.product_tree.item(item)['values'][0] == codigo:
            self.product_tree.selection_set(item)
            self.product_tree.focus(item)
            self.agregar_con_multiplicador()
            return
    
    messagebox.showwarning("No encontrado", f"No se encontró producto con código: {codigo}")

# Método para agregar con multiplicador
def agregar_con_multiplicador(self):
    item = self.product_tree.selection()
    if item:
        multiplicador = self.multiplier_var.get()
        id_prod = item[0]
        self.agregar_a_carrito(id_prod, multiplicador)

# Modificar el método agregar_a_carrito para manejar multiplicador:
def agregar_a_carrito(self, id_prod, cantidad=1.0):
    # ... (código existente)
    
    # Cambiar la validación de stock para considerar el multiplicador
    if stock < cantidad:
        messagebox.showwarning("Stock insuficiente", 
                             f"No hay suficiente stock de {nombre}\nStock disponible: {stock}")
        return
# --------------------------
# Función principal
# --------------------------
def main():
    db = Database()
    
    # Ventana de login
    login_root = tk.Tk()
    def on_login_success(usuario_id, nombre, rol):
        # Ventana principal
        main_root = tk.Tk()
        app = PuntoVenta(main_root, usuario_id, nombre, rol)
        main_root.mainloop()
    
    login_app = LoginWindow(login_root, db, on_login_success)
    login_root.mainloop()

if __name__ == "__main__":
    main()