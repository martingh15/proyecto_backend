from rest_framework import serializers
from .models import Pedido, PedidoLinea, VentaLinea, Venta
from base.signals import get_usuario_logueado
from producto.serializers import ProductoSerializer, MovimientoSerializer
from base.serializers import UsuarioSerializer
import unidecode
import locale

locale.setlocale(locale.LC_ALL, '')


class VentaLineaSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer(read_only=True)
    movimientos = MovimientoSerializer(many=True, read_only=True)

    class Meta:
        model = VentaLinea
        fields = '__all__'

    # Método que devuelve los datos de la línea.
    def to_representation(self, instance):
        """Quito password"""
        ret = super().to_representation(instance)
        ret['precio_texto'] = locale.currency(instance.precio)
        ret['total_texto'] = locale.currency(instance.total)
        return ret


class VentaSerializer(serializers.ModelSerializer):
    lineas = VentaLineaSerializer(many=True, read_only=True)
    operaciones = serializers.SerializerMethodField()

    class Meta:
        model = Venta
        fields = '__all__'

    # Método que devuelve los datos de la venta.
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['id_texto'] = instance.get_id_texto()
        ret['id_texto_limpio'] = instance.get_id_texto_limpio()
        ret['tipo_venta'] = instance.get_tipo_texto()
        ret['tipo_venta_online'] = instance.get_tipo_online_texto()
        ret['usuario_email'] = instance.usuario.email
        ret['usuario_nombre'] = unidecode.unidecode(instance.usuario.first_name)
        ret['fecha_texto'] = instance.auditoria_creado_fecha.strftime('%d/%m/%Y %H:%M')
        ret['total_texto'] = locale.currency(instance.total)
        ret['estado_texto'] = instance.get_estado_legible()
        ret['estado_clase'] = instance.get_estado_clase()
        ret['fecha_anulado'] = instance.get_fecha_anulada_texto()
        ret['vuelto_texto'] = instance.get_vuelto_texto()
        ret['direccion_texto'] = instance.get_direccion_texto()
        ret['anulada'] = instance.comprobar_anulada()
        ret['nombre'] = instance.get_nombre()
        ret['clase_venta_impresa'] = instance.get_clase_venta_impresa()
        return ret

    # Devuelve las operaciones disponibles para la venta actual.
    def get_operaciones(self, objeto):
        logueado = get_usuario_logueado()
        operaciones = []

        puede_visualizar = objeto.comprobar_puede_visualizar(logueado)
        if puede_visualizar:
            accion = 'visualizar'
            operaciones.append({
                'accion': accion,
                'clase': 'btn btn-sm btn-info text-info',
                'texto': 'Ver',
                'icono': 'fa fa-eye',
                'title': 'Ver Venta ' + objeto.get_id_texto(),
                'key': str(objeto.id) + "-" + accion,
            })

        accion = 'pdf'
        operaciones.append({
            'accion': accion,
            'clase': 'btn btn-sm btn-primary text-primary',
            'texto': 'Ticket',
            'icono': 'fas fa-file-pdf',
            'title': 'Descargar Ticket Venta ' + objeto.get_id_texto(),
            'key': str(objeto.id) + "-" + accion,
        })

        puede_comanda = objeto.comprobar_puede_emitir_comanda()
        if puede_comanda:
            accion = 'comanda'
            operaciones.append({
                'accion': accion,
                'clase': 'btn btn-sm btn-success text-success',
                'texto': 'Comanda',
                'icono': 'fas fa-file-alt',
                'title': 'Descargar Comanda Venta ' + objeto.get_id_texto(),
                'key': str(objeto.id) + "-" + accion,
            })

        puede_anular = objeto.comprobar_puede_anular(logueado)
        if puede_anular:
            accion = 'anular'
            operaciones.append({
                'accion': accion,
                'clase': 'btn btn-sm btn-danger text-danger',
                'texto': 'Anular',
                'icono': 'fa fa-window-close',
                'title': 'Anular Venta ' + objeto.get_id_texto(),
                'key': str(objeto.id) + "-" + accion,
            })
        return operaciones


class LineaSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer(read_only=True)

    class Meta:
        model = PedidoLinea
        fields = '__all__'

    # Método que devuelve los datos de la línea.
    def to_representation(self, instance):
        """Quito password"""
        ret = super().to_representation(instance)
        ret['subtotal_texto'] = locale.currency(instance.subtotal)
        ret['total_texto'] = locale.currency(instance.total)
        return ret


