# 05/07/2019 I HAVE NO IDEA WHAT I"M TRYING TO CHANGE BELOW INSIDE SERVICEKIT2 	

from collections import OrderedDict
from datetime import timedelta, datetime

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView
from django.views import View
from django.conf import settings
from django.contrib import messages


from kitcreate.forms import (
		EventInfoForm, PriceLevelForm, ServiceSelectionForm,
		EventScheduleFormFormset, AdditionalFormsFormset
	)
from kitcreate.models import (
		EventInfo, ServiceKit, ServiceKitForm, 
		ServiceType, ServiceLevel, EventSchedule
	)
# edit form in parts.


# EventInfo
#("eventinfo", EventInfoForm),
#("eventschedule", EventScheduleFormFormset),
#("pricelevelform", PriceLevelForm),
#("serviceselectionform", ServiceSelectionForm),		
#("additionalformsformset", AdditionalFormsFormset),

# urls
# url(r'^kits/edit/info/(?P<pk>\d+)/$', EventInfoChange.as_view(), name="edit_kit_info"),
# url(r'^kits/edit/schedule/(?P<pk>\d+)/$', EventScheduleChange.as_view(), name="edit_kit_schedule"),
# url(r'^kits/edit/pricelevel/(?P<pk>\d+)/$', PriceLevelChange.as_view(), name="edit_kit_pricelevel"),
# url(r'^kits/edit/services/(?P<pk>\d+)/$', ServicesChange.as_view(), name="edit_kit_services"),
# url(r'^kits/edit/addforms/(?P<pk>\d+)/$', AdditionalFormChange.as_view(), name="edit_kit_addforms"),



class EventInfoChange(TemplateView):
	
	template_name = "kitcreate/wizard_2.html"
	form_class = EventInfoForm

	def get(self, request, pk, *args, **kwargs):
		eventinfo = get_object_or_404(EventInfo, pk=pk)
		self.initial = {}
		self.instance = eventinfo
		form = self.form_class(initial=self.initial, instance=self.instance)
		return render(request, self.template_name, {'form': form, 'eventinfo': eventinfo})

	def post(self, request, pk, *args, **kwargs):
		eventinfo = get_object_or_404(EventInfo, pk=pk)		
		
		_form_version = int(eventinfo.form_version.pk)

		form = self.form_class(request.POST, instance=eventinfo)	
		form_version_changed = False
		
		if form.is_valid():			
			obj = form.save()
			form_version_changed = _form_version  != obj.form_version.pk			
			return handle_save_action(request, request.POST.get("on_save"), eventinfo, "edit_kit_info")

		return render(request, self.template_name, {'form': form, 'eventinfo': eventinfo})
		

