import tkinter as tk
from tkinter import ttk

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