class PedidoSerializer(serializers.ModelSerializer):
    venta = VentaSerializer(read_only=True)
    usuario = UsuarioSerializer(read_only=True)
    lineas = LineaSerializer(many=True, read_only=True)
    operaciones = serializers.SerializerMethodField()

    class Meta:
        model = Pedido
        fields = '__all__'

    # Método que devuelve los datos del pedido.
    def to_representation(self, instance):
        logueado = get_usuario_logueado()

        ret = super().to_representation(instance)
        ret['id_texto'] = instance.get_id_texto()
        ret['anulado'] = instance.comprobar_estado_anulado()
        ret['fecha_texto'] = instance.fecha.strftime('%d/%m/%Y %H:%M')
        ret['total_texto'] = instance.get_total_texto()
        ret['vuelto_texto'] = instance.get_vuelto_texto()
        ret['tiene_vuelto'] = instance.comprobar_tiene_vuelto()
        ret['tipo_texto'] = instance.get_tipo_texto()
        ret['tipo_delivery'] = instance.comprobar_tipo_delivery()
        ret['estado_texto'] = instance.get_estado_texto(logueado)
        ret['estado_clase'] = instance.get_estado_clase()
        ret['tarjeta_estado_clase'] = instance.get_tarjeta_estado_clase()
        ret['usuario_email'] = instance.usuario.email
        ret['usuario_nombre'] = instance.usuario.first_name
        ret['usuario_direccion'] = instance.usuario.direccion
        ret['mostrar_usuario'] = logueado.esAdmin or logueado.esVendedor
        ret['color_fondo'] = instance.get_color_fondo()
        ret['venta_id'] = instance.get_id_venta()
        return ret

    # Devuelve las operaciones de un pedido.
    def get_operaciones(self, objeto):
        logueado = get_usuario_logueado()
        operaciones = []

        puede_visualizar = objeto.comprobar_puede_visualizar(logueado)
        if puede_visualizar:
            accion = 'visualizar'
            operaciones.append({
                'accion': accion,
                'clase': 'btn btn-sm btn-info text-info',
                'clase_responsive': 'bg-info',
                'texto': 'Ver',
                'icono': 'fa fa-eye',
                'title': 'Ver Pedido ' + objeto.get_id_texto(),
                'key': str(objeto.id) + "-" + accion,
            })

        puede_entregar = objeto.comprobar_puede_entregar(logueado)
        if puede_entregar:
            accion = 'entregar'
            operaciones.append({
                'accion': accion,
                'clase': 'btn btn-sm btn-success text-success',
                'clase_responsive': 'bg-success',
                'texto': 'Entregar',
                'icono': 'fa fa-check-circle',
                'title': 'Entregar Pedido ' + objeto.get_id_texto(),
                'key': str(objeto.id) + "-" + accion,
            })

        puede_marcar_disponible = objeto.comprobar_puede_marcar_disponible(logueado)
        if puede_marcar_disponible:
            accion = 'disponible'
            operaciones.append({
                'accion': 'disponible',
                'clase': 'btn btn-sm btn-success text-success',
                'clase_responsive': 'bg-success',
                'texto': 'Disponible',
                'icono': 'fa fa-check-circle',
                'title': 'Marcar Pedido ' + objeto.get_id_texto() + " como disponible",
                'key': str(objeto.id) + "-" + accion,
            })

        puede_imprimir_venta = objeto.comprobar_puede_imprimir_venta(logueado)
        if puede_imprimir_venta:
            accion = 'venta'
            operaciones.append({
                'accion': 'venta',
                'clase': 'btn btn-sm btn-primary text-primary',
                'clase_responsive': 'bg-primary',
                'texto': 'Ticket',
                'icono': 'fas fa-file-pdf',
                'title': 'Marcar Pedido ' + objeto.get_id_texto() + " como disponible",
                'key': str(objeto.id) + "-" + accion,
            })

        puede_emitir_comanda = objeto.comprobar_puede_emitir_comanda(logueado)
        if puede_emitir_comanda:
            accion = 'comanda'
            operaciones.append({
                'accion': 'comanda',
                'clase': 'btn btn-sm btn-primary text-primary',
                'clase_responsive': 'bg-primary',
                'texto': 'Comanda',
                'icono': 'fas fa-file-alt',
                'title': 'Descargar Comanda Pedido ' + objeto.get_id_texto(),
                'key': str(objeto.id) + "-" + accion,
            })

        puede_anular = objeto.comprobar_puede_anular(logueado)
        if puede_anular:
            accion = 'anular'
            operaciones.append({
                'accion': 'anular',
                'clase': 'btn btn-sm btn-danger text-danger',
                'clase_responsive': 'bg-danger',
                'texto': 'Anular',
                'icono': 'fa fa-window-close',
                'title': 'Anular Pedido ' + objeto.get_id_texto(),
                'key': str(objeto.id) + "-" + accion,
            })
        return operaciones
