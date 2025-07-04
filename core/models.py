from django.db import models
from django.contrib.auth.models import AbstractUser
from decimal import Decimal
from datetime import date


class Usuario(AbstractUser):
    pendiente_aprobacion = models.BooleanField(default=False)
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE, related_name='usuarios', null=True, blank=True)
    rol = models.CharField(max_length=50, choices=[
        ('Administrador', 'Administrador'),
        ('Usuario', 'Usuario'),
        ('Revendedor', 'Revendedor')
    ], default='Usuario')

    # ⚡️ Campo que indica quién creó este usuario
    creado_por = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='usuarios_creados')
    correo = models.EmailField()
    telefono = models.CharField(max_length=20)
    def __str__(self):
        return f"{self.username} - {self.rol}"

    
    
class Cliente(models.Model):
    TIPO_CLIENTE = [
        ('empresa', 'Empresa'),
        ('persona', 'Persona'),
    ]
    TIPO_ALCANCE = [
        ('minorista', 'Minorista'),
    ]

    tipo_cliente = models.CharField(max_length=10, choices=TIPO_CLIENTE, default='empresa')
    nombre = models.CharField(max_length=255, unique=True)
    rut = models.CharField(max_length=15, unique=True)

    direccion = models.TextField()
    pais = models.CharField(max_length=100)
    ciudad = models.CharField(max_length=100)
    region = models.CharField(max_length=100)

    tasa = models.DecimalField(max_digits=10, decimal_places=4)
    valor_minimo = models.DecimalField(max_digits=10, decimal_places=2)

    tasa_congelada = models.DecimalField(max_digits=10, decimal_places=2)
    valor_minimo_congelado = models.DecimalField(max_digits=10, decimal_places=4)

    tramo_cobro = models.PositiveIntegerField()
    creado_por = models.ForeignKey(Usuario, null=True, blank=True, on_delete=models.SET_NULL, related_name='clientes_creados')

    def __str__(self):
        return self.nombre
    
class Pais(models.Model):
    nombre = models.CharField(max_length=100)
    sigla = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.nombre


class Ciudad(models.Model):
    pais = models.ForeignKey(Pais, on_delete=models.CASCADE, related_name='ciudades')
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.nombre} ({self.pais.nombre})"
    
class CertificadoTransporte(models.Model):
    poliza = models.CharField(default="01930324AA", max_length=20)
    compania = models.CharField(default="SafeYourCargo", max_length=50)

    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE) # Asumiendo que Cliente está definido
    fecha_partida = models.DateField()
    fecha_llegada = models.DateField()

    # Relación uno a uno con otros modelos
    ruta = models.OneToOneField('Ruta', on_delete=models.CASCADE) # Asumiendo que Ruta está definido
    metodo_embarque = models.OneToOneField('MetodoEmbarque', on_delete=models.CASCADE) # Asumiendo que MetodoEmbarque está definido
    tipo_mercancia = models.OneToOneField('TipoMercancia', on_delete=models.CASCADE)
    viaje = models.OneToOneField('Viaje', on_delete=models.CASCADE) # Asumiendo que Viaje está definido
    notas = models.OneToOneField('NotasNumeros', on_delete=models.CASCADE) # Asumiendo que NotasNumeros está definido

    # Campos de prima y auditoria
    valor_prima_estimado = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    valor_prima_cobro = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    valor_prima_pago = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)

    creado_por = models.ForeignKey(
        'Usuario', # Asumiendo que Usuario está definido
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='certificados_creados',
        verbose_name='Creado por'
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Última modificación'
    )

    class Meta:
        verbose_name = 'Certificado de Transporte'
        verbose_name_plural = 'Certificados de Transporte'
        ordering = ['-fecha_creacion']

    def calcular_valor_asegurado(self):
        # Accede a los valores de tipo_mercancia para el cálculo
        return (self.tipo_mercancia.valor_fca + self.tipo_mercancia.valor_flete) * Decimal('1.10')

    def calcular_valor_prima(self):
        # Accede a las relaciones para obtener los datos necesarios
        tipo_carga = self.metodo_embarque.tipo_carga
        monto = self.calcular_valor_asegurado()

        if tipo_carga == "PolizaCongelada":
            tasa = self.cliente.tasa_congelada
            minimo = self.cliente.valor_minimo_congelado
        else:
            tasa = self.cliente.tasa
            minimo = self.cliente.valor_minimo

        # --- Tus líneas de depuración ---
        print(f"\n--- DEBUG CÁLCULO DE PRIMA (Desde CertificadoTransporte.save()) ---")
        print(f"DEBUG: Monto Asegurado (monto): {monto}")
        print(f"DEBUG: Tasa del Cliente (tasa): {tasa}")
        print(f"DEBUG: Cálculo de Prima (tasa / 100): {tasa / 100}")
        # ----------------------------------------

        prima = monto * (tasa / 100)
        print(f"DEBUG: Resultado final de la Prima: {prima}")
        print(f"--- FIN DEBUG ---")
        return max(prima, minimo)

    # ✅ AÑADIDO: Método save() para calcular la prima automáticamente
    def save(self, *args, **kwargs):
        # Esta bandera 'recalculate_prima' es opcional, puedes usarla si quieres
        # forzar el recálculo en actualizaciones, o simplemente siempre recalcular.
        recalculate_prima = kwargs.pop('recalculate_prima', False)

        # Si es una nueva instancia (sin PK) o se fuerza el recálculo
        if not self.pk or recalculate_prima:
            try:
                # Calcula la prima y asigna el valor
                self.valor_prima_estimado = self.calcular_valor_prima()
                
                # Si valor_prima_cobro debe ser igual a valor_prima_estimado al crearse
                if self.valor_prima_cobro is None: # Asegúrate de que solo se asigne si no tiene un valor ya
                    self.valor_prima_cobro = self.valor_prima_estimado
            except Exception as e:
                # Importante: Maneja errores si las relaciones (tipo_mercancia, cliente, etc.)
                # aún no están asignadas al objeto 'self' cuando save() es llamado.
                print(f"ERROR al calcular prima en CertificadoTransporte.save(): {e}")
                # Puedes optar por dejar los campos en None, o asignar un valor predeterminado como 0
                self.valor_prima_estimado = Decimal('0.00')
                self.valor_prima_cobro = Decimal('0.00')

        super().save(*args, **kwargs) # Llama al método save() original de Django

    def __str__(self):
        return f"C-{self.id} - {self.cliente.nombre if self.cliente else 'Sin cliente'}"
    
    
    
