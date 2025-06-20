# Generated by Django 4.2 on 2023-04-15 15:48

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('receipt', '0008_alter_favorite_recept_alter_favorite_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='for_shop',
            name='recept',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shopping_recept', to='receipt.recept', verbose_name='В список покупок'),
        ),
        migrations.AlterField(
            model_name='for_shop',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shopping_user', to=settings.AUTH_USER_MODEL),
        ),
    ]
