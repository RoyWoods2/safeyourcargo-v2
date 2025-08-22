# core/management/commands/import_unlocode.py
import csv
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from core.models import UnlocodeEntry

CANDIDATE_ENCODINGS = ("utf-8-sig", "utf-8", "cp1252", "latin-1")
BATCH = 5000  # tamaño de lote

def detect_encoding_and_delimiter(path: Path):
    sample_bytes = path.read_bytes()[:200_000]
    chosen_enc, sample_text = None, None
    for enc in CANDIDATE_ENCODINGS:
        try:
            sample_text = sample_bytes.decode(enc)
            chosen_enc = enc
            break
        except Exception:
            continue
    if chosen_enc is None:
        sample_text = sample_bytes.decode("latin-1", errors="ignore")
        chosen_enc = "latin-1"
    commas = sample_text.count(",")
    semis  = sample_text.count(";")
    delim = "," if commas >= semis else ";"
    return chosen_enc, delim

def iter_rows(files):
    """Genera filas válidas (country, location, name, function, subdiv, status, iata, coords)."""
    for path in files:
        enc, delim = detect_encoding_and_delimiter(path)
        yield ("__info__", f"Procesando {path.name} (enc={enc}, delim='{delim}')")
        with path.open(encoding=enc, newline='', errors="ignore") as f:
            reader = csv.reader(f, delimiter=delim, quotechar='"')
            # 0: Ch, 1: Country, 2: Location, 3: Name, 4: NameWoDiacritics,
            # 5: SubDiv, 6: Function, 7: Status, 8: Date, 9: IATA, 10: Coordinates, 11: Remarks
            for row in reader:
                if len(row) < 12:
                    continue
                country  = (row[1] or "").strip().upper()
                location = (row[2] or "").strip().upper()
                name     = (row[3] or row[4] or "").strip()
                subdiv   = (row[5] or "").strip() or None
                function = (row[6] or "").strip() or None
                status   = (row[7] or "").strip() or None
                iata     = (row[9] or "").strip() or None
                coords   = (row[10] or "").strip() or None
                if len(country) != 2 or len(location) != 3 or not name:
                    continue
                yield (country, location, name, function, subdiv, status, iata, coords)

class Command(BaseCommand):
    help = "Importa UN/LOCODE desde carpeta con '... UNLOCODE CodeListPart1/2/3.csv' de forma rápida (bulk) y sin duplicados."

    def add_arguments(self, parser):
        parser.add_argument("folder", type=str, help="Carpeta que contiene los CSV Part1/2/3")
        parser.add_argument("--truncate", action="store_true", help="Vaciar tabla y crear todo (más rápido)")
        parser.add_argument("--limit", type=int, default=0, help="(Debug) Limitar filas válidas totales")

    def handle(self, *args, **opts):
        folder = Path(opts["folder"])
        if not folder.exists() or not folder.is_dir():
            raise CommandError(f"La ruta no es carpeta: {folder}")

        files = sorted(folder.glob("*UNLOCODE CodeListPart*.csv"))
        if not files:
            raise CommandError("No se encontraron CSV tipo 'UNLOCODE CodeListPart*.csv'.")

        self.stdout.write("Archivos detectados:")
        for p in files:
            self.stdout.write(f"  - {p.name}")

        total_validas = 0
        creados = 0
        actualizados = 0
        duplicados_skip = 0

        with transaction.atomic():
            if opts["truncate"]:
                self.stdout.write("Vaciando tabla UnlocodeEntry…")
                UnlocodeEntry.objects.all().delete()

            # set con claves ya vistas para evitar duplicados dentro del dataset (y entre partes)
            seen_keys = set()

            # Si NO truncamos, precargamos claves existentes para no intentar crearlas
            existing = {}
            if not opts["truncate"]:
                self.stdout.write("Precargando claves existentes…")
                existing = {
                    (cc, lc): pk
                    for cc, lc, pk in UnlocodeEntry.objects.values_list("country_code", "locode", "pk")
                }
                # y marcamos como ya vistas
                seen_keys.update(existing.keys())

            to_create = []
            to_update = []

            for row in iter_rows(files):
                if isinstance(row, tuple) and len(row) == 2 and row[0] == "__info__":
                    self.stdout.write("  · " + row[1])
                    continue

                country, location, name, function, subdiv, status, iata, coords = row
                locode = f"{country}{location}"
                key = (country, locode)

                total_validas += 1
                if opts["limit"] and total_validas > opts["limit"]:
                    break

                # dedupe en memoria
                if key in seen_keys:
                    duplicados_skip += 1
                    continue
                seen_keys.add(key)

                if opts["truncate"]:
                    to_create.append(UnlocodeEntry(
                        country_code=country, locode=locode, name=name,
                        function=function, subdiv=subdiv, status=status,
                        iata=iata, coordinates=coords
                    ))
                    if len(to_create) >= BATCH:
                        # ignore_conflicts: por si igual se coló alguno
                        UnlocodeEntry.objects.bulk_create(to_create, batch_size=BATCH, ignore_conflicts=True)
                        creados += len(to_create)
                        to_create.clear()
                        self.stdout.write(f"  · creados={creados} (parcial)")
                else:
                    if key in existing:
                        inst = UnlocodeEntry(
                            id=existing[key],
                            country_code=country, locode=locode, name=name,
                            function=function, subdiv=subdiv, status=status,
                            iata=iata, coordinates=coords
                        )
                        to_update.append(inst)
                        if len(to_update) >= BATCH:
                            UnlocodeEntry.objects.bulk_update(
                                to_update,
                                ["name","function","subdiv","status","iata","coordinates"],
                                batch_size=BATCH
                            )
                            actualizados += len(to_update)
                            to_update.clear()
                            self.stdout.write(f"  · actualizados={actualizados} (parcial)")
                    else:
                        to_create.append(UnlocodeEntry(
                            country_code=country, locode=locode, name=name,
                            function=function, subdiv=subdiv, status=status,
                            iata=iata, coordinates=coords
                        ))
                        if len(to_create) >= BATCH:
                            UnlocodeEntry.objects.bulk_create(to_create, batch_size=BATCH, ignore_conflicts=True)
                            creados += len(to_create)
                            to_create.clear()
                            self.stdout.write(f"  · creados={creados} (parcial)")

            # flush final
            if to_create:
                UnlocodeEntry.objects.bulk_create(to_create, batch_size=BATCH, ignore_conflicts=True)
                creados += len(to_create)
            if to_update:
                UnlocodeEntry.objects.bulk_update(
                    to_update,
                    ["name","function","subdiv","status","iata","coordinates"],
                    batch_size=BATCH
                )
                actualizados += len(to_update)

        self.stdout.write(self.style.SUCCESS(
            f"\nOK. Filas válidas: {total_validas} | nuevos: {creados} | actualizados: {actualizados} | duplicados_omitidos: {duplicados_skip}"
        ))
