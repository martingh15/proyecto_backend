from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
import datetime


class Auditoria(models.Model):
    auditoria_creado_fecha = models.DateTimeField(default=datetime.datetime.now, blank=True)
    auditoria_modificado_fecha = models.DateTimeField(default=datetime.datetime.now, blank=True)

    auditoria_creador = models.ForeignKey('base.Usuario', on_delete=models.CASCADE, related_name="+", null=True)
    auditoria_modificado = models.ForeignKey('base.Usuario', on_delete=models.CASCADE, related_name="+", null=True)

    class Meta:
        abstract = True


class Rol(models.Model):
    nombre = models.CharField(max_length=50)
    legible = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=250)
    root = models.BooleanField(default=False)

    ROOT = 'root'
    MOZO = 'mozo'
    COMENSAL = 'comensal'
    VENEDEDOR = 'vendedor'
    ADMINISTRADOR = 'admin'

    ROLES = (ROOT, MOZO, COMENSAL, VENEDEDOR, ADMINISTRADOR)


class Usuario(Auditoria, AbstractUser):
    roles = models.ManyToManyField(to='Rol', related_name="usuarios_roles", blank=True)
    dni = models.PositiveIntegerField(
        validators=[MinValueValidator(1000000), MaxValueValidator(99999999)],
        null=True,
        unique=True
    )
    email = models.EmailField(unique=True)
    username = models.CharField(unique=False, max_length=50)
    password = models.CharField(max_length=128, null=True)
    habilitado = models.BooleanField(default=True)
    token_reset = models.TextField(null=True)
    token_email = models.TextField(null=True)
    fecha_token_reset = models.DateTimeField(null=True)
    operaciones = list()
    borrado = models.BooleanField(default=False)
    observaciones = models.CharField(max_length=255, default="", blank=True)
    direccion = models.CharField(max_length=30, default="", blank=True)

    esMozo = False
    esAdmin = False
    esComensal = False
    esVendedor = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.id is not None:
            self.esMozo = self.comprobar_tiene_rol(Rol.MOZO)
            self.esAdmin = self.comprobar_tiene_rol(Rol.ADMINISTRADOR)
            self.esComensal = self.comprobar_tiene_rol(Rol.COMENSAL)
            self.esVendedor = self.comprobar_tiene_rol(Rol.VENEDEDOR)
            self.operaciones = self.get_operaciones()

    def get_url_activacion(self):
        """
            Devuelve la url para activar la cuenta del usuario.
            @return: str
        """
        token = self.token_email
        if token is None:
            return ""
        return "http://localhost:3000/validar-email/" + str(token)

    # Agrega el rol comensa al usuario.
    def agregar_rol_comensal(self):
        comensal = get_rol(Rol.COMENSAL)
        if isinstance(comensal, Rol):
            self.agregar_rol(comensal)
        else:
            raise ValidationError({"Error": "No se ha podido crear el usuario con rol comensal."})

    # Agrega un rol al usuario, el par??metro rol puede ser el id del rol, un objeto Rol o el nombre rol.
    def agregar_rol(self, rol):
        # Defino el par??metro para buscar el rol.
        id = rol
        if isinstance(id, Rol):
            id = rol.id
        filtro = {'id': id}
        if isinstance(rol, str):
            filtro = {'nombre': rol}
        existe = self.roles.filter(**filtro).first()

        # Si no tiene el rol se lo agrego.
        objeto = rol
        if isinstance(objeto, str):
            objeto = Rol.objects.get(nombre=rol)
        if not existe and isinstance(objeto, Rol):
            self.roles.add(objeto)

    # Si tiene el rol a quitar, se lo remueve de la colecci??n de roles.
    def quitar_rol(self, rol):
        existe = self.roles.filter(nombre=rol).first()
        if existe:
            self.roles.remove(existe)

    # Seg??n los cambios en los campos esMozo, esComensal y esVendedor se actualiza los roles del usuario.
    def actualizar_roles(self, usuario):
        self.actualizar_rol(usuario, Rol.MOZO)
        self.actualizar_rol(usuario, Rol.COMENSAL)
        self.actualizar_rol(usuario, Rol.VENEDEDOR)

    # Quita o agrega el rol al usuario dependiendo de los campos es'NombreRol'.
    def actualizar_rol(self, usuario, rol):
        buscar = "es" + rol.capitalize()
        agregarRol = usuario.get(buscar)
        tieneRol = self.comprobar_tiene_rol(rol)

        # Si es'NombreRol' es verdadero y no ten??a el rol anteriormente le agregamos el rol.
        if agregarRol and tieneRol is False:
            self.agregar_rol(rol)
        # Si es'NombreRol' es falso y ten??a el rol anteriormente le quitamos el rol.
        elif agregarRol is False and tieneRol:
            self.quitar_rol(rol)

    # Comprueba si el usuario tiene el rol a partir del nombre del mismo.
    def comprobar_tiene_rol(self, nombre):
        existe = self.roles.filter(nombre=nombre).first()
        return isinstance(existe, Rol)

    # Devuelve true si el usuario no ha creado entidades en el sistema.
    def comprobar_puede_borrarse(self):
        return self.ingresos.all().count() == 0 and self.pedidos.all().count() == 0 and self.pedidos.all().count() == 0 \
               and self.turnos.all().count() == 0 and self.reemplazos.all().count() == 0 \
               and self.productos_creados.all().count() == 0 and self.productos_modificados.all().count() == 0 \
               and self.categorias_creadas.all().count() == 0 and self.categorias_modificadas.all().count() == 0

    # Devuelve las operaciones del usuario seg??n los roles del mismo.
    def get_operaciones(self):
        operaciones_admin = self.get_operaciones_admin()
        operaciones_vendedor = self.get_operaciones_vendedor()
        generales = [{
            "id": 1,
            "titular": Rol.VENEDEDOR,
            "roles": [Rol.ADMINISTRADOR, Rol.VENEDEDOR],
            "ruta": "/usuarios/listar",
            "titulo": "Usuarios",
            "descripcion": "Permite gestionar los usuarios"
        },
        {
            "id": 2,
            "titular": Rol.MOZO,
            "roles": [Rol.ADMINISTRADOR, Rol.MOZO],
            "ruta": "/mesas/listar",
            "titulo": "Mesas",
            "descripcion": "Permite gestionar las mesas"
        }]
        return operaciones_admin + operaciones_vendedor + generales

    # Devuele las operaciones para el rol administrador si tiene el rol indicado.
    def get_operaciones_admin(self):
        # Si no lo tiene devolvemos una lista vac??a.
        if self.esAdmin is not True:
            return list()

        operaciones = [{
            "id": 3,
            "titular": Rol.ADMINISTRADOR,
            "roles": [Rol.ADMINISTRADOR],
            "ruta": "/productos/listar/admin",
            "titulo": "Productos",
            "descripcion": "Permite gestionar los productos"
        }, {
            "id": 4,
            "titular": Rol.ADMINISTRADOR,
            "roles": [Rol.ADMINISTRADOR],
            "ruta": "/ingreso-mercaderia/",
            "titulo": "Ingreso",
            "descripcion": "Permite ingresar mercader??a"
        }, {
            "id": 5,
            "titular": Rol.ADMINISTRADOR,
            "roles": [Rol.ADMINISTRADOR],
            "ruta": "/reemplazo-mercaderia/",
            "titulo": "Reemplazo de mercader??a",
            "descripcion": "Permite reemplazar la mercader??a existente"
        }]
        return operaciones

    # Devuele las operaciones para el rol vendedor si tiene el rol indicado.
    def get_operaciones_vendedor(self):
        # Si no lo tiene devolvemos una lista vac??a.
        if self.esVendedor is not True and self.esAdmin is not True:
            return list()

        operaciones = [{
            "id": 6,
            "titular": Rol.VENEDEDOR,
            "roles": [Rol.VENEDEDOR, Rol.ADMINISTRADOR],
            "ruta": "/pedidos/vendedor",
            "titulo": "Pedidos",
            "descripcion": "Permite gestionar los pedidos online"
        }, {
            "id": 7,
            "titular": Rol.VENEDEDOR,
            "roles": [Rol.VENEDEDOR, Rol.ADMINISTRADOR],
            "ruta": "/venta/listado",
            "titulo": "Venta",
            "descripcion": "Permite gestionar las ventas"
        }]
        return operaciones

    # Devuelve el id legible del usuario.
    def get_id_texto(self):
        return "U" + str(self.id).zfill(5)

    def __str__(self):
        return self.username


# Busca el rol por nombre.
def get_rol(rol):
    try:
        return Rol.objects.get(nombre=rol)
    except Rol.DoesNotExist:
        return None