class Ruta(models.Model):
    pais_origen = models.CharField(max_length=100)
    ciudad_origen = models.CharField(max_length=100)
    pais_destino = models.CharField(max_length=100)
    ciudad_destino = models.CharField(max_length=100)
    
class MetodoEmbarque(models.Model):
    MODO_CHOICES = [
        ('Aereo', 'Aéreo'),
        ('Maritimo', 'Marítimo'),
        ('TerrestreFerroviario', 'Terrestre y/o Ferroviario'),
        ('MarRojo', 'Marítimo vía Mar Rojo')
    ]
    TIPO_CARGA_CHOICES = [
        ('PolizaGeneral', 'Póliza para Carga General y/o Carga Seca'),
        ('PolizaCongelada', 'Póliza para Carga Congelada'),
    ]
    CLAUSULA_CHOICES = [('A', 'Tipo A'), ('C', 'Tipo C')]

    modo_transporte = models.CharField(max_length=50, choices=MODO_CHOICES)
    tipo_carga = models.CharField(max_length=50, choices=TIPO_CARGA_CHOICES)
    clausula = models.CharField(max_length=10, choices=CLAUSULA_CHOICES)

    # AÉREO
    tipo_embalaje_aereo = models.CharField(max_length=100, blank=True, null=True)
    otro_embalaje_aereo = models.CharField(max_length=100, blank=True, null=True)

    # MARÍTIMO
    embalaje_maritimo = models.CharField(max_length=10, choices=[('FCL', 'FCL'), ('LCL', 'LCL')], blank=True, null=True)
    tipo_container_maritimo = models.CharField(max_length=50, blank=True, null=True)
    tipo_embalaje_lcl = models.CharField(max_length=100, blank=True, null=True)
    otro_embalaje_lcl = models.CharField(max_length=100, blank=True, null=True)

    # TERRESTRE
    tipo_embalaje_terrestre = models.CharField(max_length=100, blank=True, null=True)
    otro_embalaje_terrestre = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.modo_transporte} - {self.tipo_carga}"

class TipoMercancia(models.Model):
    TIPO_CHOICES = [
        ('Maquinaria', 'Maquinaria y aparatos mecánicos, equipos electrónicos en FCL o LCL'),
        ('General', 'Mercancía General'),
        ('Aeronaves', 'Piezas de Aeronaves'),
        ('Hierro', 'Productos de hierro y acero'),
    ]

    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    valor_fca = models.DecimalField(max_digits=12, decimal_places=2)
    valor_flete = models.DecimalField(max_digits=12, decimal_places=2)
    valor_prima = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    monto_asegurado = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def calcular_monto_asegurado(self):
        return (self.valor_fca + self.valor_flete) * Decimal("1.10")
    
    def save(self, *args, **kwargs):
        self.monto_asegurado = self.calcular_monto_asegurado()
        super().save(*args, **kwargs)

