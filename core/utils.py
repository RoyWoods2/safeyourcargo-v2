# core/utils.py

from .models import LogActividad
import requests

# Importaciones necesarias para las funciones restantes
from django.core.mail import EmailMessage # Aunque no se usa directamente en las funciones restantes, si la necesitas para otras funciones en utils, déjala.
from django.template.loader import render_to_string
from weasyprint import HTML
from io import BytesIO
import os # Necesario para os.path.dirname, os.path.abspath, etc.

def registrar_actividad(usuario, mensaje):
    LogActividad.objects.create(usuario=usuario, mensaje=mensaje)

def obtener_dolar_observado(usuario: str, contrasena: str):
    url = (
        f"https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx?"
        f"user={usuario}&pass={contrasena}&function=GetSeries&timeseries=F073.TCO.PRE.Z.D"
    )

    try:
        response = requests.get(url)
        data = response.json()
        obs = data["Series"]["Obs"]
        ultimo = obs[-1]
        valor_dolar = float(ultimo["value"])
        fecha = ultimo["indexDateString"]
        return {"valor": valor_dolar, "fecha": fecha}
    except Exception as e:
        return {"error": str(e)}
    
# La función enviar_factura_y_certificado ha sido movida a core/emails.py
# y su lógica ha sido refactorizada para un mejor manejo de PDFs y comunicación.

def descargar_pdf_sii(url_pdf):
    """
    Descarga el PDF oficial timbrado desde facturacion.cl dado su URL.
    Devuelve el contenido en bytes o None si falla.
    """
    try:
        response = requests.get(url_pdf)
        if response.status_code == 200:
            return response.content
        else:
            print(f"⚠️ Error al descargar PDF SII: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Excepción al descargar PDF SII: {e}")
        return None

