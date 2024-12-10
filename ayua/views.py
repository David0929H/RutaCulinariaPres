from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Pedido, Plato, Orden, PedidoPlato
from .forms import ClienteRegistroForm, OrdenForm, PlatoForm
from datetime import date, timedelta
from django.http import HttpResponse
from itertools import groupby
from operator import itemgetter
from django.core.paginator import Paginator
from django.db.models import Q


@login_required
def menu(request):
    if request.method == 'POST':
        platos_seleccionados = request.POST.getlist('platos')
        if platos_seleccionados:
            request.session['platos_seleccionados'] = platos_seleccionados
            return redirect('orden_actual')  

        messages.error(request, "No seleccionaste ningún plato.")
        return redirect('menu')


    items = Plato.objects.all()
    return render(request, 'inicio.html', {'menu_items': items})

@login_required
def orden_actual(request):
    platos_ids = request.session.get('platos_seleccionados', [])
    platos = Plato.objects.filter(id__in=platos_ids)
    today = date.today().isoformat()

    if not platos.exists():
        messages.error(request, "No hay platos seleccionados.")
        return redirect('pagina_principal')

    if request.method == 'POST':
        fecha_retiro = request.POST.get('fecha_retiro')
        hora_retiro = request.POST.get('hora_retiro')

        if not fecha_retiro or not hora_retiro:
            messages.error(request, "Debes seleccionar una fecha y hora de retiro.")
            return redirect('orden_actual')

        for plato in platos:
            cantidad = int(request.POST.get(f'cantidad_{plato.id}', 1))
            if cantidad > 0:
                orden_existente = Orden.objects.filter(
                    cliente=request.user,
                    plato=plato,
                    fecha_retiro=fecha_retiro,
                    hora_retiro=hora_retiro,
                    confirmado=False
                ).first()

                if orden_existente:
                    orden_existente.cantidad += cantidad
                    orden_existente.precio_total = orden_existente.cantidad * plato.precio
                    orden_existente.save()
                else:
                    Orden.objects.create(
                        cliente=request.user,
                        plato=plato,
                        cantidad=cantidad,
                        fecha_retiro=fecha_retiro,
                        hora_retiro=hora_retiro,
                        precio_total=plato.precio * cantidad,
                        confirmado=False,
                        estado='pendiente'
                    )

        if 'guardar_carrito' in request.POST:
            messages.success(request, "Pedidos guardados en el carrito.")
            return redirect('carrito')

        elif 'confirmar_pedido' in request.POST:
            for plato in platos:
                pedido = Orden.objects.filter(
                    cliente=request.user,
                    plato=plato,
                    fecha_retiro=fecha_retiro,
                    hora_retiro=hora_retiro,
                    confirmado=False
                ).first()

                if pedido:
                    pedido.confirmado = True
                    pedido.estado = 'pendiente'
                    pedido.save()

            messages.success(request, "Pedido confirmado.")
            return redirect('perfil_cliente')

    # Calcular subtotales dinámicos para el HTML
    for plato in platos:
        plato.subtotal = plato.precio * 1  # Cantidad inicial por defecto = 1
    total = sum(plato.subtotal for plato in platos)

    return render(request, 'orden_actual.html', {'platos': platos, 'total': total, 'today': today})


@login_required
def carrito_view(request):
    pedidos = Orden.objects.filter(cliente=request.user, confirmado=False)
    total = sum(pedido.precio_total for pedido in pedidos)

    return render(request, 'carrito.html', {
        'pedidos': pedidos,
        'total': total
    })

def confirmar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    if request.method == 'POST':
        pedido.confirmado = True
        pedido.estado = 'pendiente'
        pedido.save()
        return redirect('perfil_cliente')
    return redirect('orden_actual')

@login_required
def guardar_pedido(request, plato_id):
    plato = get_object_or_404(Plato, id=plato_id)
    
    if request.method == 'POST':
        cantidad = int(request.POST.get('cantidad', 1))
        fecha_retiro = request.POST.get('fecha_retiro')
        hora_retiro = request.POST.get('hora_retiro')
        
        pedido = Orden.objects.create(
            cliente=request.user,
            plato=plato,
            cantidad=cantidad,
            fecha_retiro=fecha_retiro,
            hora_retiro=hora_retiro,
            precio_total=plato.precio * cantidad,
            confirmado=False
        )
        pedido.save()
        return redirect('carrito')

