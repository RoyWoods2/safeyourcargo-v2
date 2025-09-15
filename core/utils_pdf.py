import io
from weasyprint import HTML
from django.template.loader import render_to_string
from num2words import num2words
from django.utils.formats import date_format
from decimal import Decimal
from datetime import date
from .models import Factura, CertificadoTransporte
from .utils import obtener_dolar_observado

def generar_pdf_certificado(certificado, request):
    html_string = render_to_string('certificados/certificado_pdf.html', {
        'certificado': certificado,
    })
    pdf_buffer = io.BytesIO()
    HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer

def generar_pdf_factura(factura_instance, request):
    """
    Genera el PDF de una factura ya existente.
    Recibe un objeto Factura y un request como argumentos.
    """
    # Usar factura_instance.valor_clp para convertir a palabras
    total_palabras = num2words(int(factura_instance.valor_clp), lang='es').replace("coma cero cero", "")
    fecha_formateada = date_format(factura_instance.fecha_emision, "d \\d\\e F \\d\\e Y")

    # Renderizar el template HTML del PDF
    html_string = render_to_string('certificados/factura_pdf.html', {
        'factura': factura_instance,
        'total_palabras': total_palabras,
        'fecha_formateada': fecha_formateada,
    })
    pdf_buffer = io.BytesIO()
    HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer