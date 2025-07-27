import os
import csv
from django.conf import settings
from django.core.management.base import BaseCommand
from core.models import Navio

class Command(BaseCommand):
    help = 'Puebla la base de datos con la lista de navíos desde el archivo local core/data/navios_data.csv.'

    def handle(self, *args, **options):
        """
        Manejador principal del comando. Lee el archivo CSV local y carga los datos
        en el modelo Navio de la base de datos.
        """
        self.stdout.write(self.style.WARNING(
            "🚢 Iniciando la carga de navíos desde el archivo local..."
        ))

        # --- RUTA AL ARCHIVO CSV LOCAL ---
        # Construimos la ruta de forma dinámica para que funcione en cualquier sistema.
        file_path = os.path.join(settings.BASE_DIR, 'core', 'data', 'navios_data.csv')

        # Verificamos si el archivo existe antes de intentar abrirlo
        if not os.path.exists(file_path):
            self.stderr.write(self.style.ERROR(f"Error: No se encontró el archivo en la ruta: {file_path}"))
            return

        agregados = 0
        actualizados = 0
        errores = 0

        try:
            # Usamos un manejador de contexto para asegurar que el archivo se cierre correctamente
            with open(file_path, mode='r', encoding='utf-8') as csv_file:
                reader = csv.DictReader(csv_file)
                
                # Convertimos el reader a una lista para poder contar las filas y iterar
                data_list = list(reader)
                total_rows = len(data_list)
                
                self.stdout.write(f"Se encontraron {total_rows} registros en el archivo. Iniciando procesamiento...")

                for i, row in enumerate(data_list):
                    if (i + 1) % 100 == 0:
                        self.stdout.write(f"Procesando... {i + 1} de {total_rows} registros.")
                    
                    # --- Mapeo de columnas del CSV a los campos del modelo ---
                    # Obtenemos los valores de las columnas de nuestro archivo.
                    imo = row.get('IMO')
                    nombre_navio = row.get('SHIPNAME')

                    # Es crucial saltar filas que no tengan un IMO, que es nuestro identificador único.
                    if not imo or imo == '0' or not nombre_navio:
                        errores += 1
                        continue

                    try:
                        # Usamos update_or_create para evitar duplicados y actualizar data existente.
                        obj, created = Navio.objects.update_or_create(
                            imo=imo,
                            defaults={
                                'nombre': nombre_navio.strip(),
                                'mmsi': row.get('MMSI'),
                                'tipo': row.get('TYPE_MAIN'),
                                'bandera': row.get('FLAG'),
                                'naviera': row.get('OWNER')
                            }
                        )
                        if created:
                            agregados += 1
                        else:
                            actualizados += 1
                    except Exception as e:
                        # Capturamos errores específicos de una fila (ej. datos corruptos)
                        self.stderr.write(self.style.ERROR(f"Error en la fila {i+2}: {row} - {e}"))
                        errores += 1
                        continue
                        
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"Error: El archivo no fue encontrado en {file_path}"))
            return
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Ocurrió un error inesperado: {e}"))
            return

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Proceso finalizado. Registros agregados: {agregados}, actualizados: {actualizados}, con errores/saltados: {errores}."
        ))
