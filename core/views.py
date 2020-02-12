
from django.shortcuts import render, redirect
from django.views.generic import ListView,CreateView,UpdateView,DeleteView,TemplateView
from .models import *
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from .forms import CajeroForm,PuntoVentaForm,TerminalForm
from django.http import HttpResponse, JsonResponse
import json
from django.db.models import Count


from django.template.response import TemplateResponse
from django.db.models import Sum
import datetime


# Create your views here.
class Home(LoginRequiredMixin,TemplateView):
	
	template_name=	'dashboard.html'
	login_url='/login'
	context_object_name='obj'

def set_table_data(allset_aggregate, allset_carton_charts_aggregate):
	table_data = []
	for i in range(len(allset_aggregate)):
		line_keno = allset_aggregate[i]
		line_cartas = allset_carton_charts_aggregate[i]
		
		# add tickets from two tables (keno + cartas)
		line_cartas['tickets'] += line_keno['tickets']

		# add ventas from two tables (keno + cartas)
		line_cartas['ventas'] += line_keno['ventas']

		# calculate premios
		filterd_set_ganadoreskeno = GanadoresKeno.objects.all().filter( id_c_k__id_cajero__id_pos_pc__id_pv__localidad=line_keno['id_cajero__id_pos_pc__id_pv__localidad'] ).filter( id_c_k__id_cajero__id_pos_pc__id_pv__nombre_pv=line_keno['id_cajero__id_pos_pc__id_pv__nombre_pv'] )
		premios_ganadoreskeno = filterd_set_ganadoreskeno.aggregate(Sum('valor_ganado_k'))['valor_ganado_k__sum']
		
		filterd_set_ganadorescartas = GanadoresCartas.objects.all().filter( id_c_c__id_cajero__id_pos_pc__id_pv__localidad=line_keno['id_cajero__id_pos_pc__id_pv__localidad'] ).filter( id_c_c__id_cajero__id_pos_pc__id_pv__nombre_pv=line_keno['id_cajero__id_pos_pc__id_pv__nombre_pv'] )
		premios_ganadorescartas = filterd_set_ganadorescartas.aggregate(Sum('valor_ganado_c'))['valor_ganado_c__sum']

		line_cartas['premios'] = premios_ganadoreskeno + premios_ganadorescartas
		
		# calculate saldo
		line_cartas['saldo'] = line_cartas['premios'] - line_cartas['ventas']

		# calculate percentage
		if line_cartas['ventas'] != 0:
			line_cartas['percentage'] = round(line_cartas['premios'] * 100 / line_cartas['ventas'], 2)
		else:
			line_cartas['percentage'] = 0

		table_data.append(line_cartas)
	return table_data


# class Reportes(LoginRequiredMixin,ListView):
class Reportes(ListView):
    
	model:CartonKeno
	template_name=	'reportes.html'
	context_object_name='obj'
	queryset = []
	allset = CartonKeno.objects.all()
	allset_aggregate = allset.values('id_cajero__id_pos_pc__id_pv__localidad', 'id_cajero__id_pos_pc__id_pv__nombre_pv').order_by('id_cajero__id_pos_pc__id_pv__localidad').annotate(tickets=Count('id_c_k'), ventas=Sum('valor_apuesta_k'))
	# queryset.append(allset_aggregate)

	allset_carton_charts = CartonCartas.objects.all()
	allset_carton_charts_aggregate = allset_carton_charts.values('id_cajero__id_pos_pc__id_pv__localidad', 'id_cajero__id_pos_pc__id_pv__nombre_pv').order_by('id_cajero__id_pos_pc__id_pv__localidad').annotate(tickets=Count('id_c_c'), ventas=Sum('valor_apuesta_c'))
	    
	
	# add ventas from two queryset list
	table_data = set_table_data(allset_aggregate, allset_carton_charts_aggregate)

	queryset.append(table_data)

	model:PuntoVenta
	filterset_localidad = PuntoVenta.objects.values('localidad').annotate(dcount=Count('localidad'))
	queryset.append(filterset_localidad)

	filterset_pdv = PuntoVenta.objects.values('nombre_pv').annotate(dcount=Count('nombre_pv'))
	queryset.append(filterset_pdv)



