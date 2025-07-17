# core/emails.py

import os
import uuid
import requests # <--- Nueva importación para descargar el PDF del SII
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from email.mime.image import MIMEImage
from django.utils.html import strip_tags
from datetime import date
import io # Para manejar el contenido descargado del PDF

# Asumo que Factura se puede importar desde tus modelos para el type hinting
# from .models import Factura # Descomenta si usas Factura directamente aquí

def enviar_certificado_y_factura(certificado, pdf_cert, factura_obj, pdf_fact, destinatarios_extra=None):
    """
    Recibe el certificado, su PDF en memoria, el objeto Factura (completo),
    envía el correo con los adjuntos y limpia los archivos.
    Prioriza el PDF oficial del SII para la factura.
    """
    temp_dir = os.path.join(settings.BASE_DIR, 'temp_pdfs')
    os.makedirs(temp_dir, exist_ok=True)

    uid = uuid.uuid4().hex[:6]
    cert_path = os.path.join(temp_dir, f'certificado_{certificado.id}_{uid}.pdf')
    fact_path = os.path.join(temp_dir, f'factura_{factura_obj.id}_{uid}.pdf') # Usa el ID de la factura

    try:
        # Guardar PDF del certificado
        with open(cert_path, 'wb') as f:
            f.write(pdf_cert.getvalue())

        # --- Lógica para el PDF de la factura ---
        factura_pdf_a_adjuntar = None # BytesIO del PDF de la factura
        factura_pdf_filename = f'factura_{factura_obj.id}.pdf'

        # Intenta descargar el PDF del SII si está disponible y la emisión fue exitosa
        if factura_obj.estado_emision == 'exito' and factura_obj.url_pdf_sii:
            try:
                response = requests.get(factura_obj.url_pdf_sii, stream=True)
                response.raise_for_status() # Lanza un error para códigos de estado HTTP erróneos
                factura_pdf_a_adjuntar = io.BytesIO(response.content)
                print(f"✅ Descargado PDF oficial del SII para factura {factura_obj.id} desde {factura_obj.url_pdf_sii}")
            except requests.exceptions.RequestException as e:
                print(f"❌ Error al descargar PDF oficial del SII para factura {factura_obj.id}: {e}. Usando PDF local.")
                # Si falla la descarga, se usa el PDF local (generado por generar_pdf_factura en utils_pdf.py)
                # NOTA: Necesitarás que generar_pdf_factura devuelva su BytesIO aquí
                # Si tu generar_pdf_factura aún recibe 'certificado', tendrías que llamarla aquí
                # o modificar la vista para que te pase ambos PDFs (local y oficial).
                # Para simplificar, asumo que 'pdf_fact' (el local) podría pasarse también como un argumento opcional
                # o regenerarse aquí si la descarga falla y es absolutamente necesario.
                # En la vista, generamos pdf_fact y lo pasamos, así que lo usaremos si falla el SII.
                # Esto es un placeholder, la vista ya te está pasando 'pdf_fact' como `factura_pdf_buffer`
                # en el ejemplo de la vista. Esto significa que necesitas cambiar la firma de esta función
                # para aceptar 'pdf_fact_local' además de 'factura_obj'.
                # Vamos a ajustar la firma y la llamada en la vista.

                # CORRECCIÓN IMPORTANTE: Si la vista genera un pdf_fact_local y lo pasa, lo debemos recibir aquí
                # y usarlo si el del SII falla.
                # Si 'pdf_fact' NO es pasado a esta función, tendrías que llamarlo aquí:
                # from core.utils_pdf import generar_pdf_factura
                # factura_pdf_a_adjuntar = generar_pdf_factura(certificado, request) # CUIDADO: request no está aquí.
                # Por eso es mejor que la vista YA TE PASE EL PDF LOCAL
                
                # Para que funcione con la vista actual, DEBES CAMBIAR LA FIRMA DE ESTA FUNCIÓN
                # para que reciba el pdf_fact LOCAL también.
                # Revertimos el cambio de firma para reflejar lo que la vista está haciendo actualmente:
                # La vista pasa `pdf_fact=factura_pdf_buffer`
                # Entonces, esta función debería tener `pdf_fact_local` como parámetro si quieres usarlo de fallback.
                # Para mantener la simplicidad, y basándonos en tu snippet de la vista, la vista está llamando
                # `enviar_certificado_y_factura(..., pdf_cert=certificado_pdf_buffer, pdf_fact=factura_pdf_buffer, ...)`
                # Esto significa que `pdf_fact` *ya es* el buffer del PDF local.
                # Así que la lógica será:
                # 1. Intentar descargar SII PDF.
                # 2. Si falla la descarga, usar el `pdf_fact` que ya se recibió.
                factura_pdf_a_adjuntar = pdf_fact # Usar el PDF local pasado como argumento
        else:
            # Si no hubo éxito en la emisión SII o no hay URL, usar el PDF local
            factura_pdf_a_adjuntar = pdf_fact # Usar el PDF local pasado como argumento
            print(f"ℹ️ Usando PDF local para factura {factura_obj.id} (no hay URL del SII o emisión fallida).")
        
        # Guarda el PDF de la factura (sea del SII o local) en un archivo temporal para adjuntarlo
        if factura_pdf_a_adjuntar:
            with open(fact_path, 'wb') as f:
                f.write(factura_pdf_a_adjuntar.getvalue())
        else:
            print(f"⚠️ Advertencia: No se pudo obtener ningún PDF para la factura {factura_obj.id}. No se adjuntará.")


        # Correos fijos
        correos_fijos = [
            "Contacto@safeyourcargo.com",
            "Finanzas@safeyourcargo.com",
            "Jgonzalez@safeyourcargo.com",
            "finanzas.safeyourcargo@gmail.com",
            "hans.arancibia@live.com"
        ]

        # Agregar el correo del creador del certificado si existe
        if certificado.creado_por and certificado.creado_por.correo:
            correos_fijos.append(certificado.creado_por.correo)

        # Unir con destinatarios adicionales si hay
        destinatarios = list(set(correos_fijos + (destinatarios_extra or [])))

        # --- Preparar el contenido HTML del correo ---
        context = {
            'certificado': certificado,
            'factura': factura_obj, # Pasa la factura también al template
            'current_year': date.today().year,
        }
        html_content = render_to_string('emails/certificado_email.html', context)
        text_content = strip_tags(html_content) 

        # Crear el objeto EmailMultiAlternatives
        email = EmailMultiAlternatives(
            subject=f"📄 Documentos de Certificado C-{certificado.id} y Factura N°{factura_obj.folio_sii or factura_obj.numero} - SafeYourCargo", # Asunto más detallado
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=destinatarios
        )
        
        email.attach_alternative(html_content, "text/html")

        # --- Adjuntar la imagen del logo embebida ---
        logo_path = os.path.join(settings.BASE_DIR, 'core', 'static', 'img', 'safe_logo.png')
        if os.path.exists(logo_path):
            with open(logo_path, 'rb') as f:
                logo_data = f.read()
                logo_mime = MIMEImage(logo_data)
                logo_mime.add_header('Content-ID', '<logo_safeyourcargo>') 
                email.attach(logo_mime)
        else:
            print(f"⚠️ Advertencia: No se encontró el logo en {logo_path}. El correo se enviará sin logo.")

        # Adjuntar los archivos PDF
        email.attach_file(cert_path)
        if factura_pdf_a_adjuntar: # Solo adjuntar si se pudo obtener un PDF para la factura
            email.attach_file(fact_path)

        email.send(fail_silently=False)
        print(f"✅ Correo enviado a {destinatarios}")

    except Exception as e:
        print(f"❌ Error al enviar correo para el certificado C-{certificado.id}: {e}")
        # Aquí puedes decidir si quieres que el error se propague o solo loggearlo
        # raise # Descomenta si quieres que la excepción se lance de nuevo
    finally:
        # Limpiar archivos temporales de forma segura
        try:
            if os.path.exists(cert_path):
                os.remove(cert_path)
            if os.path.exists(fact_path):
                os.remove(fact_path)
            if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                os.rmdir(temp_dir)
        except Exception as err:
            print(f"⚠️ No se pudo eliminar archivos temporales para el certificado C-{certificado.id}: {err}")