class EventScheduleChange(TemplateView):
	
	template_name = "kitcreate/wizard_2.html"
	form_class = EventScheduleFormFormset
	

	def get(self, request, pk, *args, **kwargs):
		eventinfo = get_object_or_404(EventInfo, pk=pk)
		self.initial = {}
		self.instance = eventinfo
		form = self.form_class(initial=self.initial, instance=self.instance)
		return render(request, self.template_name, {'form': form, 'eventinfo': eventinfo})

	def post(self, request, pk, *args, **kwargs):
		eventinfo = get_object_or_404(EventInfo, pk=pk)		
		form = self.form_class(request.POST, instance=eventinfo)
		if form.is_valid():
			eventschedules = form.save()			
			company_in    = eventinfo.schedule.filter(type="company_in").order_by('date').first()
			exhibitor_in  = eventinfo.schedule.filter(type="exhibitor_in").order_by('date').first()
			exhibitor_out = eventinfo.schedule.filter(type="exhibitor_out").order_by('date').first()			

			if company_in and company_in.type == 'company_in' and company_in.date:
				if not eventinfo.schedule.filter(type="advance_ship_date"):
					_adv_ship_date = company_in.date - timedelta(settings.ADVANCE_SHIP_DATE_DAYS)
					advance_ship_date, created = EventSchedule.objects.get_or_create(type="advance_ship_date", event=eventinfo, date=_adv_ship_date)					
				
				if not eventinfo.schedule.filter(type="discount_date").first():
					_discount_date = not_a_weekend_date(company_in.date, settings.DISCOUNT_DATE_DAYS)
					discount_date, create = EventSchedule.objects.get_or_create(type="discount_date", event=eventinfo, date=_discount_date)					
					discount_date.save()
			# set direct ship date if non set by user.
			if exhibitor_in and exhibitor_in.type == 'exhibitor_in' and exhibitor_in.date:
				if not eventinfo.schedule.filter(type="direct_ship_date"):
					_direct_ship_date = exhibitor_in.date					
					direct_ship_date, created = EventSchedule.objects.get_or_create(type="direct_ship_date", event=eventinfo, date=_direct_ship_date)
					direct_ship_date.save()
			# set carrier pickup date if non set by user.
			if exhibitor_out and exhibitor_out.type == 'exhibitor_out' and (exhibitor_out.date and exhibitor_out.start_time):
				if not eventinfo.schedule.filter(type="carrier_pickup"):
					# _carrier_pickup_date = exhibitor_out.date + timedelta(hours=settings.CARRIER_PICKUP_HOURS)					
					_carrier_pickup_date = datetime.combine(exhibitor_out.date, exhibitor_out.start_time) + timedelta(hours=settings.CARRIER_PICKUP_HOURS)					
					# _carrier_pickup_time = _carrier_pickup_date.strftime('%I:%M %p')								
					carrier_pickup, created = EventSchedule.objects.get_or_create(
						type="carrier_pickup", 
						event=eventinfo, 
						date=_carrier_pickup_date, 
						start_time=_carrier_pickup_date.time()
					)

			return handle_save_action(request, request.POST.get("on_save"), eventinfo, "edit_kit_schedule")			

		return render(request, self.template_name, {'form': form, 'eventinfo': eventinfo})

class PriceLevelChange(TemplateView):
	
	template_name = "kitcreate/wizard_2.html"
	form_class = PriceLevelForm

	def get(self, request, pk, *args, **kwargs):
		eventinfo = get_object_or_404(EventInfo, pk=pk)

		form_kwargs = {}
		self.initial = {}
		self.instance = eventinfo

		form = self.form_class()
		for level in eventinfo.price_levels.all():				
			key = level.type.title
			if form.fields.has_key(key):
				form.fields[key].initial = level.pk	
		
		messages.warning(self.request, 'Changing Price Levels will clear all service forms associated with this service kit.')

		return render(request, self.template_name, {'form': form, 'eventinfo': eventinfo, 'on_save_action': 'Save and Select PL Forms'})

	def post(self, request, pk, *args, **kwargs):
		eventinfo = get_object_or_404(EventInfo, pk=pk)		
		form = self.form_class(request.POST)
		if form.is_valid():
			
			# Not really working?
			# if clean data is different than what is in eventinfo, remove those items from the service kit.
			for service_type_title, service_level_pk in form.cleaned_data.items():
				if service_level_pk:
					if not eventinfo.price_levels.filter(type__title=service_type_title, pk=service_level_pk):
						# clear all forms associated with changed service_type
	 					qs = eventinfo.service_kit.forms.filter(level=service_level_pk)
	 					if qs:
		 					eventinfo.service_kit.forms.remove(*[
		 						x.pk for x in qs
		 					])					

			eventinfo.price_levels.clear()
			for price_level in form.cleaned_data.values():
				if price_level:
					eventinfo.price_levels.add(price_level)	

			servicekit = ServiceKit.objects.create(title=str(eventinfo.event_name))

			####SERVICEKIT2####
			# for kit in eventinfo.service_kits2.all():
			# 	kit.active = False
			# 	kit.save()

			# servicekit2 = ServiceKit2.objects.create(event=eventinfo, active=True)
			# servicekit2.forms.add(*[x.pk for x in eventinfo.service_kit.forms.filter(level__type__title='Default')])
			# servicekit2.forms.add(*[x.pk for x in eventinfo.service_kit.forms.filter(level=None)])
			####ENDSERVICEKIT2####

			# copy default forms and additional forms.
			servicekit.forms.add(*[x.pk for x in eventinfo.service_kit.forms.filter(level__type__title='Default')])
			servicekit.forms.add(*[x.pk for x in eventinfo.service_kit.forms.filter(level=None)])

			eventinfo.service_kit = servicekit		
			eventinfo.save()
			return handle_save_action(request, request.POST.get("on_save"), eventinfo, "edit_kit_pricelevel")			

		return render(request, self.template_name, {'form': form, 'eventinfo': eventinfo, 'on_save_action': 'Save and Select PL Forms'})