def ajax_reportes(request):
    # get post data
    localidad = request.POST.get('localidad') # localidad
    nombre_pv = request.POST.get('nombre_pv') # nombre_pv
    selecclonar = request.POST.get('selecclonar') # selecclonar (hoy, selecclone de)
    inicial = request.POST.get('inicial') # inicial date
    final = request.POST.get('final') # final date
    
	# response queryset as a list
    queryset = []

	# count and sum
    pdvs = 0
    tickets = 0
    ventas = 0 # sum of ventas from two tables (carton_keno & carton_cartas)
    ventas_list = [] # each ventas from two tables (carton_keno & carton_cartas)
    premios = 0 # sum of premios from two tables (carton_keno & carton_cartas)
    premios_list = [] # each premios from two tables (carton_keno & carton_cartas)
    saldo = 0
    percentage = 0

    if localidad == "" and nombre_pv == "":
    	# get all QuerySet
        # allset from CartonKeno
	    # allset = CartonKeno.objects.values('id_cajero').order_by('id_cajero').annotate(count=Count('id_cajero'))
	    allset = CartonKeno.objects.all().filter(fecha_keno__gte=inicial, fecha_keno__lte=final)
	    allset_aggregate = allset.values('id_cajero__id_pos_pc__id_pv__localidad', 'id_cajero__id_pos_pc__id_pv__nombre_pv').order_by('id_cajero__id_pos_pc__id_pv__localidad').annotate(tickets=Count('id_c_k'), ventas=Sum('valor_apuesta_k'))
		
		# allset from CartonCartas
	    allset_carton_charts = CartonCartas.objects.all().filter(fecha_cartas__gte=inicial, fecha_cartas__lte=final)
	    allset_carton_charts_aggregate = allset_carton_charts.values('id_cajero__id_pos_pc__id_pv__localidad', 'id_cajero__id_pos_pc__id_pv__nombre_pv').order_by('id_cajero__id_pos_pc__id_pv__localidad').annotate(tickets=Count('id_c_c'), ventas=Sum('valor_apuesta_c'))
	    
		# add ventas from two queryset list
	    table_data = set_table_data(allset_aggregate, allset_carton_charts_aggregate)
		
		# append all set for datatable
	    queryset.append(table_data)

		# get pdvs
    else:   	 
        # filtered QuerySet
	    # filterd_set from CartonKeno
	    if localidad != "" and nombre_pv != "":
	    	filterd_set = CartonKeno.objects.all().filter(fecha_keno__gte=inicial, fecha_keno__lte=final).filter( id_cajero__id_pos_pc__id_pv__localidad=localidad ).filter( id_cajero__id_pos_pc__id_pv__nombre_pv=nombre_pv )
	    	filterd_set_aggregate = filterd_set.values('id_cajero__id_pos_pc__id_pv__localidad', 'id_cajero__id_pos_pc__id_pv__nombre_pv').order_by('id_cajero__id_pos_pc__id_pv__localidad').annotate(tickets=Count('id_c_k'), ventas=Sum('valor_apuesta_k'))
	    elif localidad == "":
		    filterd_set = CartonKeno.objects.all().filter(fecha_keno__gte=inicial, fecha_keno__lte=final).filter( id_cajero__id_pos_pc__id_pv__nombre_pv=nombre_pv )
		    filterd_set_aggregate = filterd_set.values('id_cajero__id_pos_pc__id_pv__localidad', 'id_cajero__id_pos_pc__id_pv__nombre_pv').order_by('id_cajero__id_pos_pc__id_pv__localidad').annotate(tickets=Count('id_c_k'), ventas=Sum('valor_apuesta_k'))
	    else: # nombre_pv == "":
    		filterd_set = CartonKeno.objects.all().filter(fecha_keno__gte=inicial, fecha_keno__lte=final).filter( id_cajero__id_pos_pc__id_pv__localidad=localidad )
	    	filterd_set_aggregate = filterd_set.values('id_cajero__id_pos_pc__id_pv__localidad', 'id_cajero__id_pos_pc__id_pv__nombre_pv').order_by('id_cajero__id_pos_pc__id_pv__localidad').annotate(tickets=Count('id_c_k'), ventas=Sum('valor_apuesta_k'))
		
		# filter_set from CartonCartas
	    if localidad != "" and nombre_pv != "":
		    filterd_set_cartas = CartonCartas.objects.all().filter(fecha_cartas__gte=inicial, fecha_cartas__lte=final).filter( id_cajero__id_pos_pc__id_pv__localidad=localidad ).filter( id_cajero__id_pos_pc__id_pv__nombre_pv=nombre_pv )#.filter(fecha_keno__range=["2011-01-01", "2021-01-31"])
		    filterd_set_aggregate_cartas = filterd_set_cartas.values('id_cajero__id_pos_pc__id_pv__localidad', 'id_cajero__id_pos_pc__id_pv__nombre_pv').order_by('id_cajero__id_pos_pc__id_pv__localidad').annotate(tickets=Count('id_c_c'), ventas=Sum('valor_apuesta_c'))
	    elif localidad == "":
		    filterd_set_cartas = CartonCartas.objects.all().filter(fecha_cartas__gte=inicial, fecha_cartas__lte=final).filter( id_cajero__id_pos_pc__id_pv__nombre_pv=nombre_pv )
		    filterd_set_aggregate_cartas = filterd_set_cartas.values('id_cajero__id_pos_pc__id_pv__localidad', 'id_cajero__id_pos_pc__id_pv__nombre_pv').order_by('id_cajero__id_pos_pc__id_pv__localidad').annotate(tickets=Count('id_c_c'), ventas=Sum('valor_apuesta_c'))
	    else: # nombre_pv == "":
    		filterd_set_cartas = CartonCartas.objects.all().filter(fecha_cartas__gte=inicial, fecha_cartas__lte=final).filter( id_cajero__id_pos_pc__id_pv__localidad=localidad )
	    	filterd_set_aggregate_cartas = filterd_set_cartas.values('id_cajero__id_pos_pc__id_pv__localidad', 'id_cajero__id_pos_pc__id_pv__nombre_pv').order_by('id_cajero__id_pos_pc__id_pv__localidad').annotate(tickets=Count('id_c_c'), ventas=Sum('valor_apuesta_c'))
		
		# add ventas from two queryset list (CartonKeno + CartonCartas)
	    table_data = set_table_data(filterd_set_aggregate, filterd_set_aggregate_cartas)
		# append filtered set for datatable
	    queryset.append(table_data)

		# get pdvs
	    pdvs = len(table_data)

		# calculate tickets
		# Count( CartonKeno.id_ck )
	    tickets = filterd_set.count() + filterd_set_cartas.count()

		# calculate the ventas
		# SUM( CartonKeno.valor_apuesta_k + CartonCartas.valor_apuesta_c )
	    vantas_cartonkeno = filterd_set.aggregate(Sum('valor_apuesta_k'))['valor_apuesta_k__sum']
	    
		# filterd_set_cartonCarts = CartonCartas.objects.all().filter( id_cajero__id_pos_pc__id_pv__localidad=localidad ).filter( id_cajero__id_pos_pc__id_pv__nombre_pv=nombre_pv ).filter( fecha_cartas__gte=inicial ).filter( fecha_cartas__lte=final )
	    if localidad != "" and nombre_pv != "":
		    filterd_set_cartonCarts = CartonCartas.objects.all().filter(fecha_cartas__gte=inicial, fecha_cartas__lte=final).filter( id_cajero__id_pos_pc__id_pv__localidad=localidad ).filter( id_cajero__id_pos_pc__id_pv__nombre_pv=nombre_pv )
	    elif localidad == "":
    		filterd_set_cartonCarts = CartonCartas.objects.all().filter(fecha_cartas__gte=inicial, fecha_cartas__lte=final).filter( id_cajero__id_pos_pc__id_pv__nombre_pv=nombre_pv )
	    else: # nombre_pv == "":
    		filterd_set_cartonCarts = CartonCartas.objects.all().filter(fecha_cartas__gte=inicial, fecha_cartas__lte=final).filter( id_cajero__id_pos_pc__id_pv__localidad=localidad )
		
	    vantas_cartoncarts = filterd_set_cartonCarts.aggregate(Sum('valor_apuesta_c'))['valor_apuesta_c__sum']
		
	    
	    if vantas_cartonkeno is not None: 
	        ventas += vantas_cartonkeno
	    
	    if vantas_cartoncarts is not None: 
	        ventas += vantas_cartoncarts

		# calculate the premios
		# SUM( GanadoresKeno.valor_ganado_k + GanadoresCartas.valor_ganado_c )
	    if localidad != "" and nombre_pv != "":
	    	filterd_set_ganadoreskeno = GanadoresKeno.objects.all().filter(id_c_k__fecha_keno__gte=inicial, id_c_k__fecha_keno__lte=final).filter( id_c_k__id_cajero__id_pos_pc__id_pv__localidad=localidad ).filter( id_c_k__id_cajero__id_pos_pc__id_pv__nombre_pv=nombre_pv )
	    elif localidad == "":
    		filterd_set_ganadoreskeno = GanadoresKeno.objects.all().filter(id_c_k__fecha_keno__gte=inicial, id_c_k__fecha_keno__lte=final).filter( id_c_k__id_cajero__id_pos_pc__id_pv__nombre_pv=nombre_pv )
	    else: # nombre_pv == "":
    		filterd_set_ganadoreskeno = GanadoresKeno.objects.all().filter(id_c_k__fecha_keno__gte=inicial, id_c_k__fecha_keno__lte=final).filter( id_c_k__id_cajero__id_pos_pc__id_pv__localidad=localidad )
		
	    premios_ganadoreskeno = filterd_set_ganadoreskeno.aggregate(Sum('valor_ganado_k'))['valor_ganado_k__sum']
		
	    if premios_ganadoreskeno is not None: 
	        premios += premios_ganadoreskeno
	    
	    if localidad != "" and nombre_pv != "":
	    	filterd_set_ganadorescartas = GanadoresCartas.objects.all().filter(id_c_c__fecha_cartas__gte=inicial, id_c_c__fecha_cartas__lte=final).filter( id_c_c__id_cajero__id_pos_pc__id_pv__localidad=localidad ).filter( id_c_c__id_cajero__id_pos_pc__id_pv__nombre_pv=nombre_pv )
	    elif localidad == "":
    		filterd_set_ganadorescartas = GanadoresCartas.objects.all().filter(id_c_c__fecha_cartas__gte=inicial, id_c_c__fecha_cartas__lte=final).filter( id_c_c__id_cajero__id_pos_pc__id_pv__nombre_pv=nombre_pv )
	    else: #nombre_pv == "":
    		filterd_set_ganadorescartas = GanadoresCartas.objects.all().filter(id_c_c__fecha_cartas__gte=inicial, id_c_c__fecha_cartas__lte=final).filter( id_c_c__id_cajero__id_pos_pc__id_pv__localidad=localidad )

	    premios_ganadorescartas = filterd_set_ganadorescartas.aggregate(Sum('valor_ganado_c'))['valor_ganado_c__sum']
		
	    if premios_ganadorescartas is not None: 
	        premios += premios_ganadorescartas

		# calculate the saldo
		# SUM( GanadoresKeno.valor_ganado_k + GanadoresCartas.valor_ganado_c ) - SUM( CartonKeno.valor_apuesta_k + CartonCartas.valor_apuesta_c )
	    saldo = premios - ventas

		# calculate the percentage
		# SUM( GanadoresKeno.valor_ganado_k + GanadoresCartas.valor_ganado_c ) * 100 / SUM( CartonKeno.valor_apuesta_k + CartonCartas.valor_apuesta_c )
	    if ventas is not 0:
		    percentage = premios * 100 / ventas 


    # filterd by localidad for localidad select list		
    filterset_localidad = PuntoVenta.objects.values('localidad').annotate(dcount=Count('localidad'))
    queryset.append(filterset_localidad)

	# filterd by nombre_pv for pdv select list
    filterset_pdv = PuntoVenta.objects.values('nombre_pv').annotate(dcount=Count('nombre_pv'))
    queryset.append(filterset_pdv)

	# return Response
	# obj : queryset
	# localidad : localidad
	# nombre_pv : nombre_pv
	# selecclonar : selecclonar
	# inicial : inicial
	# final : final
	# tickets : tickets
	# ventas : ventas
	# premios : premios
	# saldo : saldo
	# percentage : percentage		
	# pdvs : pdvs
    return TemplateResponse(request, 'reportes.html', {'obj':queryset, 'localidad':localidad, 'nombre_pv':nombre_pv, 'selecclonar':selecclonar, 'inicial':inicial, 'final':final, 'tickets':tickets, 'ventas':ventas, 'premios':premios, 'saldo':saldo, 'percentage':percentage, 'pdvs':pdvs})
    

