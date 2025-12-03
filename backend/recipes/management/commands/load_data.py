import csv
import os
from collections import Counter

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction

from recipes.models import Ingredient, Tag

CSV_DIR = os.path.join(settings.BASE_DIR, 'data')

MODEL_CSV = {
    Ingredient: 'ingredients.csv',
    Tag: 'tags.csv',
}

FK_FIELDS = {
    # 'author': User,
}


def _convert_fk(row: dict) -> dict:
    """Replace raw FK id → model instance."""
    for key, model in FK_FIELDS.items():
        if key in row:
            row[key] = model.objects.get(pk=row[key])
    return row


class Command(BaseCommand):
    help = 'Import initial data from CSV files located in /data/'

    def add_arguments(self, parser):
        parser.add_argument(
            '--wipe',
            action='store_true',
            help='Delete existing data before import',
        )

    def handle(self, *args, **options):
        wipe = options['wipe']
        stats = Counter(created=0, skipped=0, errors=0)
        self.stdout.write(self.style.SUCCESS('🚀  Start CSV import'))

        for model, file_name in MODEL_CSV.items():
            path = os.path.join(CSV_DIR, file_name)
            if not os.path.exists(path):
                self.stdout.write(
                    self.style.WARNING(f'⏭  {file_name} not found – skipped')
                )
                continue

            if wipe:
                with transaction.atomic():
                    model.objects.all().delete()
                self.stdout.write(
                    self.style.WARNING(f'🗑  {model.__name__} table wiped')
                )

            self.stdout.write(f'📄  Loading {file_name} …')
            with open(path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row_num, row in enumerate(reader, start=1):
                    try:
                        with transaction.atomic():
                            row = _convert_fk(row)
                            _, created = model.objects.get_or_create(
                                id=row_num,
                                defaults=row,
                            )
                            stats['created' if created else 'skipped'] += 1
                    except (model.DoesNotExist, IntegrityError) as exc:
                        stats['errors'] += 1
                        self.stdout.write(
                            self.style.ERROR(
                                f'❌  Row {row_num} in {file_name}: {exc}'
                            )
                        )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅  Finished: created={stats["created"]}, '
                f'skipped={stats["skipped"]}, errors={stats["errors"]}'
            )
        )
