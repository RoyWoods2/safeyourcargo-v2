from django import forms
from .models import Cliente,CertificadoTransporte, Ruta, MetodoEmbarque, TipoMercancia, Viaje, NotasNumeros
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.forms.widgets import Select  # <--- este import es clave
Usuario = get_user_model()
class ClienteSelectWidget(Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)
        try:
            option["attrs"]["data-tasa"] = f"{label.tasa:.4f}"
            option["attrs"]["data-tasa-congelada"] = f"{label.tasa_congelada:.4f}"
            option["attrs"]["data-minimo"] = f"{int(label.valor_minimo)}"
            option["attrs"]["data-minimo-congelado"] = f"{int(label.valor_minimo_congelado)}"
        except AttributeError:
            pass  # Si el label no es un objeto cliente, lo ignora (por ejemplo, opción vacía)
        return option
class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            'tipo_cliente', 'nombre', 'rut','direccion',
            'pais', 'ciudad', 'region',
            'tasa', 'valor_minimo', 'tasa_congelada', 'valor_minimo_congelado',
            'tramo_cobro'
        ]

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre']
        cliente_id = self.instance.pk  # importante para edición
        if Cliente.objects.exclude(pk=cliente_id).filter(nombre__iexact=nombre).exists():
            raise forms.ValidationError("Ya existe un cliente con este nombre.")
        return nombre

    def clean_valor_minimo(self):
        valor = self.cleaned_data.get('valor_minimo', '')
        return int(str(valor).replace('.', '').replace(',', ''))

    def clean_valor_minimo_congelado(self):
        valor = self.cleaned_data.get('valor_minimo_congelado', '')
        return int(str(valor).replace('.', '').replace(',', ''))




class UsuarioForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=True)

    class Meta:
        model = Usuario
        fields = ['username', 'password', 'rol', 'cliente', 'correo', 'telefono']

    def clean_username(self):
        username = self.cleaned_data['username']
        if self.instance.pk is None:
            if Usuario.objects.filter(username=username).exists():
                raise forms.ValidationError("Este nombre de usuario ya está en uso.")
        else:
            if Usuario.objects.exclude(pk=self.instance.pk).filter(username=username).exists():
                raise forms.ValidationError("Ya existe otro usuario con este nombre.")
        return username


    def clean_username(self):
        username = self.cleaned_data['username']
        if self.instance.pk is None:
            if Usuario.objects.filter(username=username).exists():
                raise forms.ValidationError("Este nombre de usuario ya está en uso.")
        else:
            if Usuario.objects.exclude(pk=self.instance.pk).filter(username=username).exists():
                raise forms.ValidationError("Ya existe otro usuario con este nombre.")
        return username


