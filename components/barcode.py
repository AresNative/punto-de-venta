from PIL import Image, ImageTk 
from tkinter import ttk, messagebox
def init_barcode_scanner(self):
    self.codigo_barras_activo = False
    self.codigo_barras_buffer = ""
    
    # Crear etiqueta para mostrar el estado del escáner
    self.barcode_status = ttk.Label(self, text="Escáner: INACTIVO", foreground='red')
    self.barcode_status.pack(pady=10)
    
    # Crear etiqueta para mostrar la imagen del escáner
    self.barcode_image_label = ttk.Label(self)
    self.barcode_image_label.pack(pady=10)
    
    # Botón para activar/desactivar el escáner
    self.toggle_button = ttk.Button(self, text="Activar Escáner de Código de Barras", command=self.toggle_barcode_scanner)
    self.toggle_button.pack(pady=10)
    
    # Asociar eventos de teclado
    self.bind("<KeyPress>", self.on_key_press)
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
