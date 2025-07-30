import base64
import os
import re
import sys
from zeep import Client
from zeep.helpers import serialize_object
from core.models import Factura # Asegúrate de que esta importación sea correcta
from lxml import etree # Importado correctamente


# 🔐 Producción
FACTURACION_WSDL = 'http://ws.facturacion.cl/WSDS/wsplano.asmx?wsdl'
FACTURACION_USUARIO = 'SAFEYOURCARGOSPA'
FACTURACION_RUT = '78087058-3'  # ← tu RUT real de empresa
FACTURACION_CLAVE = '818bb129c1'  # ← clave de producción
FACTURACION_PUERTO = '0'


# 🔧 Limpieza de RUT para cumplir formato requerido
def limpiar_rut(rut: str) -> str:
    """
    Elimina puntos y normaliza el formato del RUT chileno.
    Ejemplo: '78.087.058-3' => '78087058-3'
    """
    rut = rut.replace(".", "").replace(" ", "").upper()
    if "-" not in rut and len(rut) > 1:
        return f"{rut[:-1]}-{rut[-1]}"
    return rut

# ------------------------------------------
# 🧾 Generar archivo plano de FACTURA EXENTA (DTE 34)
# (Esta función no se usa si envías XML, pero la mantenemos por si acaso)
# ------------------------------------------
def generar_txt_factura_exenta(factura: Factura) -> str:
    certificado = factura.certificado
    cliente = certificado.cliente

    # Datos del receptor
    rut_receptor = limpiar_rut(cliente.rut or "11111111-1")
    nombre = cliente.nombre or "CLIENTE"
    giro = "PARTICULAR"
    direccion = cliente.direccion or "SIN DIRECCION"
    comuna = cliente.region or "SANTIAGO"
    ciudad = cliente.ciudad or "SANTIAGO"
    correo = "correo@cliente.cl"
    if hasattr(certificado, "creado_por") and certificado.creado_por:
        correo = certificado.creado_por.correo or correo
    fecha = factura.fecha_emision.strftime("%Y-%m-%d")
    valor = int(factura.valor_clp)

    # ✅ ENCABEZADO
    encabezado = f"34;0;{fecha};0;0;{rut_receptor};{nombre};{giro};{direccion};{comuna};{ciudad};{correo};"

    # ✅ TOTALES
    totales = f"0;0;0;0;0;{valor};0;0;{valor};0;0;"

    # ✅ DETALLE
    descripcion = f"Despacho {certificado.ruta.ciudad_destino or 'Destino'} - C-{certificado.id}"
    desc_larga = f"Seguro de carga internacional - PRIMA USD ${factura.valor_usd}"
    detalle = f"1;SEG001;Seguro de Carga;1;{valor};0;0;0;0;{valor};0;INT1;UN;{desc_larga};"

    # ✅ FORMATO FINAL
    lineas = [
        "->Encabezado<-",
        encabezado,
        "->Totales<-", 
        totales,
        "->Detalle<-",
        detalle
    ]

    return "\r\n".join(lineas)

