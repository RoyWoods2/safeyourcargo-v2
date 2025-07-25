# Generated by Django 5.2.1 on 2025-06-11 00:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_factura_folio_sii'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cliente',
            name='correo',
        ),
        migrations.RemoveField(
            model_name='cliente',
            name='telefono',
        ),
        migrations.AddField(
            model_name='usuario',
            name='correo',
            field=models.EmailField(default='', max_length=254),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='usuario',
            name='telefono',
            field=models.CharField(default='', max_length=20),
            preserve_default=False,
        ),
    ]
