# En core/management/commands/poblar_aerolineas.py

import requests
from django.core.management.base import BaseCommand
from core.models import Aerolinea  # Asegúrate de importar tu modelo

# Usaremos una fuente pública y confiable para la lista de aerolíneas
# Esta URL contiene una lista extensa y bien formateada
DATA_URL = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airlines.dat"

class Command(BaseCommand):
    help = 'Puebla la base de datos con una lista de aerolíneas desde OpenFlights.'

    def handle(self, *args, **options):
        self.stdout.write("✈️  Iniciando la descarga de aerolíneas...")

        try:
            response = requests.get(DATA_URL)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            self.stderr.write(self.style.ERROR(f"Error al descargar los datos: {e}"))
            return

        lineas_agregadas = 0
        lineas_actualizadas = 0

        # El archivo .dat es un CSV sin encabezados
        for line in response.text.splitlines():
            parts = line.split(',')

            # Formato de la data: Airline ID,Name,Alias,IATA,ICAO,Callsign,Country,Active
            if len(parts) < 8:
                continue

            nombre = parts[1].strip('"')
            iata = parts[3].strip('"')
            icao = parts[4].strip('"')
            pais = parts[6].strip('"')
            activo = parts[7].strip('"')

            # Saltamos aerolíneas inactivas o sin nombre/código
            if activo != 'Y' or not nombre or not iata:
                continue

            # Usamos update_or_create para evitar duplicados y permitir actualizaciones
            obj, created = Aerolinea.objects.update_or_create(
                codigo_iata=iata,
                defaults={
                    'nombre': nombre,
                    'codigo_icao': icao if icao != '\\N' else None,
                    'pais': pais if pais != '\\N' else None,
                }
            )

            if created:
                lineas_agregadas += 1
            else:
                lineas_actualizadas += 1

        self.stdout.write(self.style.SUCCESS(
            f"✅ Proceso completado. Agregadas: {lineas_agregadas}, Actualizadas: {lineas_actualizadas}."
        ))