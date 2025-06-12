from utils.database import Database
from components.login import LoginWindow
from components.app import PuntoVenta

import tkinter as tk

def main():
    db = Database()
    
    login_root = tk.Tk()

    def on_login_success(usuario_id, nombre, rol):
        main_root = tk.Tk()
        app = PuntoVenta(main_root, usuario_id, nombre, rol)
        main_root.mainloop()
    
    LoginWindow(login_root, db, on_login_success)
    login_root.mainloop()

if __name__ == "__main__":
    main()