class ServicesChange(TemplateView):
	
	template_name = "kitcreate/wizard_2.html"
	form_class = ServiceSelectionForm

	def get(self, request, pk, *args, **kwargs):
		
		eventinfo = get_object_or_404(EventInfo, pk=pk)
		servicelevels = OrderedDict()
		form_kwargs = {}
		self.initial = {}
		self.instance = eventinfo

		for level in eventinfo.price_levels.all():				
			key = level.type.title
			servicelevels[key] = level.pk

		form_kwargs = {
			"servicelevel": servicelevels, 
			"form_version": eventinfo and eventinfo.form_version or None
		}

		form = self.form_class(**form_kwargs)
		for servicekitform in eventinfo.service_kit.forms.all():
			key = servicekitform.title
			if servicekitform.title in form.fields:
				form.fields[key].initial = True
		
		return render(request, self.template_name, {'form': form, 'eventinfo': eventinfo})



	def post(self, request, pk, *args, **kwargs):
		eventinfo = get_object_or_404(EventInfo, pk=pk)		
		servicelevels = OrderedDict()
		servicekitforms = {}
		for level in eventinfo.price_levels.all():				
			key = level.type.title
			servicelevels[key] = level.pk

		form_kwargs = {
			"servicelevel": servicelevels, 
			"form_version": eventinfo and eventinfo.form_version or None
		}
		form = self.form_class(servicelevels, eventinfo and eventinfo.form_version or None, request.POST)
		
		if form.is_valid():
			# create a new service kit
			# servicekit = ServiceKit.objects.create(title=str(eventinfo.event_name))
			servicekit = eventinfo.service_kit

			# Add ServiceKitForm to ServiceKit
			# if we are resaving the service kit, load the previous service kit and get its default forms
			previous_service_kit = eventinfo.service_kit
			if previous_service_kit:
				servicekitforms['default_forms'] = [x.pk for x in previous_service_kit.forms.filter(level__type__title='Default')]
				servicekitforms['additional_forms'] = [x.pk for x in previous_service_kit.forms.filter(level=None)]
			# else add the default forms defined by the servicekitlevel "default_items"
			else:
				# first time saving form apply the default items
				servicekitforms['default_forms'] = ServiceKitForm.objects.filter(level__title="default_items", form_version=form_version)
			
			# need to do this...
			servicekit.forms.clear()
			servicekit.forms.add(*servicekitforms['default_forms'])		

			pks = form.get_servicekitforms_pks()
			servicekitforms['servicekitforms'] = ServiceKitForm.objects.filter(pk__in=pks).order_by('level__type')
			servicekit.forms.add(*servicekitforms['servicekitforms'])
			if servicekitforms['additional_forms']:				
				servicekit.forms.add(*servicekitforms['additional_forms'])
			
			servicekit.save()
			# Add Additional Forms
			eventinfo.service_kit = servicekit
			eventinfo.save()

			####SERVICEKIT2####
			# previous_service_kit = None
			# _previous_service_kit = eventinfo.service_kits2.all().order_by('-created_on')
			# if len(_previous_service_kit) > 1:
			# 	previous_service_kit = _previous_service_kit[1]

			# servicekit2 = eventinfo.service_kits2.filter(active=True).first()
			# servicekit2.forms.clear()
			# servicekit2.forms.add(*servicekitforms['default_forms'])
			# pks = form.get_servicekitforms_pks()
			# servicekitforms['servicekitforms'] = ServiceKitForm.objects.filter(pk__in=pks).order_by('level__type')
			# servicekit2.forms.add(*servicekitforms['servicekitforms'])
			# if servicekitforms['additional_forms']:				
			# 	servicekit2.forms.add(*servicekitforms['additional_forms'])	
			# servicekit2.forms = sort_servicekit(eventinfo, default_order=previous_service_kit)
			# servicekit2.save()
			####ENDSERVICEKIT2####


			eventinfo.service_kit.forms = sort_servicekit(eventinfo, default_order=previous_service_kit)
			return handle_save_action(request, request.POST.get("on_save"), eventinfo, "edit_kit_services")

		return render(request, self.template_name, {'form': form, 'eventinfo': eventinfo})


