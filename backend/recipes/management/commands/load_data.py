import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from recipes.models import Ingredient, Tag

DATA_ROOT = os.path.join(settings.BASE_DIR, 'data')

MODELS = {
    'ingredients.json': Ingredient,
    'tags.json': Tag
}


class Command(BaseCommand):
    help = 'Load data from a JSON file.'
    model = None

    def add_arguments(self, parser):
        parser.add_argument('file_name', type=str, help='Имя JSON файла')

    def handle(self, *args, **options):
        self.model = MODELS[options['file_name']]
        try:
            with open(
                os.path.join(DATA_ROOT, options['file_name']),
                'r',
                encoding='utf-8'
            ) as file:
                objects = self.model.objects.bulk_create(
                    (self.model(**item) for item in json.load(file)),
                    ignore_conflicts=True
                )
            total_objects = len(objects)
            self.stdout.write(self.style.SUCCESS(
                f'{total_objects} '
                f'{self.model._meta.verbose_name_plural} '
                f'успешно импортировано из {options['file_name']}'
            ))
        except FileNotFoundError:
            raise CommandError(
                'Указанный файл должен находиться в директории {DATA_ROOT}.'
            )
        except Exception as error:
            raise CommandError(
                f'Ошибка импорта {options['file_name']}: {error}'
            )
