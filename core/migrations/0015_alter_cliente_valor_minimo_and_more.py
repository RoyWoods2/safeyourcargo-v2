# Generated by Django 5.2.1 on 2025-07-01 20:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_alter_cliente_valor_minimo_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cliente',
            name='valor_minimo',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
        migrations.AlterField(
            model_name='cliente',
            name='valor_minimo_congelado',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
    ]