class AdditionalFormChange(TemplateView):
	
	template_name = "kitcreate/wizard_2.html"
	form_class = AdditionalFormsFormset


	def get(self, request, pk, *args, **kwargs):
		eventinfo = get_object_or_404(EventInfo, pk=pk)
		self.initial = {}
		self.instance = eventinfo

		form = self.form_class()
		# this may fail, needs better testing
		# check the amount of AdditionalFormsForm supplied
		addform_count = len(form.forms)
		# loop over all service kit forms in the event with no level 
		for i, servicekitform in enumerate(eventinfo.service_kit.forms.filter(level=None)):
			# if i is greater than length of forms. Add a new form the list
			# I imagine this is to make sure there is always enough forms if more than 7 additional forms are added.			
			if i > addform_count:
				# get an empty AdditioanlFormsForm
				empty_form = form.empty_form()
				# set the new form field's initial value to the service kit
				empty_form.fields['form'].initial = servicekitform.pk
				# append the new form to the formset.
				form.forms.append(empty_form)
			else:
				# if i is less than addform_count
				# add its initial value.
				form.forms[i].fields['form'].initial = servicekitform.pk
		
		####SERVICEKIT2####
		# self.initial = {}
		# self.instance = eventinfo
		# servicekit2 = eventinfo.service_kits2.filter(active=True).first()

		# form = self.form_class()
		# # this may fail, needs better testing
		# # check the amount of AdditionalFormsForm supplied
		# addform_count = len(form.forms)
		# # loop over all service kit forms in the event with no level 
		# for i, servicekitform in enumerate(servicekit2.forms.filter(level=None)):
		# 	# if i is greater than length of forms. Add a new form the list
		# 	# I imagine this is to make sure there is always enough forms if more than 7 additional forms are added.			
		# 	if i > addform_count:
		# 		# get an empty AdditioanlFormsForm
		# 		empty_form = form.empty_form()
		# 		# set the new form field's initial value to the service kit
		# 		empty_form.fields['form'].initial = servicekitform.pk
		# 		# append the new form to the formset.
		# 		form.forms.append(empty_form)
		# 	else:
		# 		# if i is less than addform_count
		# 		# add its initial value.
		# 		form.forms[i].fields['form'].initial = servicekitform.pk
		####ENDSERVICEKIT2####

		return render(request, self.template_name, {'form': form, 'eventinfo': eventinfo})

	def post(self, request, pk, *args, **kwargs):
		eventinfo = get_object_or_404(EventInfo, pk=pk)		
		form = self.form_class(request.POST)
		if form.is_valid():

			servicekit = eventinfo.service_kit
			# just append these forms to the current eventinfo.service_kit if they aren't already in there.
			add_pks = []
			remove_pks = []
			additionalforms = []
			# gets a list of additional forms to add and remove
			for x in form.cleaned_data:
				if x.get('form') and x.get('form') != 'None' and not x.get(u'DELETE'):
					add_pks.append(x.get('form'))
				elif x.get('form') and x.get('form') != 'None' and x.get(u'DELETE'):
					remove_pks.append(x.get('form'))
			
			# additionalforms = ServiceKitForm.objects.filter(pk__in=add_pks)
			for _pk in add_pks:
				additionalforms.append(ServiceKitForm.objects.filter(pk=add_pks))

			servicekit.forms.remove(*remove_pks)			
			servicekit.forms.add(*additionalforms)
			return handle_save_action(request, request.POST.get("on_save"), eventinfo, "edit_kit_addforms")

		####SERVICEKIT2####
		# if form.is_valid():

		# 	servicekit2 = eventinfo.service_kit2.filter(active=True)
		# 	# just append these forms to the current eventinfo.service_kit if they aren't already in there.
		# 	add_pks = []
		# 	remove_pks = []
		# 	additionalforms = []
		# 	# gets a list of additional forms to add and remove
		# 	for x in form.cleaned_data:
		# 		if x.get('form') and x.get('form') != 'None' and not x.get(u'DELETE'):
		# 			add_pks.append(x.get('form'))
		# 		elif x.get('form') and x.get('form') != 'None' and x.get(u'DELETE'):
		# 			remove_pks.append(x.get('form'))
			
		# 	# additionalforms = ServiceKitForm.objects.filter(pk__in=add_pks)
		# 	for _pk in add_pks:
		# 		additionalforms.append(ServiceKitForm.objects.filter(pk=add_pks))

		# 	servicekit2.forms.remove(*remove_pks)			
		# 	servicekit2.forms.add(*additionalforms)
		# 	servicekit2.save()
		# 	return handle_save_action(request, request.POST.get("on_save"), eventinfo, "edit_kit_addforms")
		####ENDSERVICEKIT2####

		return render(request, self.template_name, {'form': form, 'eventinfo': eventinfo})

