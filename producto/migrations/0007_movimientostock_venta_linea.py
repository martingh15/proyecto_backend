# Generated by Django 3.2.4 on 2021-10-28 19:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gastronomia', '0003_venta_ventalinea'),
        ('producto', '0006_alta_reemplazos'),
    ]

    operations = [
        migrations.AddField(
            model_name='movimientostock',
            name='venta_linea',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='movimientos', to='gastronomia.ventalinea'),
        ),
    ]
