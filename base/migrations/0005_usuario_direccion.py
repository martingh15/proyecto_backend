# Generated by Django 3.2.4 on 2021-12-01 17:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0004_alter_usuario_observaciones'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='direccion',
            field=models.CharField(blank=True, default='', max_length=30),
        ),
    ]
