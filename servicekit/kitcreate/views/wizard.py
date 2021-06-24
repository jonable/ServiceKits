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

from kitcreate.views import not_a_weekend_date, minus_business_days, add_business_days

# edit form in parts.

from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
staff_member_required = user_passes_test(
	lambda u: u.is_authenticated() and u.is_active and u.is_staff)

class StaffMemberRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
	def test_func(self):
		u = self.request.user
		return u.is_authenticated() and u.is_active and u.is_staff

DEFAULT_TEMPLATE = "kitcreate/v2/edit-wizard.html"

class EventInfoCreate(StaffMemberRequiredMixin, TemplateView):
	# "kitcreate/v2/create-wizard.html"
	# template_name = DEFAULT_TEMPLATE
	template_name = "kitcreate/v2/forms/eventinfo-create.html"
	form_class = EventInfoForm

	save_redirect = "edit_kit_info"
	save_and_continue_redirect = "edit_kit_schedule"

	def get(self, request, *args, **kwargs):		
		self.initial = {}
		form = self.form_class(initial=self.initial)
		return render(request, self.template_name, {'form': form})

	def post(self, request, *args, **kwargs):
		
		# eventinfo = get_object_or_404(EventInfo, pk=pk)		
		
		# if not eventinfo.form_version:
		# 	settings.FORM_VERSION
		_form_version = None

		form = self.form_class(request.POST)	
		form_version_changed = False
		
		if form.is_valid():			
			eventinfo = form.save()
			
			# create a service kit to add the default forms too
			form_version = eventinfo.form_version.pk
			
			# create a new ServiceKit obj (container for forms)
			# a new ServiceKit object is created each time a form is saved.
			servicekit = ServiceKit.objects.create(title=str(eventinfo.event_name))						
			# first time saving form apply the default items
			default_forms = ServiceKitForm.objects.filter(level__title="default_items", form_version=form_version)
			servicekit.forms.add(*default_forms)

			servicekit.save()
			eventinfo.service_kit = servicekit
			eventinfo.save()

			if not eventinfo.output_dir:	
				from kitcreate.views import create_directory
				create_directory(eventinfo, rebuild=True)
				
			return handle_save_action(request, 
				request.POST.get("on_save"), 
				eventinfo, 
				save_redirect=self.save_redirect, 
				save_and_continue_redirect=self.save_and_continue_redirect)


		return render(request, self.template_name, {'form': form})	

class EventInfoChange(StaffMemberRequiredMixin, TemplateView):
	
	# template_name = "kitcreate/wizard_2.html"
	template_name = DEFAULT_TEMPLATE
	form_class = EventInfoForm

	save_redirect = "edit_kit_info"
	save_and_continue_redirect = "edit_kit_schedule"

	def get(self, request, pk, *args, **kwargs):
		eventinfo = get_object_or_404(EventInfo, pk=pk)
		self.initial = {}
		self.instance = eventinfo
		form = self.form_class(initial=self.initial, instance=self.instance)
		return render(request, self.template_name, {'form': form, 'eventinfo': eventinfo})

	def post(self, request, pk, *args, **kwargs):
		
		eventinfo = get_object_or_404(EventInfo, pk=pk)		
		
		# if not eventinfo.form_version:
		# 	settings.FORM_VERSION
		_form_version = None
		if eventinfo.form_version:
			_form_version = int(eventinfo.form_version.pk)

		form = self.form_class(request.POST, instance=eventinfo)	
		form_version_changed = False
		
		if form.is_valid():			
			obj = form.save()
			form_version_changed = _form_version  != obj.form_version.pk			
			if form_version_changed:
				messages.info(request, 'Form Version Changed. Service Forms will need to be re-added.')
			return handle_save_action(request, 
				request.POST.get("on_save"), 
				eventinfo, 
				save_redirect=self.save_redirect, 
				save_and_continue_redirect=self.save_and_continue_redirect)


		return render(request, self.template_name, {'form': form, 'eventinfo': eventinfo})
		

class EventScheduleChange(StaffMemberRequiredMixin, TemplateView):
	
	# template_name = "kitcreate/wizard_2.html"
	template_name = DEFAULT_TEMPLATE
	form_class = EventScheduleFormFormset
	
	save_redirect = "edit_kit_schedule"
	save_and_continue_redirect = "edit_kit_pricelevel"

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

			return handle_save_action(request, request.POST.get("on_save"), eventinfo, save_redirect="edit_kit_schedule", save_and_continue_redirect=self.save_and_continue_redirect)	

		return render(request, self.template_name, {'form': form, 'eventinfo': eventinfo})

