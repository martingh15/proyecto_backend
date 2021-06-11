from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth.models import AbstractUser
from django.db import models
import datetime


class Auditoria(models.Model):
    auditoria_creado_fecha = models.DateTimeField(default=datetime.datetime.now, blank=True)
    auditoria_modificado_fecha = models.DateTimeField(default=datetime.datetime.now, blank=True)

    auditoria_creador = models.ForeignKey('backend.Usuario', on_delete=models.CASCADE, related_name="+", null=True)
    auditoria_modificado = models.ForeignKey('backend.Usuario', on_delete=models.CASCADE, related_name="+", null=True)

    class Meta:
        abstract = True


class Usuario(Auditoria, AbstractUser):
    dni = models.PositiveIntegerField(
        validators=[MinValueValidator(1000000), MaxValueValidator(99999999)],
        null=True,
        unique=True
    )
    email = models.EmailField(unique=True)
    username = models.CharField(unique=False, max_length=50)
    habilitado = models.BooleanField(default=False)
    token_reset = models.TextField(null=True)
    token_email = models.TextField(null=True)
    fecha_token_reset = models.DateTimeField(null=True)

    roles = models.ManyToManyField(
        to='Rol', related_name="usuarios_roles", blank=True)

    def agregar_rol(self, rol):
        exists = self.roles.filter(id=rol.id).first()
        if not exists:
            self.roles.add(rol)

    def agregar_roles(self, roles):
        for rol in roles:
            objetoRol = get_rol(rol)
            if objetoRol is None:
                raise ValidationError({"Error": "No se ha encontrado el rol."})
            self.agregar_rol(objetoRol)


class Rol(models.Model):
    nombre = models.CharField(max_length=50)
    legible = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=250)
    root = models.BooleanField(default=False)

    ROOT = 'root'
    MOZO = 'mozo'
    COMENSAL = 'comensal'
    VENEDEDOR = 'vendedor'
    ADMINISTRADOR = 'administrador'

    ROLES = (ROOT, MOZO, COMENSAL, VENEDEDOR, ADMINISTRADOR)


def get_rol(rol):
    try:
        return Rol.objects.get(nombre=rol)
    except Rol.DoesNotExist:
        return None