@login_required
def eliminar_pedido(request, pedido_id):
    pedido = get_object_or_404(Orden, id=pedido_id)
    pedido.delete()
    return redirect('carrito')

def editar_pedido(request, pedido_id):
    pedido = get_object_or_404(Orden, id=pedido_id)

    if request.method == 'POST':
        form = OrdenForm(request.POST, instance=pedido)
        if form.is_valid():
            pedido = form.save(commit=False)
            pedido.precio_total = pedido.cantidad * pedido.plato.precio
            pedido.save()
            return redirect('carrito')
    else:
        form = OrdenForm(instance=pedido)

    return render(request, 'orden_actual.html', {'form': form, 'plato': pedido.plato, 'pedido': pedido})

@login_required
def finalizar_pedido(request, pedido_id):
    pedido = get_object_or_404(Orden, id=pedido_id, cliente=request.user)
    pedido.confirmado = True
    pedido.estado = 'pendiente'
    pedido.save()
    return redirect('perfil_cliente')

def admin_required(login_url='login_admin'):
    return user_passes_test(lambda u: u.is_staff, login_url=login_url)

def mostrar_inicio(request):
    menu_items = Plato.objects.all() 
    return render(request, 'inicio.html', {'menu_items': menu_items})

def login_cliente(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        usuario = authenticate(request, username=username, password=password)
        if usuario is not None:
            login(request, usuario)
            return redirect('pagina_principal')
        else:
            messages.error(request, 'Nombre de usuario o contraseña incorrectos')
    return render(request, 'login_cliente.html')

def login_admin(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('ordenes')
    return render(request, 'login_admin.html')

def registro_cliente(request):
    if request.method == 'POST':
        form = ClienteRegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Te has registrado exitosamente.")
            return redirect('pagina_principal')
        else:
            messages.error(request, "Por favor corrige los errores.")
    else:
        form = ClienteRegistroForm()
    return render(request, 'registro_cliente.html', {'form': form})

def cerrar_sesion(request):
    logout(request)
    return redirect('pagina_principal')

@login_required
def perfil_cliente(request):
    # Obtiene todas las órdenes confirmadas para el cliente actual
    pedidos = Orden.objects.filter(cliente=request.user, confirmado=True).order_by('-fecha_retiro')
    return render(request, 'perfil_cliente.html', {'pedidos': pedidos})


@login_required
@admin_required()
def menu_admin(request, plato_id=None):
    platos = Plato.objects.all()
    plato = None

    if plato_id:
        plato = get_object_or_404(Plato, id=plato_id)

    if request.method == "POST":
        if plato:
            form = PlatoForm(request.POST, request.FILES, instance=plato)
        else:
            form = PlatoForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            return redirect('menu_admin')
    else:
        form = PlatoForm(instance=plato)

    return render(request, 'menu_admin.html', {'platos': platos, 'form': form, 'plato': plato})

@admin_required()
def todas_ordenes(request):
    query = request.GET.get('query', '')
    filtro_estado = request.GET.get('filtro_estado', 'todos')
    pedidos = Orden.objects.all()

    if filtro_estado != 'todos':
        pedidos = pedidos.filter(estado=filtro_estado)

    context = {
        'pedidos': pedidos,
        'query': query,
        'filtro_estado': filtro_estado,
    }
    return render(request, 'ordenes.html', context)




@admin_required()
def aceptar_pedido(request, pedido_id):
    pedido = get_object_or_404(Orden, id=pedido_id)
    if request.method == 'POST':
        pedido.estado = 'aceptado'
        pedido.confirmado = True
        if not pedido.codigo_autenticacion:
            pedido.generar_codigo()
        pedido.save()
        messages.success(request, f"Pedido aceptado. Código de autenticación: {pedido.codigo_autenticacion}")
    return redirect('ordenes')

@login_required
@admin_required()
def editar_plato(request, id):
    plato = Plato.objects.get(id=id)
    form=PlatoForm(instance=plato)
    if request.method == 'POST':
        form=PlatoForm(request.POST, instance=plato)
        if form.is_valid():
            form.save()
        return redirect('menu_admin')
    data={'form':form}
    return render(request, 'menu_admin.html', data)



@login_required
@admin_required()
def eliminar_plato(request, id):
    plato = Plato.objects.get(id=id)
    plato.delete()
    return redirect('menu_admin')

@admin_required()
def pagado_pedido(request, pedido_id):
    pedido = get_object_or_404(Orden, id=pedido_id)
    if request.method == 'POST':
        pedido.estado = 'pagado'
        pedido.save()
        messages.success(request, f"Pedido marcado como pagado.")
    return redirect('ordenes')
    
@admin_required()
def cancelar_pedido(request, pedido_id):
    pedido = get_object_or_404(Orden, id=pedido_id)
    if request.method == 'POST':
        motivo = request.POST.get('motivo_rechazo', '')
        if motivo:
            pedido.estado = 'cancelado'
            pedido.motivo_rechazo = motivo
            pedido.save()
            messages.error(request, "Pedido cancelado.")
    return redirect('ordenes')

@admin_required()
def registro_pedidos(request):
    dia_anterior = date.today() - timedelta(days=1)
    

    pedidos_anteriores = Orden.objects.filter(fecha_retiro=dia_anterior)

    pedidos_pagados = Orden.objects.filter(estado='pagado')
    pedidos_cancelados = Orden.objects.filter(estado='cancelado')

    if request.GET.get('descargar') == 'txt':
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="registro_pedidos.txt"'
        
        lines = []
        for pedido in pedidos_anteriores | pedidos_pagados | pedidos_cancelados:
            lines.append(f"Cliente: {pedido.cliente.username}\n")
            lines.append(f"Plato: {pedido.plato.nombre}\n")
            lines.append(f"Cantidad: {pedido.cantidad}\n")
            lines.append(f"Fecha de Retiro: {pedido.fecha_retiro}\n")
            lines.append(f"Hora de Retiro: {pedido.hora_retiro}\n")
            lines.append(f"Precio Total: ${pedido.precio_total}\n")
            lines.append(f"Estado: {pedido.estado}\n")
            if pedido.estado == 'cancelado' and pedido.motivo_rechazo:
                lines.append(f"Motivo de Cancelación: {pedido.motivo_rechazo}\n")
            lines.append(f"Código de Autenticación: {pedido.codigo_autenticacion}\n")
            lines.append("-" * 40 + "\n")
        
        response.writelines(lines)
        return response

    context = {
        'pedidos_anteriores': pedidos_anteriores,
        'pedidos_pagados': pedidos_pagados,
        'pedidos_cancelados': pedidos_cancelados,
        'dia_anterior': dia_anterior
    }
    return render(request, 'registro_pedidos.html', context)

def descargar_registro(request):
    dia_anterior = date.today() - timedelta(days=1)
    pedidos = Orden.objects.filter(fecha_retiro=dia_anterior)
    
    contenido = ""
    for pedido in pedidos:
        contenido += f"Cliente: {pedido.cliente.username}\n"
        contenido += f"Plato: {pedido.plato.nombre}\n"
        contenido += f"Cantidad: {pedido.cantidad}\n"
        contenido += f"Precio Total: ${pedido.precio_total}\n"
        contenido += f"Estado: {pedido.estado}\n"
        contenido += "-"*30 + "\n"

    response = HttpResponse(contenido, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="registro_pedidos.txt"'
    return response

@login_required
def gestionar_clientes(request):
    if not request.user.is_staff:  # Solo los administradores pueden acceder
        messages.error(request, "No tienes permiso para acceder a esta página.")
        return redirect('pagina_principal')

    clientes = User.objects.filter(is_staff=False).order_by('username')  # Filtrar solo clientes

    if request.method == 'POST':
        cliente_id = request.POST.get('cliente_id')
        cliente = get_object_or_404(User, id=cliente_id)

        if cliente.is_staff:
            messages.error(request, "No puedes eliminar usuarios administrativos.")
        else:
            cliente.delete()
            messages.success(request, f"El cliente {cliente.username} ha sido eliminado.")

        return redirect('gestionar_clientes')

    return render(request, 'gestionar_clientes.html', {'clientes': clientes})