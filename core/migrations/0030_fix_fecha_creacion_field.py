# Generated manually to fix fecha_creacion field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0029_alter_viaje_aeropuerto_destino_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='certificadotransporte',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación'),
        ),
    ]

