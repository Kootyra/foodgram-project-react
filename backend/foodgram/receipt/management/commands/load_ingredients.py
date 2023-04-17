import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from receipt.models import Ingredient

DATA_ROOT = os.path.join(settings.BASE_DIR, 'data')


class Command(BaseCommand):
    """
    Переносим данные из csv в базу данных
    """
    help = 'Добавляем ингредиенты из файла ingredients.csv'

    def add_arguments(self, parser):
        parser.add_argument('filename', default='ingredients.csv', nargs='?',
                            type=str)

    def handle(self, *args, **options):
        try:
            with open(os.path.join(DATA_ROOT, options['filename']), 'r',
                      encoding='utf-8') as f:
                data = csv.reader(f)
                for row in data:
                    name, izmerenie = row
                    Ingredient.objects.get_or_create(
                        name=name,
                        izmerenie=izmerenie
                    )
        except FileNotFoundError:
            raise CommandError('Не обнаружен ingredients.csv')