class Viaje(models.Model):
    nombre_avion = models.CharField(max_length=100)
    numero_viaje = models.CharField(max_length=100)
    vuelo_origen_pais = models.CharField(max_length=100)
    vuelo_origen_ciudad = models.CharField(max_length=100)
    aeropuerto_origen = models.CharField(max_length=100)
    vuelo_destino_pais = models.CharField(max_length=100)
    vuelo_destino_ciudad = models.CharField(max_length=100)
    aeropuerto_destino = models.CharField(max_length=100)
    descripcion_carga = models.TextField()
    vuelo_origen_pais_fk = models.ForeignKey(Pais, on_delete=models.CASCADE, related_name='viajes_origen', null=True, blank=True)
    vuelo_destino_pais_fk = models.ForeignKey(Pais, on_delete=models.CASCADE, related_name='viajes_destino', null=True, blank=True)
    

class NotasNumeros(models.Model):
    referencia = models.CharField(max_length=200, blank=True, null=True)
    guia_carga = models.CharField(max_length=100)
    numero_factura = models.CharField(max_length=100, blank=True, null=True)
    notas = models.TextField(blank=True, null=True)


class Factura(models.Model):
    certificado = models.OneToOneField('CertificadoTransporte', on_delete=models.CASCADE, related_name='factura')
    numero = models.PositiveIntegerField(unique=True)
    fecha_emision = models.DateField(default=date.today)

    valor_usd = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.0'))
    tipo_cambio = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('950.0'))
    valor_clp = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.0'))

    razon_social = models.CharField(max_length=255)
    rut = models.CharField(max_length=20)
    direccion = models.CharField(max_length=255)
    comuna = models.CharField(max_length=100)
    ciudad = models.CharField(max_length=100)

    folio_sii = models.PositiveIntegerField(null=True, blank=True, unique=True)
    observaciones = models.TextField(blank=True, null=True)
    estado_emision = models.CharField(max_length=20, null=True, blank=True, choices=[
    ('pendiente', 'Pendiente'),
    ('exito', 'Emitida exitosamente'),
    ('fallida', 'Con error'),
    ('duplicado', 'Folio ya usado')
])
def save(self, *args, **kwargs):
    envio_automatico = self.pk is None
    self.valor_clp = self.valor_usd * self.tipo_cambio
    super().save(*args, **kwargs)

    if envio_automatico:
        try:
            from core.utils import enviar_factura_y_certificado
            enviar_factura_y_certificado(self)
        except Exception as e:
            print(f"❌ Error al enviar automáticamente correo con factura y certificado: {e}")


# ✅ FUNCIÓN LIBRE (fuera del modelo)
def obtener_siguiente_folio():
    from .models import Factura
    folio_min = 545
    folio_max = 10000
    usados = Factura.objects.exclude(folio_sii__isnull=True).values_list('folio_sii', flat=True)
    for folio in range(folio_min, folio_max + 1):
        if folio not in usados:
            return folio
    raise Exception("No hay folios disponibles en el rango 540–10000.")


class CAF(models.Model):
    tipo_dte = models.PositiveSmallIntegerField()  # e.g. 34
    desde = models.PositiveIntegerField()
    hasta = models.PositiveIntegerField()
    fecha_autorizacion = models.DateField()
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"DTE {self.tipo_dte}: {self.desde}–{self.hasta}"


class Cobranza(models.Model):
    certificado = models.OneToOneField('CertificadoTransporte', on_delete=models.CASCADE, related_name='cobranza')

    fecha_cobro = models.DateField(blank=True, null=True)
    valor_fca = models.DecimalField(max_digits=12, decimal_places=2)
    valor_flete = models.DecimalField(max_digits=12, decimal_places=2)
    monto_asegurado = models.DecimalField(max_digits=12, decimal_places=2)
    
    valor_prima_estimado = models.DecimalField(max_digits=12, decimal_places=2)
    valor_prima_cobro = models.DecimalField(max_digits=12, decimal_places=2)  # Lo que realmente se cobra
    valor_prima_pago = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)

    estado = models.CharField(max_length=20, choices=[
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('vencido', 'Vencido'),
    ], default='pendiente')

    def calcular_monto_asegurado(self):
        return (self.valor_fca + self.valor_flete) * Decimal('1.10')

    def calcular_prima(self):
        tasa = self.certificado.cliente.tasa
        minimo = self.certificado.cliente.valor_minimo
        prima = self.monto_asegurado * tasa
        return max(prima, minimo)

    def save(self, *args, **kwargs):
        if not self.monto_asegurado:
            self.monto_asegurado = self.calcular_monto_asegurado()
        if not self.valor_prima_estimado:
            self.valor_prima_estimado = self.calcular_prima()
        if not self.valor_prima_cobro:
            self.valor_prima_cobro = self.valor_prima_estimado
        super().save(*args, **kwargs)
        
        
class LogActividad(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    mensaje = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.username} - {self.mensaje} - {self.fecha}"
