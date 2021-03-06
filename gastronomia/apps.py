from django.apps import AppConfig
from django.db.models.signals import pre_save
from base.signals import agregar_auditorias


class GastronomiaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gastronomia'

    pre_save.connect(agregar_auditorias, sender='gastronomia.Pedido'),
    pre_save.connect(agregar_auditorias, sender='gastronomia.Venta'),
