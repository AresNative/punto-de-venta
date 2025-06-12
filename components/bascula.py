import threading
import time
import random
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