# Generated manually to add fecha_emision field

from django.db import migrations, models
from datetime import date


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0030_fix_fecha_creacion_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='certificadotransporte',
            name='fecha_emision',
            field=models.DateField(default=date.today, verbose_name='Fecha de emisión'),
        ),
    ]
