# Generated by Django 4.2 on 2023-04-21 18:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('receipt', '0012_rename_tiempo_receipt_cooking_time'),
    ]

    operations = [
        migrations.RenameField(
            model_name='ingredient',
            old_name='izmerenie',
            new_name='measurement_unit',
        ),
        migrations.RenameField(
            model_name='quantity_ingredientes',
            old_name='quantity',
            new_name='amount',
        ),
        migrations.RenameField(
            model_name='receipt',
            old_name='ingridientes',
            new_name='ingredients',
        ),
        migrations.RenameField(
            model_name='receipt',
            old_name='title',
            new_name='name',
        ),
    ]