def handle_save_action(request, action, eventinfo, save_and_finish_redirect):
	messages.success(request, 'Service Kit (%s) Saved.' % eventinfo)
	if action and action.lower() == 'save':
		return HttpResponseRedirect(reverse(save_and_finish_redirect, args=(eventinfo.pk,)))
	if action and action.lower() == 'save and select pl forms':
		return HttpResponseRedirect(reverse("edit_kit_services", args=(eventinfo.pk,)))
	return HttpResponseRedirect(reverse('servicekit_complete', kwargs={'pk':eventinfo.pk}))


def sort_servicekit(eventinfo, default_order=None):
	"""
	Applies a default order to service kit forms.
	If form is not in order, it will be added to the end.
	:eventinfo <kitcreate.models.EventInfo obj>
	:default_order <kitcreate.models.ServiceKit obj> user defined default order.
	"""
	# check if a previous servicekit exist and base form order off that first.
	# How To setup default servicekit object
	# Add a new servicekit object.
	# Use the same value for the servicekit.title as settings.KITFORMS_DEFAULT_SERVICEKIT_ORDER
	# Add all the ServiceKitForms to the new object.
	# run kitcreate.util.initial_default_servicekit_order's set_order(servicekit) function to set a default order.
	
	if not settings.KITFORMS_DEFAULT_SERVICEKIT_ORDER:
		raise Exception('KITFORMS_DEFAULT_SERVICEKIT_ORDER must be defined in settings.py. Value is equal to the default Service Kit\'s title')

	if not default_order:
		default_order = ServiceKit.objects.filter(title=settings.KITFORMS_DEFAULT_SERVICEKIT_ORDER).first()

	if not default_order:
		# initialize a default_order service kit.
		from kitcreate.utils.initial_default_servicekit_order import set_order
		default_order = ServiceKit.objects.create(title=settings.KITFORMS_DEFAULT_SERVICEKIT_ORDER)
		[default_order.forms.add(obj.pk) for obj in ServiceKitForm.objects.all()]		
		set_order(default_order)
		default_order.save()		
	
	order = [x.title for x in default_order.forms.all()]
	
	def _sort(x):
		# default_servicekit_order ServiceKit doesn't contain user upload forms
		# give them an unnasseary big index so they should up at hte end.
		if x.title in order:
			return order.index(x.title)
		else:
			return len(order) + 100
	if eventinfo.service_kit:
		return sorted(eventinfo.service_kit.forms.all(), key=_sort)
	return []