class CertificadoTransporteForm(forms.ModelForm):
    # Añade este campo al formulario, igual que en la sugerencia anterior
    otros_emails_copia = forms.CharField(
        label='Enviar copia a otros emails (separados por coma)',
        required=False, # Este campo es opcional
        help_text='Ej: email1@ejemplo.com, email2@ejemplo.com',
        widget=forms.TextInput(attrs={'placeholder': 'email1@dominio.com, email2@dominio.com'})
    )

    class Meta:
        model = CertificadoTransporte
        # ¡IMPORTANTE! Añade 'otros_emails_copia' a la lista de fields
        fields = ['cliente', 'fecha_partida', 'fecha_llegada', 'otros_emails_copia']
        widgets = {
            'cliente': ClienteSelectWidget(attrs={'class': 'form-select', 'id': 'id_cliente'}),
            'fecha_partida': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_llegada': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Filtra si no es superuser
        if user and not user.is_superuser:
            self.fields['cliente'].queryset = Cliente.objects.filter(creado_por=user)

        # 👇 Esta línea es clave para mantener el objeto como label y acceder a tasas
        self.fields['cliente'].label_from_instance = lambda obj: obj







        
class RutaForm(forms.ModelForm):
    class Meta:
        model = Ruta
        fields = '__all__'
        widgets = {
            'pais_origen': forms.TextInput(attrs={'class': 'form-control'}),
            'ciudad_origen': forms.TextInput(attrs={'class': 'form-control'}),
            'pais_destino': forms.TextInput(attrs={'class': 'form-control'}),
            'ciudad_destino': forms.TextInput(attrs={'class': 'form-control'}),
        }
class MetodoEmbarqueForm(forms.ModelForm):
    class Meta:
        model = MetodoEmbarque
        fields = '__all__'
        widgets = {
            'modo_transporte': forms.Select(attrs={'class': 'form-select', 'id': 'modoTransporte'}),
            'tipo_carga': forms.Select(attrs={'class': 'form-select'}),
            'clausula': forms.Select(attrs={'class': 'form-select'}),

            # AÉREO
            'tipo_embalaje_aereo': forms.Select(attrs={'class': 'form-select'}),
            'otro_embalaje_aereo': forms.TextInput(attrs={'class': 'form-control'}),

            # MARÍTIMO
            'embalaje_maritimo': forms.Select(attrs={'class': 'form-select'}),
            'tipo_container_maritimo': forms.Select(attrs={'class': 'form-select'}),
            'tipo_embalaje_lcl': forms.Select(attrs={'class': 'form-select'}),
            'otro_embalaje_lcl': forms.TextInput(attrs={'class': 'form-control'}),

            # TERRESTRE
            'tipo_embalaje_terrestre': forms.Select(attrs={'class': 'form-select'}),
            'otro_embalaje_terrestre': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        modo = cleaned_data.get("modo_transporte")

        # AÉREO
        if modo == "Aereo":
            tipo = cleaned_data.get("tipo_embalaje_aereo")
            otro = cleaned_data.get("otro_embalaje_aereo")
            if not tipo:
                self.add_error("tipo_embalaje_aereo", "Debe seleccionar el tipo de embalaje para aéreo.")
            if tipo == "OTRO" and not otro:
                self.add_error("otro_embalaje_aereo", "Debe especificar el embalaje aéreo.")

        # MARÍTIMO
        elif modo == "Maritimo":
            embalaje_maritimo = cleaned_data.get("embalaje_maritimo")
            if not embalaje_maritimo:
                self.add_error("embalaje_maritimo", "Debe seleccionar FCL o LCL para marítimo.")
            if embalaje_maritimo == "FCL":
                tipo = cleaned_data.get("tipo_container_maritimo")
                if not tipo:
                    self.add_error("tipo_container_maritimo", "Debe seleccionar tipo de contenedor.")
            elif embalaje_maritimo == "LCL":
                tipo = cleaned_data.get("tipo_embalaje_lcl")
                otro = cleaned_data.get("otro_embalaje_lcl")
                if not tipo:
                    self.add_error("tipo_embalaje_lcl", "Debe seleccionar el tipo de embalaje.")
                if tipo == "OTRO" and not otro:
                    self.add_error("otro_embalaje_lcl", "Debe especificar el embalaje.")

        # TERRESTRE
        elif modo == "TerrestreFerroviario":
            tipo = cleaned_data.get("tipo_embalaje_terrestre")
            otro = cleaned_data.get("otro_embalaje_terrestre")
            if not tipo:
                self.add_error("tipo_embalaje_terrestre", "Debe seleccionar el tipo de embalaje.")
            if tipo == "OTRO" and not otro:
                self.add_error("otro_embalaje_terrestre", "Debe especificar el embalaje.")



class TipoMercanciaForm(forms.ModelForm):
    class Meta:
        model = TipoMercancia
        fields = '__all__'
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'valor_fca': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'inputmode': 'decimal'}),
            'valor_flete': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'inputmode': 'decimal'}),
            'valor_prima': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'inputmode': 'decimal'}),
        }
class ViajeForm(forms.ModelForm):
    aeropuerto_origen = forms.CharField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_aeropuerto_origen'})
    )
    aeropuerto_destino = forms.CharField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_aeropuerto_destino'})
    )

    class Meta:
        model = Viaje
        fields = '__all__'
        widgets = {
            'nombre_avion': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_viaje': forms.TextInput(attrs={'class': 'form-control'}),
            'vuelo_origen_pais': forms.TextInput(attrs={'class': 'form-control'}),
            'vuelo_origen_ciudad': forms.TextInput(attrs={'class': 'form-control'}),
            'vuelo_destino_pais': forms.TextInput(attrs={'class': 'form-control'}),
            'vuelo_destino_ciudad': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion_carga': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Si hay datos POST, asignar las opciones directamente
        if self.data.get("aeropuerto_origen"):
            self.fields['aeropuerto_origen'].widget.choices = [
                (self.data.get("aeropuerto_origen"), self.data.get("aeropuerto_origen"))
            ]

        if self.data.get("aeropuerto_destino"):
            self.fields['aeropuerto_destino'].widget.choices = [
                (self.data.get("aeropuerto_destino"), self.data.get("aeropuerto_destino"))
            ]

class NotasNumerosForm(forms.ModelForm):
    class Meta:
        model = NotasNumeros
        fields = '__all__'
        widgets = {
            'referencia': forms.TextInput(attrs={'class': 'form-control'}),
            'guia_carga': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_factura': forms.TextInput(attrs={'class': 'form-control'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['referencia'].required = False
        self.fields['numero_factura'].required = False
        self.fields['notas'].required = False


class NsureTestForm(forms.Form):
    # Nuevo campo para el ID de la declaración
    declaration_id = forms.CharField(
        max_length=255, 
        required=False, 
        label="ID de Declaración (para Navíos/Países)",
        help_text="Necesitas crear una declaración primero para obtener este ID. Puede ser un ID numérico o 'external-id=TU_ID_EXTERNO'."
    )

    ENDPOINT_CHOICES = [
        ('create_declaration', '1. Crear Declaración de Prueba'), # Nueva opción
        ('vessels', '2. Buscador de Navíos (5.4)'),
        ('countries', '3. Listado de Países (5.6)'),
    ]
    endpoint = forms.ChoiceField(choices=ENDPOINT_CHOICES, label="Selecciona el Endpoint")
    search_term = forms.CharField(max_length=255, required=False, label="Término de Búsqueda (para Navíos)")