class CajeroCreate(LoginRequiredMixin,CreateView):
	model = Cajero
	form_class = CajeroForm
	template_name = "cajeros.html"
	context_object_name = "obj"
	success_url = reverse_lazy('core:cajerosall')
	login_url='/login'

	def form_valid(self, form):
		form.instance.user = self.request.user.id
		return super().form_valid(form)

class CajeroViews(LoginRequiredMixin,ListView):
	Model:Cajero
	template_name="cajerosall.html"
	context_object_name="obj"
	#queryset = Cajero.objects.all()
	login_url='/login'

	def get_queryset(self, *args, **kwargs):
		return Cajero.objects.filter(id_pos_pc__id_pv__user=self.request.user)

class CajeroUpdate(LoginRequiredMixin,UpdateView):
	model = Cajero
	form_class = CajeroForm
	template_name = "cajeros_edit.html"
	success_url = reverse_lazy('core:cajerosall')
	context_object_name = "obj"
	

	def form_valid(self, form):
		form.instance.user = self.request.user.id
		return super().form_valid(form)

class CajeroDelete(LoginRequiredMixin,DeleteView):
	model = Cajero
	context_object_name = "obj"
	form_class = CajeroForm
	template_name = "cajeros_delete.html"
	success_url = reverse_lazy('core:cajerosall')
	login_url='/login'

	def form_valid(self, form):
		form.instance.user = self.request.user.id
		return super().form_valid(form)

