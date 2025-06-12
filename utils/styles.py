from tkinter import ttk
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