# ------------------------------------------
# 🚀 Enviar archivo a facturacion.cl vía WebService
# ------------------------------------------
def emitir_factura_exenta_cl_xml(factura: Factura) -> dict:
    try:
        # Generar XML
        xml_data = generar_xml_factura_exenta(factura)
        ruta_debug = f"/var/www/uniCloud/xml_facturas/FACTURA_C{factura.certificado.id}.xml"
        try:
            # Asegúrate de que el directorio exista antes de escribir el archivo
            os.makedirs(os.path.dirname(ruta_debug), exist_ok=True) 
            with open(ruta_debug, "w", encoding="utf-8") as f:
                f.write(xml_data)
            print(f"✅ XML de factura generado y guardado localmente en {ruta_debug}")
        except Exception as e:
            print(f"⚠️ No se pudo guardar el XML localmente: {str(e)}")

        # Codificar archivo en base64
        encoded_file = base64.b64encode(xml_data.encode('utf-8')).decode('utf-8')

        # Login info (base64 codificado)
        login_info = {
            'Usuario': base64.b64encode(FACTURACION_USUARIO.encode()).decode(),
            'Rut': base64.b64encode(FACTURACION_RUT.encode()).decode(),
            'Clave': base64.b64encode(FACTURACION_CLAVE.encode()).decode(),
            'Puerto': base64.b64encode(FACTURACION_PUERTO.encode()).decode(),
            'IncluyeLink': "1" # Solicitar que incluya el link del PDF en la respuesta
        }

        # Consumir WebService
        client = Client(FACTURACION_WSDL)
        response = client.service.Procesar(login=login_info, file=encoded_file, formato="2")
        respuesta_xml = serialize_object(response) # Serializa el objeto de respuesta completo
        print(f"DEBUG: Respuesta XML completa del WS: {respuesta_xml}") # Línea de depuración añadida

        # Inicializar folio y URL a None, se actualizarán si se encuentran en la respuesta
        folio_sii_obtenido = None
        url_pdf_sii_obtenida = None

        # Intentar extraer Folio
        folio_match = re.search(r'<Folio>(\d+)</Folio>', respuesta_xml)
        if folio_match:
            folio_sii_obtenido = int(folio_match.group(1))
            print(f"Folio SII extraído por regex: {folio_sii_obtenido}")

        # Intentar extraer urlCedible y decodificarla
        url_cedible_match = re.search(r'<urlCedible>(.*?)</urlCedible>', respuesta_xml)
        if url_cedible_match:
            base64_url = url_cedible_match.group(1)
            try:
                url_pdf_sii_obtenida = base64.b64decode(base64_url.encode('utf-8')).decode('utf-8')
                print(f"URL PDF SII (cedible) extraída y decodificada: {url_pdf_sii_obtenida}")
            except Exception as e:
                print(f"❌ Error al decodificar URL cedible Base64: {e}")
                url_pdf_sii_obtenida = None # Asegurarse de que sea None si falla la decodificación
        else:
            print("DEBUG: No se encontró <urlCedible> en la respuesta XML.")


        # Determinar estado basado en contenido
        estado = "fallida" # Estado por defecto si no se encuentra un match claro
        if "<Resultado>True</Resultado>" in respuesta_xml:
            estado = "exito"
            print(f"✅ Emisión SII exitosa para factura C-{factura.certificado.id}")
        elif "Ya existe el Documento" in respuesta_xml:
            estado = "duplicado"
            print(f"⚠️ Documento duplicado para factura C-{factura.certificado.id}.")
            # Si es duplicado y tenemos el folio, intentar obtener el link oficial
            if factura.folio_sii: # Usar el folio que ya tiene la factura (si lo tiene)
                try:
                    link_result = obtener_link_pdf_boleta(factura.folio_sii)
                    if link_result['success']:
                        url_pdf_sii_obtenida = link_result['url'] # Actualizar con el link recuperado
                        print(f"URL PDF recuperada para duplicado usando folio existente: {url_pdf_sii_obtenida}")
                except Exception as e_link:
                    print(f"❌ Error al intentar recuperar URL para duplicado: {e_link}")
        elif "<Resultado>False</Resultado>" in respuesta_xml:
            estado = "fallida"
            print(f"❌ Emisión SII fallida para factura C-{factura.certificado.id}. Respuesta detallada: {respuesta_xml}")
        else:
            estado = "fallida_inesperada"
            print(f"❌ Respuesta del WS no contiene Resultado True/False o Ya existe (estado inesperado): {respuesta_xml}")


        # Guardar estado, folio y URL en la factura
        factura.estado_emision = estado
        if folio_sii_obtenido:
            factura.folio_sii = folio_sii_obtenido
        if url_pdf_sii_obtenida:
            factura.url_pdf_sii = url_pdf_sii_obtenida
        factura.save() # Guarda los cambios en la instancia de la factura

        return {
            'success': estado == "exito", # Solo es éxito si el estado final es 'exito'
            'estado_emision': estado,
            'folio_sii': factura.folio_sii, # Retorna el folio que ahora está en la factura
            'url_pdf_sii': factura.url_pdf_sii, # Retorna la URL que ahora está en la factura
            'respuesta_completa': respuesta_xml # Para depuración
        }

    except Exception as e:
        # Captura cualquier excepción que ocurra durante el proceso (conexión, parsing, etc.)
        factura.estado_emision = "fallida_exception"
        factura.save() # Guarda el estado de falla
        print(f"❌ Error crítico en emitir_factura_exenta_cl_xml: {e}")
        return {'success': False, 'error': str(e), 'estado_emision': 'fallida_exception'}


# 🔗 Obtener el PDF oficial desde facturacion.cl
# ------------------------------------------
def obtener_link_pdf_boleta(folio: int, tipo_dte: int = 34) -> dict:
    try:
        client = Client(FACTURACION_WSDL)

        login_info = {
            'Usuario': base64.b64encode(FACTURACION_USUARIO.encode()).decode(),
            'Rut': base64.b64encode(FACTURACION_RUT.encode()).decode(),
            'Clave': base64.b64encode(FACTURACION_CLAVE.encode()).decode(),
            'Puerto': base64.b64encode(FACTURACION_PUERTO.encode()).decode()
        }

        response = client.service.ObtenerLink(
            login=login_info,
            tipoDte=str(tipo_dte),
            folio=str(folio)
        )

        if hasattr(response, 'Mensaje') and response.Mensaje:
            url_base64 = response.Mensaje
            url_decodificada = base64.b64decode(url_base64.encode()).decode()
            print(f"URL de PDF obtenida por ObtenerLink para folio {folio}: {url_decodificada}")
            return {'success': True, 'url': url_decodificada}

        return {'success': False, 'error': 'No se encontró el campo Mensaje en la respuesta para ObtenerLink.'}

    except Exception as e:
        print(f"❌ Error en obtener_link_pdf_boleta para folio {folio}: {e}")
        return {'success': False, 'error': str(e)}

