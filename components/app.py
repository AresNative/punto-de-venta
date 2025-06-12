from utils.styles import configurar_estilos
from utils.ticket import TicketGenerator
from utils.database import Database
from components.bascula import Bascula
from components.barcode import toggle_barcode_scanner, on_key_press, buscar_por_codigo_barras
import tkinter as tk
from tkinter import ttk, messagebox
import keyboard 
import datetime
import os

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