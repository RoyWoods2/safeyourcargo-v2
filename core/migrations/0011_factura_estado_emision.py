# Generated by Django 5.2.1 on 2025-06-11 07:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_alter_certificadotransporte_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='factura',
            name='estado_emision',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
