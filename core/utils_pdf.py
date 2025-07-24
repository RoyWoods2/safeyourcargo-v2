import io
from weasyprint import HTML
from django.template.loader import render_to_string
from num2words import num2words
from django.utils.formats import date_format
from decimal import Decimal
from datetime import date
from .models import Factura, CertificadoTransporte # Asegúrate de importar CertificadoTransporte
from .utils import obtener_dolar_observado

def generar_pdf_certificado(certificado, request):
    html_string = render_to_string('certificados/certificado_pdf.html', {
        'certificado': certificado,
    })
    pdf_buffer = io.BytesIO()
    HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer

def generar_pdf_factura(certificado, request):
    """
    Genera el PDF de la factura.
    Asegura que el certificado tenga el valor_prima_estimado calculado y guardado
    antes de llamar a esta función, lo cual ya se hace en views.py.
    """
    # Recupera o crea la instancia de Factura asociada al certificado.
    # Los cálculos de valor_usd, tipo_cambio y valor_clp se realizan aquí
    # para asegurar que el PDF refleje los valores correctos al momento de su generación.
    factura_instance, _ = Factura.objects.get_or_create(
        certificado=certificado,
        defaults={
            'numero': Factura.objects.count() + 1,
            'razon_social': certificado.cliente.nombre,
            'rut': certificado.cliente.rut,
            'direccion': certificado.cliente.direccion,
            'comuna': certificado.cliente.region or 'Por definir',
            'ciudad': certificado.cliente.ciudad,
            'valor_usd': certificado.tipo_mercancia.valor_prima, # ✅ CORRECCIÓN: Usar valor_prima de TipoMercancia
            'fecha_emision': certificado.fecha_partida or date.today(),
        }
    )

    # ✅ CORRECCIÓN: Usar certificado.tipo_mercancia.valor_prima para el valor_usd de la factura
    factura_instance.valor_usd = certificado.tipo_mercancia.valor_prima 

    # Obtener el tipo de cambio del dólar
    resultado = obtener_dolar_observado("hans.arancibia@live.com", "Rhad19326366.")
    dolar = Decimal(resultado.get("valor", '950.00')) # Valor por defecto si no se puede obtener

    # Calcular y asignar valor_clp
    factura_instance.tipo_cambio = dolar
    factura_instance.valor_clp = (factura_instance.valor_usd or Decimal('0.0')) * dolar
    factura_instance.save() # Guarda la factura con el valor_clp actualizado para el PDF

    # Usar factura_instance.valor_clp para convertir a palabras
    total_palabras = num2words(int(factura_instance.valor_clp), lang='es').replace("coma cero cero", "")
    fecha_formateada = date_format(factura_instance.fecha_emision, "d \\d\\e F \\d\\e Y")

    # Renderizar el template HTML del PDF
    html_string = render_to_string('certificados/factura_pdf.html', {
        'factura': factura_instance, # Asegurarse de que la instancia correcta de Factura se pase al template
        'total_palabras': total_palabras, # Pasar total_palabras al template si es necesario
        'fecha_formateada': fecha_formateada, # Pasar la fecha formateada al template si es necesario
    })
    pdf_buffer = io.BytesIO()
    HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer
