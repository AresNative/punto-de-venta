# 🧾 Punto de Venta en Python

Sistema completo de punto de venta (PDV) con interfaz gráfica usando **Tkinter**, base de datos local con **SQLite3**, generación de tickets en **PDF**, y funcionalidades como escáner de código de barras y simulación de báscula.

---

## 📁 Estructura del Proyecto

```
pdv/
├── main.py
├── /components
│   ├── app.py
│   ├── bascula.py
│   ├── barcode.py
│   └── login.py
├── /utils
│   ├── database.py
│   ├── styles.py
│   └── ticket.py
├── assets/
│   ├── barcode_active.png
│   └── barcode_inactive.png
└── README.md
```

---

## 🚀 Requisitos

Instala las dependencias necesarias:

```bash
pip install -r requirements.txt
```

### `requirements.txt` sugerido:

```
tk
reportlab
pillow
keyboard
```

> ⚠️ `keyboard` requiere permisos de administrador en Windows para funcionar correctamente.

O de manera idependiente:

```bash
pip install tk
```

```bash
pip install reportlab
```

```bash
pip install keyboard pillow
```

```bash
pip install pyinstaller
```

---

## ▶️ Ejecución del Proyecto

```bash
python main.py
```

---

## 🔐 Acceso por defecto

- **Usuario:** `admin`
- **Contraseña:** `admin123`

---

## 💾 Base de datos

Se genera automáticamente como `punto_venta.db` al ejecutar el sistema por primera vez.

---

## 🛠️ Compilar a `.exe`

Para generar un archivo ejecutable `.exe` en Windows con PyInstaller:

### 1. Instalar PyInstaller

```bash
pip install pyinstaller
```

### 2. Generar el ejecutable

```bash
pyinstaller --noconfirm --onefile --windowed --add-data "assets;assets" main.py
```

> ⚠️ En Linux/macOS usa `:` en lugar de `;` para el parámetro `--add-data`.

### 🔍 El ejecutable se ubicará en:

```
dist/main.exe
```

---

## 📌 Notas

- El escaneo por teclado (`keyboard`) funciona correctamente si ejecutas el programa como **administrador en Windows**.
- Puedes extender este proyecto fácilmente con:
  - Control de inventario avanzado
  - Dashboard de estadísticas
  - Integración con impresoras térmicas
  - Exportación a Excel o PDF

---