class PriceLevelChange(StaffMemberRequiredMixin, TemplateView):
	
	# template_name = "kitcreate/wizard_2.html"
	template_name = DEFAULT_TEMPLATE
	form_class = PriceLevelForm

	save_redirect = "edit_kit_pricelevel"
	save_and_continue_redirect = "edit_kit_services"

	def get(self, request, pk, *args, **kwargs):
		eventinfo = get_object_or_404(EventInfo, pk=pk)

		form_kwargs = {}
		self.initial = {}
		self.instance = eventinfo

		form = self.form_class()
		
		_obj = {}
		for level in eventinfo.price_levels.all():				
			key = level.type.title
			if form.fields.has_key(key):
				if not _obj.has_key(key):
					_obj[key] = []
				_obj[key].append(level.pk)
				# form.fields[key].initial = level.pk	
		for key, value in _obj.items():
			form.fields[key].initial = value	

		messages.warning(self.request, 'Changing Price Levels will clear all service forms associated with this service kit.')
		# context = {'on_save_action': 'Save and Select PL Forms'}
		return render(request, self.template_name, {'form': form, 'eventinfo': eventinfo, })

	def post(self, request, pk, *args, **kwargs):
		
		eventinfo = get_object_or_404(EventInfo, pk=pk)		
		form = self.form_class(request.POST)
		if form.is_valid():
			
			# Not really working?
			# if clean data is different than what is in eventinfo, remove those items from the service kit.
			if eventinfo.service_kit:
				for service_type_title, service_level_pk in form.cleaned_data.items():
					if service_level_pk:
						if not eventinfo.price_levels.filter(type__title=service_type_title, pk__in=service_level_pk):
							# clear all forms associated with changed service_type
		 					qs = eventinfo.service_kit.forms.filter(level__in=service_level_pk)
		 					if qs:
			 					eventinfo.service_kit.forms.remove(*[
			 						x.pk for x in qs
			 					])					

			eventinfo.price_levels.clear()
						
			flatten_pks = [item for sublist in form.cleaned_data.values() for item in sublist]
			for price_level in flatten_pks:
				if price_level:
					eventinfo.price_levels.add(price_level)	
			servicekit = ServiceKit.objects.create(title=str(eventinfo.event_name))
			
			if eventinfo.service_kit:
			# copy default forms and additional forms.
				servicekit.forms.add(*[x.pk for x in eventinfo.service_kit.forms.filter(level__type__title='Default')])
				servicekit.forms.add(*[x.pk for x in eventinfo.service_kit.forms.filter(level=None)])

			eventinfo.service_kit = servicekit		
			eventinfo.save()
			return handle_save_action(request, request.POST.get("on_save"), eventinfo, save_redirect=self.save_redirect, save_and_continue_redirect=self.save_and_continue_redirect)			

		return render(request, self.template_name, {'form': form, 'eventinfo': eventinfo, 'on_save_action': 'Save and Select PL Forms'})


class ServicesChange(StaffMemberRequiredMixin, TemplateView):
	
	# template_name = "kitcreate/wizard_2.html"
	template_name = DEFAULT_TEMPLATE
	form_class = ServiceSelectionForm

	save_redirect = "edit_kit_services"
	save_and_continue_redirect = "edit_kit_addforms"	

	def get(self, request, pk, *args, **kwargs):
		
		eventinfo = get_object_or_404(EventInfo, pk=pk)
		servicelevels = OrderedDict()
		form_kwargs = {}
		self.initial = {}
		self.instance = eventinfo

		for level in eventinfo.price_levels.all():				
			key = level.type.title
			if not servicelevels.has_key(key):
				servicelevels[key] = []	
			servicelevels[key].append(level.pk)

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
			if not servicelevels.has_key(key):
				servicelevels[key] = []	
			servicelevels[key].append(level.pk)

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
			eventinfo.service_kit.forms = sort_servicekit(eventinfo, default_order=previous_service_kit)
			return handle_save_action(request, request.POST.get("on_save"), eventinfo, save_redirect=self.save_redirect, save_and_continue_redirect=self.save_and_continue_redirect)

		return render(request, self.template_name, {'form': form, 'eventinfo': eventinfo})


class AdditionalFormChange(StaffMemberRequiredMixin, TemplateView):
	
	# template_name = "kitcreate/wizard_2.html"
	template_name = DEFAULT_TEMPLATE
	form_class = AdditionalFormsFormset
	save_redirect = "edit_kit_addforms"
	save_and_continue_redirect = "servicekit_complete"

	def get(self, request, pk, *args, **kwargs):
		eventinfo = get_object_or_404(EventInfo, pk=pk)
		self.initial = {}
		self.instance = eventinfo

		form = self.form_class()
		# this may fail, needs better testing
		addform_count = len(form.forms)
		for i, servicekitform in enumerate(eventinfo.service_kit.forms.filter(level=None)):
			if i > addform_count:
				empty_form = form.empty_form()
				empty_form.fields['form'].initial = servicekitform.pk
				form.forms.append(empty_form)
			else:
				form.forms[i].fields['form'].initial = servicekitform.pk
		
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
			for x in form.cleaned_data:
				if x.get('form') and x.get('form') != 'None' and not x.get(u'DELETE'):
					add_pks.append(x.get('form'))
				elif x.get('form') and x.get('form') != 'None' and x.get(u'DELETE'):
					remove_pks.append(x.get('form'))
			
			additionalforms = ServiceKitForm.objects.filter(pk__in=add_pks)
			servicekit.forms.remove(*remove_pks)			
			servicekit.forms.add(*additionalforms)
			
			return handle_save_action(request, 
				request.POST.get("on_save"), 
				eventinfo, 
				save_redirect=self.save_redirect, 
				save_and_continue_redirect=self.save_and_continue_redirect)

		return render(request, self.template_name, {'form': form, 'eventinfo': eventinfo})

def handle_save_action(request, action, eventinfo, save_redirect=None, save_and_continue_redirect=None):
	messages.success(request, 'Service Kit (%s) Saved.' % eventinfo)
	
	if action and action.lower() == 'save':
		return HttpResponseRedirect(reverse(save_redirect, args=(eventinfo.pk,)))
	
	if action and action.lower() == 'save and select pl forms':
		return HttpResponseRedirect(reverse("edit_kit_services", args=(eventinfo.pk,)))

	if action and action.lower() == 'save and continue':
		return HttpResponseRedirect(reverse(save_and_continue_redirect, args=(eventinfo.pk,)))

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
