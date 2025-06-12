
import sqlite3
import datetime
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