def cajero_inactivar(request, id_cajero):
	template_name = 'cajeros_delete.html'
	contexto = {}
	cajero = Cajero.objects.filter(pk=id_cajero).first()

	if not cajero:
		return HttpResponse('Cajero no encontrado' + str(id_cajero))

	if request.method=='GET':
		contexto={'obj':cajero}

	if request.method=='POST':
		cajero.estado_cajero="inactivo"
		cajero.save()
		contexto={'obj':'OK'}
		return HttpResponse('Cajero inactivado')

	return render(request,template_name,contexto)

class PuntoventaViews(LoginRequiredMixin,ListView):
	Model:PuntoVenta
	template_name="Allpv.html"
	context_object_name="obj"
	#queryset = PuntoVenta.objects.all()
	login_url='/login'

	def get_queryset(self, *args, **kwargs):
		return PuntoVenta.objects.filter(user=self.request.user)

class PuntoVentaCreate(CreateView):
	model = PuntoVenta
	form_class = PuntoVentaForm
	template_name = "puntoventa.html"
	success_url = reverse_lazy('core:allpv')

class PuntoVentaUpdate(LoginRequiredMixin,UpdateView):
	model = PuntoVenta
	form_class = PuntoVentaForm
	template_name = "puntoventa_edit.html"
	success_url = reverse_lazy('core:allpv')
	context_object_name = "obj"
	

	"""def form_valid(self, form):
		form.instance.user = self.request.user.id
		return super().form_valid(form)"""

