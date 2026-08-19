import json
from django.core.management.base import BaseCommand
from organization.models import Region, City, GcCode
from .city_to_region_map import city_region_map

class Command(BaseCommand):
    help = "Import GC codes from JSON file"

    def handle(self, *args, **options):
        # Load JSON data
        with open("city_to_gc_code.json", "r") as f:
            city_gc_map = json.load(f)

        # Get or create regions
        regions = {}
        for region_name in set(city_region_map.values()):
            region, created = Region.objects.get_or_create(
                name=region_name
            )
            regions[region_name] = region
            if created:
                self.stdout.write(f'Created region: {region_name}')

        # Import cities and GC codes
        city_count = 0
        gc_count = 0
        skipped_cities = []

        for city_name, gc_codes in city_gc_map.items():
            region_name = city_region_map.get(city_name)
            if not region_name:
                skipped_cities.append(city_name)
                continue

            # Get or create city
            city, created = City.objects.get_or_create(
                name=city_name, 
                region=regions[region_name]
            )
            if created:
                city_count += 1

            # Create GC codes
            for gc_code in gc_codes:
                gc, created = GcCode.objects.get_or_create(
                    code=gc_code,
                    defaults={
                        "city": city,
                        "name": f"GC Code {gc_code}"  # Optional: set a default name
                    }
                )
                if created:
                    gc_count += 1

            self.stdout.write(
                self.style.SUCCESS(f"Imported {len(gc_codes)} GC codes for {city_name}")
            )

        self.stdout.write(self.style.SUCCESS(f'\nImport completed!'))
        self.stdout.write(f'Cities created: {city_count}')
        self.stdout.write(f'GC codes created: {gc_count}')
        
        if skipped_cities:
            self.stdout.write(self.style.WARNING(f'\nSkipped cities (no region mapped):'))
            for city in skipped_cities[:20]:
                self.stdout.write(f'  - {city}')
            if len(skipped_cities) > 20:
                self.stdout.write(f'  ... and {len(skipped_cities) - 20} more')