from reportlab.pdfgen import canvas
import tempfile
from reportlab.lib.pagesizes import letter
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