def puntoventa_inactivar(request, id_pv):
	template_name = 'puntoventa_delete.html'
	contexto = {}
	puntoventa = PuntoVenta.objects.filter(pk=id_pv).first()

	if not puntoventa:
		return HttpResponse('Punto de Venta no encontrado' + str(id_pv))

	if request.method=='GET':
		contexto={'obj':puntoventa}

	if request.method=='POST':
		puntoventa.estado_pv="inactivo"
		puntoventa.save()
		contexto={'obj':'OK'}
		return HttpResponse('Punto de Venta inactivado')

	return render(request,template_name,contexto)

class TermnalesViews(LoginRequiredMixin,ListView):
	Model:PosPc
	template_name="terminalesall.html"
	context_object_name="obj"
	#queryset = PosPc.objects.all()
	login_url='/login'

	def get_queryset(self, *args, **kwargs):
		return PosPc.objects.filter(id_pv__user=self.request.user)

class TerminalCreate(CreateView):
	model = PosPc
	form_class = TerminalForm
	template_name = "terminal_create.html"
	success_url = reverse_lazy('core:terminalesall')

class TerminalUpdate(LoginRequiredMixin,UpdateView):
	model = PosPc
	form_class = TerminalForm
	template_name = "terminal_edit.html"
	success_url = reverse_lazy('core:terminalesall')
	context_object_name = "obj"
	

	"""def form_valid(self, form):
		form.instance.user = self.request.user.id
		return super().form_valid(form)"""

def terminal_inactivar(request, id_pos_pc):
	template_name = 'terminal_delete.html'
	contexto = {}
	terminal = PosPc.objects.filter(pk=id_pos_pc).first()

	if not terminal:
		return HttpResponse('Terminal no encontrado' + str(id_pv))

	if request.method=='GET':
		contexto={'obj':terminal}

	if request.method=='POST':
		terminal.estado_pos_pc="inactivo"
		terminal.save()
		contexto={'obj':'OK'}
		return HttpResponse('Terminal inactivado')

	return render(request,template_name,contexto)