def normalizar_rut(rut: str) -> str:
    """
    Devuelve el RUT con guion y sin puntos. Ej: '60.905.000-K' -> '60905000-K'
    """
    rut = rut.replace(".", "").replace(" ", "").upper()
    if "-" not in rut and len(rut) > 1:
        return f"{rut[:-1]}-{rut[-1]}"
    return rut

def generar_xml_factura_exenta(factura: Factura) -> str:
    from lxml import etree
    import re
    # Ya está importado, no es necesario importar de nuevo: from core.services.facturacion_cl import limpiar_rut

    certificado = factura.certificado
    cliente = certificado.cliente

    # RUT limpio
    rut_limpio = limpiar_rut(cliente.rut or "11111111-1")
    cdg_int = re.sub(r'\D', '', cliente.rut or "11111111-1")  # Solo dígitos

    root = etree.Element("DTE", version="1.0")
    documento = etree.SubElement(root, "Documento", ID="F1T34")

    # Encabezado
    encabezado = etree.SubElement(documento, "Encabezado")

    iddoc = etree.SubElement(encabezado, "IdDoc")
    etree.SubElement(iddoc, "TipoDTE").text = "34"

    # --- CAMBIO REALIZADO AQUÍ ---
    # Se envía el folio como "0" para solicitar a facturacion.cl que asigne
    # el siguiente número de folio correlativo y autorizado por el SII.
    #
    # --- ANTES ---
    # etree.SubElement(iddoc, "Folio").text = str(factura.folio_sii)
    #
    # --- DESPUÉS ---
    etree.SubElement(iddoc, "Folio").text = "0"

    etree.SubElement(iddoc, "FchEmis").text = factura.fecha_emision.strftime("%Y-%m-%d")

    emisor = etree.SubElement(encabezado, "Emisor")
    etree.SubElement(emisor, "RUTEmisor").text = "78087058-3"
    etree.SubElement(emisor, "RznSoc").text = "SAFE YOUR CARGO"
    etree.SubElement(emisor, "GiroEmis").text = "Servicios Logísticos"
    etree.SubElement(emisor, "Acteco").text = "515009"
    etree.SubElement(emisor, "DirOrigen").text = "Pedro de Valdivia 25"
    etree.SubElement(emisor, "CmnaOrigen").text = "Providencia"
    etree.SubElement(emisor, "CiudadOrigen").text = "Santiago"

    receptor = etree.SubElement(encabezado, "Receptor")
    etree.SubElement(receptor, "RUTRecep").text = rut_limpio
    etree.SubElement(receptor, "CdgIntRecep").text = cdg_int
    etree.SubElement(receptor, "RznSocRecep").text = cliente.nombre or "CLIENTE"
    etree.SubElement(receptor, "GiroRecep").text = "SERVICIO"
    etree.SubElement(receptor, "DirRecep").text = cliente.direccion or "SIN DIRECCIÓN"
    etree.SubElement(receptor, "CmnaRecep").text = cliente.region or "SANTIAGO"
    etree.SubElement(receptor, "CiudadRecep").text = cliente.ciudad or "SANTIAGO"

    totales = etree.SubElement(encabezado, "Totales")
    monto = int(factura.valor_clp or 0)
    etree.SubElement(totales, "MntExe").text = str(monto)
    etree.SubElement(totales, "MntTotal").text = str(monto)

    # Detalle
    detalle = etree.SubElement(documento, "Detalle")
    etree.SubElement(detalle, "NroLinDet").text = "1"
    cdgitem = etree.SubElement(detalle, "CdgItem")
    etree.SubElement(cdgitem, "TpoCodigo").text = "INT1"
    etree.SubElement(cdgitem, "VlrCodigo").text = "SEG001"
    etree.SubElement(detalle, "IndExe").text = "1"
    etree.SubElement(detalle, "NmbItem").text = "Seguro de Carga"
    etree.SubElement(detalle, "QtyItem").text = "1"
    etree.SubElement(detalle, "UnmdItem").text = "UN"
    etree.SubElement(detalle, "PrcItem").text = str(monto)
    etree.SubElement(detalle, "MontoItem").text = str(monto)

    return etree.tostring(root, encoding="utf-8", xml_declaration=True, pretty_print=True).decode("utf-8")