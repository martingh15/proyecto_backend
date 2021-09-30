from .models import Pedido, Estado
from .serializers import PedidoSerializer
from base.permisos import TieneRolComensal
from base.respuestas import Respuesta
from django.core.exceptions import ValidationError
from django.db import transaction
from gastronomia.repositorio import get_pedido, validar_crear_pedido, crear_pedido, actualizar_pedido, cerrar_pedido
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from base import utils

respuesta = Respuesta()


# Abm de pedidos con autorización
class PedidoViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.all()
    serializer_class = PedidoSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, TieneRolComensal]

    def get_cantidad_registros(self, request):
        desdeTexto = request.query_params.get('fechaDesde', "")
        hastaTexto = request.query_params.get('fechaHasta', "")
        desde = utils.get_fecha_string2objeto(desdeTexto)
        hasta = utils.get_fecha_string2objeto(hastaTexto, False)
        idUsuario = request.query_params.get('usuario', None)
        numero = request.query_params.get('numero', "")

        filtros = {
            "fecha__range": (desde, hasta),
        }
        if idUsuario is not None and idUsuario.isnumeric() and int(idUsuario) > 0:
            filtros["usuario"] = idUsuario
        if numero is not None and numero.isnumeric() and int(numero) > 0:
            filtros = {
                "id": numero
            }
        cantidad = Pedido.objects.filter(**filtros).count()
        return cantidad

    def filtrar_pedidos(self, request):
        desdeTexto = request.query_params.get('fechaDesde', "")
        hastaTexto = request.query_params.get('fechaHasta', "")
        desde = utils.get_fecha_string2objeto(desdeTexto)
        hasta = utils.get_fecha_string2objeto(hastaTexto, False)
        idUsuario = request.query_params.get('usuario', None)
        numero = request.query_params.get('numero', "")

        pagina = int(request.query_params.get('paginaActual', 1))
        registros = int(request.query_params.get('registrosPorPagina', 10))
        offset = (pagina - 1) * registros
        limit = offset + registros
        filtros = {
            "fecha__range": (desde, hasta),
        }
        if idUsuario is not None and idUsuario.isnumeric() and int(idUsuario) > 0:
            filtros["usuario"] = idUsuario

        numero_valido = numero is not None and numero.isnumeric() and int(numero) > 0
        if numero_valido:
            filtros = {
                "id": numero
            }
        pedidos = Pedido.objects.filter(**filtros)
        if numero_valido:
            return pedidos

        pedidos = Pedido.objects.filter(**filtros).order_by('-fecha')[offset:limit]
        return pedidos

    def list(self, request, *args, **kwargs):
        pedidos = self.filtrar_pedidos(request)
        if len(pedidos) > 0:
            serializer = PedidoSerializer(instance=pedidos, many=True)
            pedidos = serializer.data

        idUsuario = request.query_params.get("usuario")
        cantidad = self.get_cantidad_registros(request)
        total = Pedido.objects.filter(usuario=idUsuario).count()
        datos = {
            "pedidos": pedidos,
            "total": total,
            "registros": cantidad
        }
        return respuesta.get_respuesta(datos=datos, formatear=False)

    @action(detail=False, methods=['get'])
    def listado_vendedor(self, request, pk=None):
        logueado = request.user
        pedidos = []
        if logueado.esVendedor:
            pedidos = self.filtrar_pedidos(request)
        else:
            return respuesta.get_respuesta(False, "No está autorizado para listar los pedidos vendidos.", 401)
        if len(pedidos) > 0:
            serializer = PedidoSerializer(instance=pedidos, many=True)
            pedidos = serializer.data
        cantidad = self.get_cantidad_registros(request)
        total = Pedido.objects.count()
        datos = {
            "pedidos": pedidos,
            "total": total,
            "registros": cantidad
        }
        return respuesta.get_respuesta(datos=datos, formatear=False)

    def retrieve(self, request, *args, **kwargs):
        clave = kwargs.get('pk')
        pedido = None
        usuario = request.user
        serializer = None
        estado_valido = Estado.comprobar_estado_valido(clave)
        if estado_valido:
            pedido = get_pedido(pk=None, usuario=usuario, estado=clave)
            serializer = PedidoSerializer(instance=pedido)
        elif clave.isnumeric():
            pedido = get_pedido(pk=clave)
            serializer = PedidoSerializer(instance=pedido)
            return respuesta.get_respuesta(exito=True, datos=serializer.data)
        cerrado = None
        if pedido is None:
            cerrado = get_pedido(pk=None, usuario=usuario, estado=Estado.CERRADO)
        noHayAbierto = pedido is None
        hayCerrado = cerrado is not None
        if noHayAbierto and not hayCerrado:
            return respuesta.get_respuesta(False, "")
        if noHayAbierto and hayCerrado:
            return respuesta.get_respuesta(exito=True, datos={"cerrado": True})
        return respuesta.get_respuesta(True, "", None, serializer.data)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        usuario = request.user
        try:
            tipo = Pedido.TIPO_ONLINE
            datos = request.data
            validar_crear_pedido(datos)
            id = datos["id"]
            lineas = datos["lineas"]
            if id <= 0:
                pedido = crear_pedido(usuario, lineas, tipo)
            else:
                pedido = actualizar_pedido(id, lineas)
            datos = {"pedido": "borrado"}
            if pedido is not None:
                serializer = PedidoSerializer(instance=pedido)
                datos = serializer.data
            return respuesta.get_respuesta(True, "", None, datos)
        except ValidationError as e:
            return respuesta.get_respuesta(False, e.messages)

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return respuesta.get_respuesta(True, "Pedido cancelado con éxito.")

    def update(self, request, *args, **kwargs):
        pedido = get_pedido(pk=kwargs["pk"])
        if pedido is None:
            return respuesta.get_respuesta(True, "No se ha encontrado el pedido.")
        cerrar_pedido(pedido)
        return respuesta.get_respuesta(True, "Pedido realizado con éxito, podrá retirarlo por el local en "
                                             "aproximadamente 45 minutos.")

    @action(detail=True, methods=['post'])
    def entregar(self, request, pk=None):
        try:
            pedido = get_pedido(pk)
            if pedido is None:
                return respuesta.get_respuesta(exito=False, mensaje="No se ha encontrado el pedido a marcar como "
                                                                    "recibido.")
            abierto = pedido.comprobar_estado_abierto()
            if abierto:
                return respuesta.get_respuesta(exito=False, mensaje="No se puede marcar como entregado el pedido "
                                                                    "debido a que el usuario no lo ha cerrado.")
            recibido = pedido.comprobar_estado_recibido()
            if recibido:
                return respuesta.get_respuesta(exito=False, mensaje="El pedido ya se encuentra en estado entregado.")
            cerrado = pedido.comprobar_estado_cerrado()
            if cerrado:
                pedido.entregar_pedido()
            else:
                raise ValidationError("")
            return respuesta.get_respuesta(exito=True, mensaje="El pedido se ha entregado con éxito.")
        except:
            return respuesta.get_respuesta(exito=False, mensaje="Ha ocurrido un error al entregar el pedido.")

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        try:
            pedido = get_pedido(pk)
            if pedido is None:
                return respuesta.get_respuesta(exito=False, mensaje="No se ha encontrado el pedido a cancelar.")
            usuario = request.user
            puede_cancelar = pedido.comprobar_puede_cancelar(usuario)
            if not puede_cancelar:
                return respuesta.get_respuesta(exito=False, mensaje="No está habilitado para cancelar el pedido.")
            pedido.agregar_estado(Estado.CANCELADO)
            pedido.save()
            return respuesta.get_respuesta(exito=True, mensaje="El pedido se ha cancelado con éxito.")
        except:
            return respuesta.get_respuesta(exito=False, mensaje="Ha ocurrido un error al cancelar el pedido.")
