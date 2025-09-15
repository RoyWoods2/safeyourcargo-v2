import os
import uuid
import requests
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from email.mime.image import MIMEImage
from django.utils.html import strip_tags
from datetime import date
import io

def _obtener_destinatarios(certificado, destinatarios_extra=None):
    """Función auxiliar para obtener la lista completa de destinatarios."""
    correos_fijos = [
        "Contacto@safeyourcargo.com",
        "Finanzas@safeyourcargo.com",
        "Jgonzalez@safeyourcargo.com",
        "finanzas.safeyourcargo@gmail.com",
        "hans.arancibia@live.com",
        "jaimevalpo2020@gmail.com"
    ]
    if certificado.creado_por and certificado.creado_por.correo:
        correos_fijos.append(certificado.creado_por.correo)
    
    return list(set(correos_fijos + (destinatarios_extra or [])))

def _preparar_email_base(subject, context, destinatarios):
    """Función auxiliar para preparar el objeto base del correo."""
    html_content = render_to_string('emails/certificado_email.html', context)
    text_content = strip_tags(html_content) 

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=destinatarios
    )
    email.attach_alternative(html_content, "text/html")
    
    # Adjuntar la imagen del logo embebida
    logo_path = os.path.join(settings.BASE_DIR, 'core', 'static', 'img', 'safe_logo.png')
    if os.path.exists(logo_path):
        with open(logo_path, 'rb') as f:
            logo_data = f.read()
        logo_mime = MIMEImage(logo_data)
        logo_mime.add_header('Content-ID', '<logo_safeyourcargo>') 
        email.attach(logo_mime)
    else:
        print(f"⚠️ Advertencia: No se encontró el logo en {logo_path}. El correo se enviará sin logo.")
        
    return email

def enviar_certificado_y_factura(certificado, pdf_cert, factura_obj, pdf_fact, destinatarios_extra=None):
    """
    Envía el correo con el certificado y la factura.
    """
    temp_dir = os.path.join(settings.BASE_DIR, 'temp_pdfs')
    os.makedirs(temp_dir, exist_ok=True)
    uid = uuid.uuid4().hex[:6]
    cert_path = os.path.join(temp_dir, f'certificado_{certificado.id}_{uid}.pdf')
    fact_path = os.path.join(temp_dir, f'factura_{factura_obj.id}_{uid}.pdf')

    try:
        with open(cert_path, 'wb') as f:
            f.write(pdf_cert.getvalue())
        
        factura_pdf_a_adjuntar = pdf_fact
        if factura_obj.estado_emision == 'exito' and factura_obj.url_pdf_sii:
            try:
                response = requests.get(factura_obj.url_pdf_sii, stream=True)
                response.raise_for_status()
                factura_pdf_a_adjuntar = io.BytesIO(response.content)
            except requests.exceptions.RequestException as e:
                print(f"❌ Error al descargar PDF del SII: {e}. Usando PDF local.")
        
        if factura_pdf_a_adjuntar:
            with open(fact_path, 'wb') as f:
                f.write(factura_pdf_a_adjuntar.getvalue())
        
        destinatarios = _obtener_destinatarios(certificado, destinatarios_extra)
        
        subject = f"📄 Documentos de Certificado C-{certificado.id} y Factura N°{factura_obj.folio_sii or factura_obj.numero} - SafeYourCargo"
        context = {
            'certificado': certificado,
            'factura': factura_obj,
            'current_year': date.today().year,
        }

        email = _preparar_email_base(subject, context, destinatarios)
        email.attach_file(cert_path)
        if factura_pdf_a_adjuntar:
            email.attach_file(fact_path)
        
        email.send(fail_silently=False)
        print(f"✅ Correo enviado a {destinatarios}")
    
    except Exception as e:
        print(f"❌ Error al enviar correo para el certificado C-{certificado.id}: {e}")
    finally:
        try:
            if os.path.exists(cert_path): os.remove(cert_path)
            if os.path.exists(fact_path): os.remove(fact_path)
            temp_dir_contents = os.listdir(temp_dir) if os.path.exists(temp_dir) else []
            if not temp_dir_contents: os.rmdir(temp_dir)
        except Exception as err:
            print(f"⚠️ No se pudo eliminar archivos temporales para el certificado C-{certificado.id}: {err}")


def enviar_solo_certificado(certificado, pdf_cert, destinatarios_extra=None):
    """
    Envía un correo con solo el PDF del certificado.
    Esta función es para clientes que manejan su propia facturación.
    """
    temp_dir = os.path.join(settings.BASE_DIR, 'temp_pdfs')
    os.makedirs(temp_dir, exist_ok=True)
    uid = uuid.uuid4().hex[:6]
    cert_path = os.path.join(temp_dir, f'certificado_{certificado.id}_{uid}.pdf')

    try:
        with open(cert_path, 'wb') as f:
            f.write(pdf_cert.getvalue())

        destinatarios = _obtener_destinatarios(certificado, destinatarios_extra)

        subject = f"📄 Documento de Certificado C-{certificado.id} - SafeYourCargo"
        context = {
            'certificado': certificado,
            'factura': None, # Pasa None para que el template sepa que no hay factura
            'current_year': date.today().year,
        }

        email = _preparar_email_base(subject, context, destinatarios)
        email.attach_file(cert_path)
        
        email.send(fail_silently=False)
        print(f"✅ Correo con solo certificado enviado a {destinatarios}")
        
    except Exception as e:
        print(f"❌ Error al enviar correo con solo certificado para C-{certificado.id}: {e}")
    finally:
        try:
            if os.path.exists(cert_path): os.remove(cert_path)
            temp_dir_contents = os.listdir(temp_dir) if os.path.exists(temp_dir) else []
            if not temp_dir_contents: os.rmdir(temp_dir)
        except Exception as err:
            print(f"⚠️ No se pudo eliminar archivo temporal para el certificado C-{certificado.id}: {err}")