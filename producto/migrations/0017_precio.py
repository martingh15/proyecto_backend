# Generated by Django 3.2.4 on 2021-10-06 22:38

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('producto', '0016_producto_stock'),
    ]

    operations = [
        migrations.CreateModel(
            name='Precio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='precios',
                                               to='producto.producto')),
                ('fecha', models.DateTimeField(default=datetime.datetime.now)),
                ('precio', models.FloatField()),
                ('auditoria_creado_fecha', models.DateTimeField(blank=True, default=datetime.datetime.now)),
                ('auditoria_modificado_fecha', models.DateTimeField(blank=True, default=datetime.datetime.now)),
                ('auditoria_creador', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('auditoria_modificado', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]