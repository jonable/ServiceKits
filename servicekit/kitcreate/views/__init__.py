import os
import json
import requests
import zipfile


from shutil import copyfile
from collections import OrderedDict
from datetime import timedelta, datetime
# from shutil import copyfile
# 
from django.utils import six
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.utils.safestring import mark_safe
from django.shortcuts import render
from django.http import JsonResponse
from django.http import FileResponse
from django.views.decorators.cache import never_cache
from django.views.generic.list import ListView
from django.views.generic.edit import DeleteView, UpdateView
from django.contrib import messages
# from django.contrib.auth import authenticate, login
from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.response import SimpleTemplateResponse
from django.shortcuts import get_object_or_404

from background_task.models import Task
from filebrowser.base import FileListing, FileObject
from filebrowser.sites import site

from formtools.wizard.views import SessionWizardView

from mailmerge import MailMerge

from kitcreate.utils.docxtopdf import forms_to_pdf
from kitcreate.utils.ep_dates import get_mapped_dates, get_eventschedule
# from kitcreate.utils.pdf_page_numbers import add_page_numbers
from kitcreate.forms import (
	EventInfoForm, EventScheduleFormFormset, SortSkFormsForm,
	PriceLevelForm, ServiceSelectionForm, AdditionalFormsFormset, 
	EventInfoStatusForm, EventInfoStorefrontStatusForm, SelectKitForm, 
	InternalNoteForm, UploadServiceKitForm, StatusMessageForm, ServicekitstatusForm
)
from kitcreate.notifications import (
	create_status_notification, create_storefrontstatus_notification, notification_generic
)
from kitcreate.kitcontext import ServiceKitContext, GSContext
from kitcreate.models import (
	Place, EventInfo, ServiceKitForm, ServiceType,
	ServiceKit, EventData, EventSchedule, 
	ServiceKitFieldValue, FormVersion
)



import logging
logger = logging.getLogger('django')

from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
staff_member_required = user_passes_test(
	lambda u: u.is_authenticated() and u.is_active and u.is_staff)

class StaffMemberRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
	def test_func(self):
		u = self.request.user
		return u.is_authenticated() and u.is_active and u.is_staff

class DeleteEventInfoView(DeleteView):
	"""Generic View to delete a Service Kit"""
	model = EventInfo
	success_url = '/'

class EventInfoListView(StaffMemberRequiredMixin, ListView):
	"""Generic View displaying all active Event's Service Kits"""
	model = EventInfo
	paginate_by = 25
	# see below for sorting
	# http://stackoverflow.com/questions/33350362/django-listview-form-to-filter-and-sort
	def get(self, request, *args, **kwargs):
		response = super(EventInfoListView, self).get(request, *args, **kwargs)
		return response
	
	def get_queryset(self, *args, **kwargs):
		search_val = self.request.GET.get('search', None)
		order_by = self.request.GET.get('_o', None)

		if not search_val and not order_by:
			return super(EventInfoListView, self).get_queryset(*args, **kwargs).order_by('event_name__event_code')
		
		new_context = []

		if search_val:
			new_context = EventInfo.objects.filter(
				event_name__description__icontains=search_val,
			)
		else:
			new_context = super(EventInfoListView, self).get_queryset(*args, **kwargs)

		if order_by:			
			if 'event_date' in order_by:
				new_context = EventInfo.objects.order_by_event_date(reverse=order_by.startswith('-'))
			else:
				new_context = new_context.order_by(order_by)
		
		return new_context

	def get_context_data(self, **kwargs):
		context = super(EventInfoListView, self).get_context_data(**kwargs)
		order_by = self.request.GET.get('_o', '')
		
		if order_by and order_by.startswith('-'):
			context['asc'] = ''
			context['order_by_field'] = order_by.replace('-', '')
		else:
			context['asc'] = '-'
			context['order_by_field'] = order_by

		if not order_by:
			context['asc'] = '-'

		context['search'] = self.request.GET.get('search', '')
		return context	

class ServiceKitWizard2(StaffMemberRequiredMixin, SessionWizardView):
	"""Form Wizard to create a service kit"""
	form_list = [		
		("eventinfo", EventInfoForm),
		("eventschedule", EventScheduleFormFormset),
		("pricelevelform", PriceLevelForm),
		("serviceselectionform", ServiceSelectionForm),		
		("additionalformsformset", AdditionalFormsFormset),
	]
	
	# template_name = 'kitcreate/wizard.html'
	template_name = 'kitcreate/v2/create-wizard.html'

	# def render(self, form=None, **kwargs):		

	# 	# TERRIBLE AF!
	# 	Really needs more testing
	# 	if self.steps.prev == 'serviceselectionform' and self.steps.current == 'extraformfieldvalues':
	# 		servicekitforms = ServiceKitForm.objects.filter(form_fields__isnull=False, title__in=[
	# 			k for k,x in self.get_cleaned_data_for_step('serviceselectionform').items() if x
	# 		])
	# 		if not servicekitforms:
	# 			if self.form_list.has_key('extraformfieldvalues'):
	# 				self.form_list.pop('extraformfieldvalues')
	# 			return self.render_goto_step('additionalformsformset')
		
	# 	if self.steps.prev == 'serviceselectionform' and self.steps.current == 'additionalformsformset':
	# 		servicekitforms = ServiceKitForm.objects.filter(form_fields__isnull=False, title__in=[
	# 			k for k,x in self.get_cleaned_data_for_step('serviceselectionform').items() if x
	# 		])
	# 		if servicekitforms:				
	# 			obj = OrderedDict()
	# 			for key, value in self.__class__.form_list:
	# 				obj[key] = value				
	# 			self.form_list = obj
	# 			return self.render_goto_step('extraformfieldvalues')

 # 		return super(ServiceKitWizard2, self).render(form=form, **kwargs)


	def get(self, request, *args, **kwargs):	
		# redirect if user tries to edit an approved or greater kit.
		eventinfo = self.get_eventinfo()
		if eventinfo and not eventinfo.is_editable:
			messages.warning(request, 'Can not edit kit "%s" with %s status.' % (eventinfo, eventinfo.status))			
			return HttpResponseRedirect(reverse('servicekit_complete', args=(eventinfo.pk,)))		
		return super(ServiceKitWizard2, self).get(request, *args, **kwargs)

	def get_context_data(self, form, **kwargs):
		context = super(ServiceKitWizard2, self).get_context_data(form=form, **kwargs)
		context.update({"eventinfo":self.get_eventinfo()})
		return context

	def get_form_kwargs(self, step):
		"""
		Gets the ServiceKitForms based on the selected ServiceLevels
		"""
		# kwargs passed to the forms __init__ method
		form_version = None
		if step == 'serviceselectionform':
			servicelevel = OrderedDict()
			eventinfo = self.get_eventinfo()

			# print('Check that pricelevel form works here.')
			# import ipdb; ipdb.set_trace()

			for k, v in sorted(self.get_cleaned_data_for_step('pricelevelform').items()):
				servicelevel[k] = v
				# if not servicelevel.has_key(k):
				# 	servicelevel[k] = []
				# servicelevel[k].append(v)
			
			eventinfo_form_data = self.get_cleaned_data_for_step('eventinfo')
			form_version = eventinfo_form_data.get('form_version')
			# if not form_verison and (eventinfo and eventinfo.form_version):
			# 	form_version = eventinfo.form_version
			# eventinfo and eventinfo.form_version or None
			return {"servicelevel": servicelevel, "form_version": form_version}

		return {}

	def get_form_initial(self, step):
		"""
		Gets default form info
		"""
		initial_dict = self.initial_dict.get(step, {})

		# Set default values for eventinfo step
		if step == 'eventinfo' and not self.get_eventinfo():
			# sets carrier default to SER.
			ser = Place.objects.filter(code="SERWORCMASS").first()
			if ser:
				initial_dict.update({"carrier": ser.pk})

		# load schedule data from EventPath into eventschedule step
		if step == 'eventschedule' and not self.get_eventinfo():
			event_pk = self.request.POST.get('eventinfo-event_name')
			if event_pk:
				event = EventData.objects.get(pk=event_pk)
				if event.data and event.data != [u""]:
					try:
						event_data   = get_mapped_dates(event.data)
						schedule     = get_eventschedule(event_data)
						initial_dict = schedule
					except Exception, e:
						messages.error(self.request, 'Could not load Eventpath data: %s' % (e))
						logger.error(e)

		return initial_dict

	def get_eventinfo(self):
		"""
		Helper method to get the eventinfo instance (cached vs db lookup)
		:return <EventInfo> or None
		"""
		# check if instance_dict cached eventinfo
		eventinfo = self.instance_dict.get('eventinfo')
		if eventinfo:
			return eventinfo
		# lookup eveninfo if the pk exists
		eventinfo_pk = self.kwargs.get('pk', '')
		if eventinfo_pk:
			eventinfo = EventInfo.objects.get(pk=eventinfo_pk)
			return eventinfo		

	def get_form(self, step=None, data=None, files=None):

		form = super(ServiceKitWizard2, self).get_form(step=step, data=data, files=files)
		# determine the step if not given
		if step is None:
			step = self.steps.current	
		# get eventinfo instances, if it exists
		eventinfo = self.get_eventinfo()
		# if step is price level, service selection, addtional forms 
		# and we are editing and we populate form data.
		
		if step == 'pricelevelform' and eventinfo:
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
		
		if ( step == 'pricelevelform' or step == 'serviceselectionform' or step == 'additionalformsformset') and eventinfo and not eventinfo.service_kit:			
			sk_list = ServiceKit.objects.filter(title=str(eventinfo.event_name))
			if sk_list:
				html = ("".join(["<li><a href=\"%s\">%s</a></li>" % 
					(reverse('fix_broken_servicekit', kwargs={"eventinfo_pk":eventinfo.pk, "servicekit_pk":x.pk}), x.title) for x in sk_list]))
				messages.warning(self.request, mark_safe('There was an error fetching the service kit for this event. <br>Either re-enter the information, or click one of the kits found by the application to reattach it to the Event. <ul>%s</ul>' % html))
			else:
				messages.warning(self.request, "There was an error fetching the servie kit for this event. Please re-enter the information.")

		if step == 'serviceselectionform' and eventinfo and eventinfo.service_kit:
			for servicekitform in eventinfo.service_kit.forms.all():
				key = servicekitform.title
				if servicekitform.title in form.fields:
					form.fields[key].initial = True
		# load additional forms from service kit if available. Else loads blank forms.
		if step == 'additionalformsformset' and eventinfo and eventinfo.service_kit:
			# this may fail, needs better testing
			derp = len(form.forms)
			for i, servicekitform in enumerate(eventinfo.service_kit.forms.filter(level=None)):
				if i > derp:
					empty_form = form.empty_form()
					empty_form.fields['form'].initial = servicekitform.pk
					form.forms.append(empty_form)
				else:
					form.forms[i].fields['form'].initial = servicekitform.pk

		return form

	def get_form_instance(self, step):
		"""
		Returns an object which will be passed to the form for `step`
		as `instance`. If no instance object was provided while initializing
		the form wizard, None will be returned.
		"""
		# gets the eventinfo object if editing
		eventinfo_pk = self.kwargs.get('pk', '')
		if eventinfo_pk:
			eventinfo = EventInfo.objects.get(pk=eventinfo_pk)
			self.instance_dict[step] = eventinfo

		return self.instance_dict.get(step, None)
		
	def done(self, form_list, **kwargs):
		"""
		Preps and Saves Wizard data.
		"""
		servicekitforms   = {}
		eventinfo         = None
		previous_service_kit = None
		eventinfoform     = form_list[0] #indexing form list may cause issues...
		eventscheduleform = form_list[1]
		pricelevelform    = form_list[2]
		# does an assertion test to make sure the wizard.form_list does not change (a better method probably exists to do this...)
		if type(eventinfoform) != EventInfoForm or type(eventscheduleform) != EventScheduleFormFormset or type(pricelevelform) != PriceLevelForm:
			raise Exception('form_list index has changed')		
		
		self.get_all_cleaned_data().get('form_version')
		# form_version = FormVersion.objects.filter(title=default_form_version).first()


		# save the current eventinfo form.
		is_edit = bool(eventinfoform.instance.pk)
		eventinfoform.instance.save()	
		eventinfo = eventinfoform.instance
		
		form_version = self.get_all_cleaned_data().get('form_version')
		form_version_changed = ('form_version' in eventinfoform.changed_data)
		# save form version on first go, after this adjust in admin
		if not is_edit and not eventinfo.form_version:
			eventinfo.form_version = form_version

		# if not is_edit:
		# 	eventinfo.servicekitstatus = EventInfo.SERVICEKITSTATUS.ae_pulled		
		# if the eventinfo was successfuly saved...

		# set defaults
		if eventinfo and eventinfo.pk:
			eventscheduleform.instance = eventinfo
			eventscheduleform.save()
			company_in    = eventinfo.schedule.filter(type="company_in").order_by('date').first()
			exhibitor_in  = eventinfo.schedule.filter(type="exhibitor_in").order_by('date').first()
			exhibitor_out = eventinfo.schedule.filter(type="exhibitor_out").order_by('date').first()
			# if not set, auto sets advance ship date, direct ship date, discount deadline date.
			
			previous_service_kit = eventinfo.service_kit
			# set advance ship date if non set by user.
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


		# add price levels
		eventinfo.price_levels.clear()
		for x in pricelevelform.cleaned_data.values():
			if x:
				# this may faile.
				eventinfo.price_levels.add(*x)

		# create a new ServiceKit obj (container for forms)
		# a new ServiceKit object is created each time a form is saved.
		servicekit = ServiceKit.objects.create(title=str(eventinfo.event_name))
		
		# Add ServiceKitForm to ServiceKit
		# if we are resaving the service kit, load the previous service kit and get its default forms
		if previous_service_kit and not form_version_changed:
			servicekitforms['default_forms'] = previous_service_kit.forms.filter(level__type__title='Default')
		# else add the default forms defined by the servicekitlevel "default_items"
		else:
			# first time saving form apply the default items
			servicekitforms['default_forms'] = ServiceKitForm.objects.filter(level__title="default_items", form_version=form_version)
		servicekit.forms.add(*servicekitforms['default_forms'])

		for form in form_list:
			# Add Service Kit Forms
			if type(form) == ServiceSelectionForm:
				pks = form.get_servicekitforms_pks()
				servicekitforms['servicekitforms'] = ServiceKitForm.objects.filter(pk__in=pks).order_by('level__type')
				servicekit.forms.add(*servicekitforms['servicekitforms'])
			# Add Additional Forms
			if type(form) == AdditionalFormsFormset:
				pks = []
				for x in form.cleaned_data:
					if x.get('form') and x.get('form') != 'None' and not x.get(u'DELETE'):
						pks.append(x.get('form'))
				servicekitforms['additionalforms'] = ServiceKitForm.objects.filter(pk__in=pks)
				servicekit.forms.add(*servicekitforms['additionalforms'])
		
		# Save the new ServiceKit to EventInfo
		servicekit.save()
		eventinfo.service_kit = servicekit
		
		# cache values:
		eventinfo._update_event_dates()
		eventinfo.save()

		# apply default form order only if new...
		# if not is_edit:
		eventinfo.service_kit.forms = sort_servicekit(eventinfo, default_order=previous_service_kit)
		# create a directory for the Event if non exists
		if not eventinfo.output_dir:			
			create_directory(eventinfo, rebuild=True)
		
		messages.success(self.request, 'Service Kit (%s) Saved.' % eventinfo)

		# Clear the FormWizard's session
		self.instance_dict = None
		self.storage.reset()

		# return HttpResponseRedirect(reverse('admin:kitcreate_eventinfo_change', args=(eventinfo.pk,)))		
		return HttpResponseRedirect(reverse('servicekit_complete', kwargs={'pk':eventinfo.pk}))

def fix_broken_servicekit(request, eventinfo_pk, servicekit_pk):
	eventinfo = EventInfo.objects.get(pk=eventinfo_pk)
	servicekit = ServiceKit.objects.get(pk=servicekit_pk)
	eventinfo.service_kit = servicekit
	eventinfo.save()
	messages.success(request, "Service Kit (%s's) information restored." % (eventinfo))	
	return HttpResponseRedirect(reverse('servicekit_complete', args=(eventinfo_pk,)))

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

from background_task.models import Task
def check_for_tasks(request, eventinfo):	
	for task in Task.objects.filter(queue='create-servicekit-queue'):
		if task.creator and task.creator.pk == eventinfo.pk:
			view_task_url = reverse('create_service_kit_queue', kwargs={"eventinfo_pk":eventinfo.pk, "task_pk":task.pk})
			messages.info(request, "%s's ServiceKit is queued for creation. Task created by %s. <a href=\"%s\">(task: #%s)</a>" 
				% (eventinfo, request.user.email, view_task_url, task.pk))

def wizard_complete(request, pk):
	"""The complete/review page once a service kit is finished"""
	eventinfo = EventInfo.objects.get(pk=pk)
	# clear the formwizard, just incase it is saved.
	# wizard_service_kit_wizard2
	if request.session.get('wizard_service_kit_wizard2'):
		del request.session['wizard_service_kit_wizard2']

	if not eventinfo.service_kit:
		price_level_url = reverse('edit_kit_pricelevel', kwargs={"pk":eventinfo.pk})
		messages.warning(request, "Service Levels and forms must be selecte before a kit can be created. <a href=\"%s\">Click here to get started.</a>" % price_level_url)
		# sk_list = ServiceKit.objects.filter(title=str(eventinfo.event_name))
		# if sk_list:
		# 	html = ("".join(["<li><a href=\"%s\">%s</a></li>" % 
		# 		(reverse('fix_broken_servicekit', kwargs={"eventinfo_pk":eventinfo.pk, "servicekit_pk":x.pk}), x.title) for x in sk_list]))
		# 	messages.warning(request, mark_safe('There was an error fetching the service kit forms for this event. <br>Either re-enter the information, or click one of the kits found by the application to reattach it to the Event. <ul>%s</ul>' % html))
		# else:
		# 	messages.warning(request, "There was an error fetching the servie kit for this event. Please re-enter hte information.")
	
	# check if user wants to edit/reorder service kit forms	
	if request.POST and request.POST.get('reorder'):
		sort_sk_form = SortSkFormsForm(eventinfo, request.POST, instance=eventinfo.service_kit)
		if sort_sk_form.is_valid():
			sort_sk_form.save()
			messages.success(request, 'Service Kit (%s) Form\'s Order Saved.' % eventinfo)
	
	extra_field_values = get_form_field_values(eventinfo)

	sort_sk_form = SortSkFormsForm(eventinfo, instance=eventinfo.service_kit)

	check_for_tasks(request, eventinfo)

	if not eventinfo.is_editable:
		messages.info(request, '%s is %s, and locked for editing' % (eventinfo, eventinfo.get_servicekitstatus_display()))

	context = {}
	context['servicekits'] = ServiceKit.objects.filter(title=str(eventinfo.event_name))
	context['active_service_kit'] = eventinfo.service_kit
	context['status_message_form'] = StatusMessageForm(initial={'status_type':'status'})
	context['is_editable'] = eventinfo.is_editable
	context['internal_note_form'] = InternalNoteForm(instance=eventinfo)
	context['status_form']  = ServicekitstatusForm(instance=eventinfo)
	context['storefrontstatus_form'] = EventInfoStorefrontStatusForm(instance=eventinfo)
	context['eventinfo']    = eventinfo
	context['sort_sk_form'] = sort_sk_form
	context['extra_field_values'] = extra_field_values
	context['pdf_exists']   = os.path.exists(eventinfo.get_pdf())

	# Some problems with this at the moment
	# This doesn't 100% time the pricing in the form with the boomer pricelist
	# for instances if old form without of date pricing is used
	# then there is a disconnect... eventually need to render the forms on the fly.
	# boomer_pricelists = set()
	# for form in eventinfo.service_kit.forms.all():
	# 	pricelist_link = form.pricelist_links.first()
	# 	if pricelist_link and pricelist_link.pricelist:
	# 		boomer_pricelists.add(pricelist_link.pricelist.get_export_url())
	# context['boomer_pricelists'] = boomer_pricelists
	
	# return render(request, 'kitcreate/done.html', context)	
	return render(request, 'kitcreate/v2/kit-review.html', context)	

wizard_complete = staff_member_required(wizard_complete)

# Collection of views to handle updating fields on the EventInfo
class InternalNoteUpdateView(StaffMemberRequiredMixin, UpdateView):
	""" 
	View to update EventInfo.internal_note
	"""
	model = EventInfo
	fields = ['internal_note',]
	def get_success_url(self):
		messages.success(self.request, '%s Internal Note Updated' % (self.object))
		return reverse('servicekit_complete', kwargs={'pk':self.object.pk})

def update_kit_status(request, pk):
	"""View to handle updating the service kits status"""

	eventinfo = EventInfo.objects.get(pk=pk)
	redirect_url = reverse('servicekit_complete', args=(pk,))	
	if request.POST and request.POST.get('status'):		
		status_form = EventInfoStatusForm(request.POST, instance=eventinfo)
		if status_form.is_valid():
			status_value = status_form.cleaned_data.get('status')
			notify       = status_form.cleaned_data.get('notify')
			status_form.save()
			messages.success(request, '%s status changed: %s' % (eventinfo, status_value))		
			if notify and notify != 'false':
				try:
					receivers = create_status_notification(eventinfo, status_value)
					if not receivers:
						messages.warning(request, 'The notification was not sent.')
					else:
						emails = ', '.join(receivers)
						messages.info(request, 'Notificaion sent to %s' % (emails))
				except Exception, e:
					messages.error(request, 'An error was encountered sending notification. %s' % (str(e)))
					logger.error(e)	
	
	redirect = request.POST.get('redirect')
	if redirect:
		redirect_url = reverse(redirect)


	return HttpResponseRedirect(redirect_url)

class StorefrontstatusListView(StaffMemberRequiredMixin, ListView):
	"""
	View to display EventInfo.storefrontstatus's
	Storefront == GoShow (SER's exhibitor ecommerce site)	
	"""
	model = EventInfo
	paginate_by = 50
	template_name = "kitcreate/v2/storefrontstatus_list.html"

	def get_queryset(self, *args, **kwargs):		
		qs =  super(StorefrontstatusListView, self).get_queryset(*args, **kwargs)
		storefront_status_value = self.request.GET.get('storefrontstatus', None)
		servicekitstatus_value = self.request.GET.get('servicekitstatus', None)
		search_val = self.request.GET.get('search', None)

		if servicekitstatus_value and storefront_status_value:
			qs = qs.filter(servicekitstatus=servicekitstatus_value, storefrontstatus=storefront_status_value)
		else:
			if servicekitstatus_value:
				qs = qs.filter(servicekitstatus=servicekitstatus_value)

			if storefront_status_value:
				qs = qs.filter(storefrontstatus=storefront_status_value)
		
		if search_val:
			qs = qs.filter(event_name__description__icontains=search_val)
			
		return qs.order_by('pk').reverse()		

	def get_context_data(self, **kwargs):
		# Call the base implementation first to get a context
		context = super(StorefrontstatusListView, self).get_context_data(**kwargs)
		# Add in a QuerySet of all the books
		context['storefrontstatus_form'] = EventInfoStorefrontStatusForm(self.request.GET)
		context['storefrontstatus_form'].fields['storefrontstatus'].choices = [('', '----')] + context['storefrontstatus_form'].fields['storefrontstatus'].choices
		
		# context['status_form'] = EventInfoStatusForm(self.request.GET)
		# context['status_form'].fields['status'].choices = [('', '----')] + context['status_form'].fields['status'].choices

		context['status_form'] = ServicekitstatusForm(self.request.GET)
		context['status_form'].fields['servicekitstatus'].choices = [('', '----')] + context['status_form'].fields['servicekitstatus'].choices
		context['search_val'] = self.request.GET.get('search', "")
		return context

from kitcreate.utils.modelsearch import get_query
from kitcreate.forms import Servicekits_FilterForm
from kitcreate.utils.queryset_to_xls import download_workbook
class ServicekitstatusListView(StaffMemberRequiredMixin, ListView):
	"""
	View to display EventInfo.servicekitstatus's
	"""
	model = EventInfo
	paginate_by = 50
	template_name = "kitcreate/v2/servicekitstatus_list.html"
	search_fields = ["event_name__description", "event_name__event_code", "event_mgmt__title", "facility__title", "salesperson__title"]
	
	def get_queryset(self, *args, **kwargs):				
		qs               =  super(ServicekitstatusListView, self).get_queryset(*args, **kwargs)		
		filter_form = Servicekits_FilterForm(self.request.GET)
		filter_form.is_valid()
		servicekitstatus = filter_form.cleaned_data.get('servicekitstatus', None)
		search_text      = filter_form.cleaned_data.get('search_text', None)
		start_date       = filter_form.cleaned_data.get('start_date', None)
		end_date         = filter_form.cleaned_data.get('end_date', None)
		order_by         = filter_form.cleaned_data.get('order_by', 'event_start_date')

		if isinstance(start_date, str):
			start_date = datetime.strptime(start_date, "%Y-%m-%d")
		if isinstance(start_date, str):
			end_date = datetime.strptime(end_date, "%Y-%m-%d")

		if start_date and end_date:
			# qs = EventInfo.objects.filter_by_daterange(start_date=start_date,end_date=end_date)
			qs = EventInfo.objects.filter(event_start_date__range=(start_date,end_date))
					
		if start_date and not end_date:
			qs = EventInfo.objects.filter(event_start_date__gte=start_date)
		
		if end_date and not start_date:
			qs = EventInfo.objects.filter(event_start_date__lte=end_date)

		if servicekitstatus:
			qs = qs.filter(servicekitstatus__in=servicekitstatus)

		if search_text:
			query = get_query(search_text, self.search_fields)
			if query:
				qs = qs.filter(query)


		if not EventInfo.SERVICEKITSTATUS.expired in servicekitstatus:
			qs = qs.filter(active=True)
		
		if order_by:
			return qs.order_by(order_by)
		return qs

	def get_context_data(self, **kwargs):
		# Call the base implementation first to get a context
		context = super(ServicekitstatusListView, self).get_context_data(**kwargs)
		context['statusmessageform'] = StatusMessageForm(initial={'status_type':'servicekitstatus'})
		context['servicekits_filterform'] = Servicekits_FilterForm(self.request.GET)		
		context['servicekitstatus'] = self.request.GET.get('servicekitstatus', None)
		context['search_text']      = self.request.GET.get('search_text', '')		
		context['start_date']       = self.request.GET.get('start_date', None)
		context['end_date']         = self.request.GET.get('end_date', None)		
		return context

	# def get_full_path(self, *args, **kwargs):
	# 	uri = super(ServicekitstatusListView, self).get_full_path(*args,**kwargs)
	# 	return uri +"#filter-form"

	def get(self, request, *args, **kwargs):
		response = super(ServicekitstatusListView, self).get(request, *args, **kwargs)
		
		# HAXXOR 
		if request.GET.get('download'):
			qs = self.get_queryset()
			columns = [
				"event_name.event_code",
				"event_name.event_subcode",
				"event_mgmt.code",
				"facility.code",
				"salesperson",
				"ae_pulled",
				"given_to_ae",
				"completed_by_ae",
				"proofed_by_exhibitor_services",
				"sent_to_sm",
				"approved_goshow",
				"list_received",
				"published",			
			]

			return download_workbook(qs, columns, report_name="ServiceKit-Status-Report")
		
		return response

def send_status_message(request, pk):
	"""
	Send a message about an Event's status change.
	"""
	eventinfo = EventInfo.objects.get(pk=pk)
	if request.POST:		
		form = StatusMessageForm(request.POST)
		if form.is_valid():
			if form.cleaned_data.get('emails'):
				receivers = [x.email for x in User.objects.filter(pk__in=form.cleaned_data.get('emails'))]
			else:
				receivers = [x.email for x in User.objects.filter(groups__pk=form.cleaned_data.get('group'))]
			message = form.cleaned_data['message']				
			status  = form.cleaned_data['status']
			status_type = form.cleaned_data['status_type']
			if status_type == 'status':
				subject = 'Kit Status Changed for %s' % (eventinfo.event_name)
				eventinfo.status = status
				eventinfo.save()
				messages.success(request, '%s status changed: %s' % (eventinfo, status))
			elif status_type == 'storefrontstatus':
				subject = '%s Storefront Status' % (eventinfo.event_name)
				eventinfo.storefrontstatus = status
				eventinfo.save()
				messages.success(request, '%s storefront setup status changed: %s' % (eventinfo, status))
			elif hasattr(eventinfo, status_type):
				setattr(eventinfo, status_type, status)
				if status == EventInfo.SERVICEKITSTATUS.expired:
					eventinfo.active = False
				eventinfo.save()				
				eventinfo.save()
				subject = 'ServiceKit %s Status Changed' % (eventinfo.event_name)
				# messages.success(request, '%s status changed: %s' % (eventinfo, status))
				messages.success(request, '%s servicekit status changed: %s' % (eventinfo, eventinfo.get_servicekitstatus_display()))
			context = {'eventinfo': eventinfo, 'message':message, 'status':status, 'status_type': status_type}
			
			try:
				notification_generic(eventinfo, subject, message, receivers, context=context)				
				messages.info(request, 'Notificaion sent to %s' % (', '.join(receivers)))
			except Exception, e:
				messages.error(request, 'An error was encountered sending notification. %s' % (str(e)))
				logger.error(e)	
		else:
			errors = ' '.join('{}: {}'.format(key.upper(), ', '.join(val)) for key, val in form.errors.items())
			messages.error(request, 'Invalid form: %s' % errors)

	return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
send_status_message = staff_member_required(send_status_message)


def storefrontstatus_quickinfo(request, pk):
	"""
	Helper for entering ServiceKit data into GoShow.
	"""
	eventinfo = EventInfo.objects.get(pk=pk)
	context = {}
	context['no_direct_shipments'] = False
	material_handling_type = ServiceType.objects.filter(title="MaterialHandling").first()
	if material_handling_type and eventinfo.service_kit:
		for form in eventinfo.service_kit.forms.filter(level__type=material_handling_type):
			if 'adv' in form.title.lower():
				context['no_direct_shipments'] = True	
				break
	context['storefrontstatus_form'] = EventInfoStorefrontStatusForm(instance=eventinfo)
	context['sk'] = ServiceKitContext(eventinfo).__dict__
	context['eventdata_json'] = GSContext(eventinfo).to_json()
	context['eventinfo'] = eventinfo
	return render(request, "kitcreate/storefront-quick-info.html", context)

storefrontstatus_quickinfo = staff_member_required(storefrontstatus_quickinfo)

def storefrontstatus_update(request, pk):
	"""View to handle storefront status updates..."""
	eventinfo = EventInfo.objects.get(pk=pk)
	
	if request.POST and request.POST.get('storefrontstatus'):
		status_form = EventInfoStorefrontStatusForm(request.POST, instance=eventinfo)		
		if status_form.is_valid():
			status_value = status_form.cleaned_data.get('storefrontstatus')
			notify       = status_form.cleaned_data.get('notify2')
			status_form.save()
			messages.success(request, '%s storefront setup status changed: %s' % (eventinfo, status_value))
			if notify and notify != 'false':
				try:
					receivers = create_storefrontstatus_notification(eventinfo, status_value)
					if not receivers:
						messages.warning(request, 'The notification was not sent.')
					else:
						emails = ', '.join(receivers)
						messages.info(request, 'Notificaion sent to %s' % (emails))
				except Exception, e:
					messages.error(request, 'An error was encountered sending notification. %s' % (str(e)))
					logger.error(e)	
	
	return HttpResponseRedirect(reverse('servicekit_complete', args=(pk,)))

storefrontstatus_update = staff_member_required(storefrontstatus_update)

def servicekitstatus_update(request, pk):
	"""View to handle storefront status updates..."""	
	eventinfo         = EventInfo.objects.get(pk=pk)
	search_query      = ''
	status_value      = None
	send_notification = False
	if request.POST and request.POST.get('servicekitstatus'):
		status_form = ServicekitstatusForm(request.POST, instance=eventinfo)		
		if status_form.is_valid():
			status_value = status_form.cleaned_data.get('servicekitstatus')
			search_query = status_form.cleaned_data.get('search_query')
			send_notification = status_form.cleaned_data.get('send_notification')
			
			if status_value == EventInfo.SERVICEKITSTATUS.expired:
				eventinfo.active = False
				eventinfo.save()

			status_form.save()			
			messages.success(request, '%s servicekit status changed: %s' % (eventinfo, eventinfo.get_servicekitstatus_display()))
			if send_notification and send_notification != 'false':
				try:
					# EventCoordinators, CustomerService
					to = [x.email for x in User.objects.filter(groups__name='EventCoordinators')]
					subject = 'ServiceKit %s Status Changed' % (eventinfo.event_name)
					context = {
						'eventinfo': eventinfo, 
						'status':eventinfo.get_servicekitstatus_display(), 						
					}
					receivers = notification_generic(eventinfo, subject, '', to, context=context)
					if not receivers:
						messages.warning(request, 'The notification was not sent.')
					else:
						emails = ', '.join(receivers)
						messages.info(request, 'Notificaion sent to %s' % (emails))
				except Exception, e:
					messages.error(request, 'An error was encountered sending notification. %s' % (str(e)))
					logger.error(e)	
	
	# return HttpResponseRedirect(reverse('servicekit_complete', args=(pk,)))	
	
	if '_continue' in request.POST:
		return HttpResponseRedirect(reverse('servicekit_complete', args=(eventinfo.pk,)))	
	
	if search_query:
		search_query = "?%s" % (search_query)
	elif request.POST.get('search_query'):
		search_query = "?%s" % (request.POST.get('search_query'))

	return HttpResponseRedirect("%s%s" % (reverse('serviceskitstatus_listview'), search_query))

servicekitstatus_update = staff_member_required(servicekitstatus_update)

# Views to handle uploading ServiceKitForm
class ServiceKitFormListView(StaffMemberRequiredMixin, ListView):
	"""
	View to list all available service kit forms.
	"""
	model = ServiceKitForm
	paginate_by = 50
	template_name = 'kitcreate/v2/servicekitform_list.html'

	def get_queryset(self, *args, **kwargs):
		search_val = self.request.GET.get('search', None)
		is_popup = self.request.GET.get('_popup') or False
		# if not a popup and no searching show all the forms.
		if not search_val and not is_popup:
			return ServiceKitForm.objects.all().order_by('title')
		# if is a popup and search value, show only forms without a price level
		if not search_val:
			return ServiceKitForm.objects.filter(level=None).order_by('title')			

		new_context = ServiceKitForm.objects.filter(
			title__icontains=search_val
		)
		return new_context.order_by('pk').reverse()

	def get_context_data(self, **kwargs):
		context = super(ServiceKitFormListView, self).get_context_data(**kwargs)
		context['search'] = self.request.GET.get('search', '')
		context['is_popup'] = bool(self.request.GET.get('_popup'))
		return context	

def handle_uploaded_file(f, filepath):
	with open(filepath, 'wb+') as destination:
		for chunk in f.chunks():
			destination.write(chunk)

def form_exists(filepath):
	"""
	Check if a file exists as a ServiceKitForm
	"""
	return ServiceKitForm.objects.filter(document__icontains=filepath).exists()

def file_upload(request, pk=None):
	"""
	Quick method to creating a ServiceKitForm
	Forms are upload to uploads/documents/forms/misc/
	"""
	servicekitform = None
	base_dir = os.path.join(site.storage.location, site.directory)
	misc_dir = os.path.join(base_dir, 'documents', 'forms', 'misc' )
	is_popup = request.GET.get('_popup', False)	
	is_edit  = bool(pk)
	if pk:
		servicekitform = ServiceKitForm.objects.get(pk=pk)

	form = UploadServiceKitForm(request.POST, request.FILES, instance=servicekitform)
	if request.method == 'POST':		
		if form.is_valid():				
			# get the file path
			_file = request.FILES.get('file')
			if _file:
				filename = _file.name
				full_filename = ("%s__%s" % (datetime.now().strftime("%Y%m%d-%H%M%S"), filename))
				full_path = os.path.join(misc_dir, full_filename)

				# ServiceKitForm.objects.filter(document__icontains='')
				# if no title for the servicekit form provide use the file name
				if request.POST.get('title'):
					form_title = request.POST.get('title')
				else:
					form_title, ext = os.path.splitext(filename)
				
				# save the file to the misc folder.
				handle_uploaded_file(request.FILES['file'], full_path)
				servicekitform = form.save()			
				servicekitform.title = form_title
				servicekitform.document = FileObject(os.path.join(misc_dir, full_filename))
				servicekitform.save()
			else:
				servicekitform = form.save()
			
			popup_response_data = {
				'value': six.text_type(servicekitform.pk),
				'obj': six.text_type(servicekitform)
			}

			if _file and not is_edit:
				messages.success(request, "%s successfully added" % filename)			
			elif not is_edit:
				messages.success(request, "%s successfully added" % servicekitform)
			else:
				messages.success(request, "%s successfully changed" % servicekitform)
				# popup_response_data['action'] = "change"
			
			if is_popup:
				return SimpleTemplateResponse('admin/popup_response.html', {
						"popup_response_data": json.dumps(popup_response_data)
						# 'value': servicekitform.pk,
						# 'obj': servicekitform
					})							
			return HttpResponseRedirect(reverse("file_edit_form",kwargs={'pk':servicekitform.pk}))

	form = UploadServiceKitForm(instance=servicekitform)
	return render(request, 'kitcreate/v2/servicekitform-upload.html', {
		'form': form, 
		'is_popup':is_popup, 
		'is_edit': is_edit,	
		'servicekitform': servicekitform
		}
	)
file_upload = staff_member_required(file_upload)
# Views and helper functions to create, download and archive ServiceKit PDF

def download_service_kit(request, pk):
	"""Download a PDF Service Kit (created from create_service_kit)"""
	eventinfo = EventInfo.objects.get(pk=pk)
	filename    = eventinfo.get_output_filename()
	output_path = eventinfo.get_pdf()
	if not os.path.exists(output_path):
		messages.error(request, 'File does not exists: %s' % output_path)
		return HttpResponseRedirect(reverse('servicekit_complete', args=(pk,)))		
	data = open(output_path, 'r').read()
	response = HttpResponse(data, content_type='application/pdf')
	response['Content-Disposition'] = 'attachment; filename=%s' % filename
	return response

download_service_kit = staff_member_required(download_service_kit)


# FileResponse(open('foobar.pdf', 'rb'), content_type='application/pdf')
@never_cache
def view_service_kit(request, pk):
	"""Download a PDF Service Kit (created from create_service_kit)"""
	eventinfo = EventInfo.objects.get(pk=pk)
	filename    = eventinfo.get_output_filename()
	output_path = eventinfo.get_pdf()
	if not os.path.exists(output_path):
		messages.error(request, 'File does not exists: %s' % output_path)
		return HttpResponseRedirect(reverse('servicekit_complete', args=(pk,)))		
	return FileResponse(open(output_path, 'rb'), content_type='application/pdf')


view_service_kit = staff_member_required(view_service_kit)

def quick_export(request, pk):
	"""
	View to export forms in an Event without creating a new service kit.
	"""
	context = {}
	eventinfo = EventInfo.objects.get(pk=pk)

	filename    = 'e-%s' % eventinfo.get_output_filename(file_type='pdf')
	output_path = os.path.join(eventinfo.output_dir, filename)
	previous_export = None
	if os.path.exists(output_path):
		previous_export = "/uploads/kits/%s-%s/%s" % (eventinfo.pk, eventinfo._filename, filename)

	if request.POST and request.POST.get('export'):
		form = SortSkFormsForm(eventinfo, request.POST, instance=eventinfo.service_kit)
		if form.is_valid():
			try:
				render_forms(eventinfo)
			except Exception, e:
				messages.error(request, mark_safe('An error was encountered processing service kit. %s' % (e)))
				logger.error('Eventinfo object: %s.  Error: %s' % (eventinfo.pk, e))
				return HttpResponseRedirect(reverse('servicekit_complete', args=(pk,)))

			# filename = datetime.now().strftime("%Y%m%d-%H%M%S")
			filelisting = list(FileListing(eventinfo.output_dir).listing())
			forms = []
			for _form in form.cleaned_data['forms']:
				_full_path = get_merged_form_path(eventinfo, _form)
				_filename = os.path.basename(_full_path)
				if _filename in filelisting:
					forms.append(_full_path)
			if not forms:
				messages.info(request, 'There were no forms found for this Service Kit')
			else:
				try:
					forms_to_pdf(forms, output_path)
					download_url = "/uploads/kits/%s-%s/%s" % (eventinfo.pk, eventinfo._filename, filename)
					messages.success(request, mark_safe('Your files were successfully created. <a href="%s">Click here to download pdf</a>'% (download_url)))
					return HttpResponseRedirect(download_url)
				except Exception, e:
					messages.error(request, 'An error was encountered processing service kit. %s' % (str(e)))
					logger.error(e)

			
	
	form = SortSkFormsForm(eventinfo, instance=eventinfo.service_kit)
	context['form'] = form
	context['eventinfo'] = eventinfo
	context['previous_export'] = previous_export
	return render(request, 'kitcreate/quick-export.html', context)
quick_export = staff_member_required(quick_export)


def create_service_kit(request, pk):
	""" 
	Render EventInfo data into Service Kit .docx forms 
	Calls to CloudConvert to merge forms into a PDF 
	"""
	from kitcreate.tasks import create_servicekit_task
	eventinfo = EventInfo.objects.get(pk=pk)
	url       = reverse('servicekit_complete', args=(pk,))
	overwrite = False
	# update the forms order on save.
	# struggle with this because there are multiple indepent forms in the html
	# so one way data bind the name="forms" but adds javascript too...
	# and can make hte ui a little unpredictable. idk.
	if request.POST and request.POST.get('forms'):
		sort_sk_form = SortSkFormsForm(eventinfo, request.POST, instance=eventinfo.service_kit)
		if sort_sk_form.is_valid():
			sort_sk_form.save()
			messages.success(request, 'Service Kit (%s) Form\'s Order Saved.' % eventinfo)

	if not request.POST and not request.POST.has_key('create'): 
		return HttpResponseRedirect(url)
	
	# if overwrite is true, recreate directory and it's forms.
	overwrite = request.POST.get('overwrite', False)	
	
	user = request.user
	task = create_servicekit_task(eventinfo.pk, user.pk, overwrite=overwrite, creator=eventinfo)
	view_task_url = reverse('create_service_kit_queue', kwargs={"eventinfo_pk":eventinfo.pk, "task_pk":task.pk})
	messages.info(request, "%s's ServiceKit is now queued for creation. You will receive an email (at %s) once the kit is ready. <a href=\"%s\">(task: #%s)</a>" 
		% (eventinfo, user.email, view_task_url, task.pk))
	return HttpResponseRedirect(url)

create_service_kit = staff_member_required(create_service_kit)


def clean_eventinfo_dir(folder):	
	"""
	Deletes all files in an Event's folder
	:folder <string> path to folder to clean.
	"""
	# folder = eventinfo.output_dir
	for the_file in os.listdir(folder):
		file_path = os.path.join(folder, the_file)
		try:
			if os.path.isfile(file_path):
				os.unlink(file_path)
			#elif os.path.isdir(file_path): shutil.rmtree(file_path)
		except Exception as e:
			raise e

# shutil.copyfile(src, dst)
def create_directory(eventinfo, rebuild=True):
	"""Create the EventInfo directory where rendered forms will be stored"""
	# if rebuild is false and we already have an existing directory, don't rebuild
	if rebuild == False and (eventinfo.output_dir and os.path.exists(eventinfo.output_dir or '')):
		return eventinfo.output_dir
	# rebuild if the diretory if it does exists and requested
	if rebuild and (eventinfo.output_dir and os.path.exists(eventinfo.output_dir or '')):		
		clean_eventinfo_dir(eventinfo.output_dir)

	output_dir = None
	new_directory_name = "%s-%s" % (eventinfo.pk, eventinfo._filename)
	output_dir = os.path.abspath(os.path.join(site.storage.location, site.directory, 'kits', new_directory_name))
	if not os.path.exists(output_dir):
		os.makedirs(output_dir)
		# os.makedirs(os.path.join(output_dir, 'pdfs'))
	eventinfo.output_dir = output_dir
	eventinfo.save()
	return output_dir

def archive_servicekit_forms(eventinfo):
	"""
	Archive an Event's forms.
	"""
	# files_to_archive = []
	# Tracking down a weird error, putting catch all exceptions wherever I can...
	try:
		if not eventinfo.output_dir:
			return None
		
		archive_dir = os.path.join(eventinfo.output_dir, 'archive')
		
		if not os.path.exists(archive_dir):
			os.makedirs(archive_dir)

		archive_filename = "%s.zip" % (datetime.now().strftime("%Y%m%d-%H%M%S"))
		
		zf = zipfile.ZipFile(os.path.join(archive_dir, archive_filename), mode="w", allowZip64=False, compression=zipfile.ZIP_DEFLATED)
		for the_file in os.listdir(eventinfo.output_dir):
			filename = os.path.basename(the_file)
			zf.write(os.path.join(eventinfo.output_dir, the_file), arcname=filename)		
			# zf.write(os.path.join(folder, the_file))
		zf.close()				
		return archive_filename
	except Exception, e:
		raise Exception('Error archiving %s. Error Message: ' % (eventinfo, e))
	


from threading import Thread
def postpone(function):
  def decorator(*args, **kwargs):
	t = Thread(target = function, args=args, kwargs=kwargs)
	t.daemon = True
	t.start()
  return decorator

@postpone
def background_archive_servicekit_forms(eventinfo):
	"""Puts the archiving forms process in the background"""
	archive_servicekit_forms(eventinfo)

def create_archive(filelist):
	""" 
	Create a zip archive of the files for download
	"""
	# event = EventInfo.objects.get(pk=17)
	# master = ServiceKitForm.objects.last()
	# cover = ServiceKitForm.objects.get(pk=9)
	# filelist = [x.document.path_full for x in [master, cover]]
	# [filelist.append(x.document.path_full)for x in event.service_kit.forms.all()]
	import tempfile
	import zipfile

	with tempfile.SpooledTemporaryFile() as tmp:
		with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as archive:
			arcname = './docs/'
			for x in filelist:
				filename = os.path.basename(x)
				archive.write(x, arcname=os.path.join(arcname, filename))

		# Reset file pointer
		tmp.seek(0)

		# Write file data to response
		return HttpResponse(tmp.read(), content_type='application/x-zip-compressed')

def download_archive_pdf(eventinfo, archive_filename):
	"""
	Download an Event's archive.
	"""
	archive = zipfile.ZipFile(os.path.join(eventinfo.get_archive_path(), archive_filename), 'r')
	for x in archive.filelist:
		if x.filename == eventinfo.get_output_filename():
			derp = archive.open(x)
			data = derp.read()
			response = HttpResponse(data, content_type='application/pdf')
			response['Content-Disposition'] = 'attachment; filename=%s' % eventinfo.get_output_filename()
			return response

def view_kit_archive(request, pk):
	""" 
	View a list of archives available for download.
	"""
	eventinfo = EventInfo.objects.get(pk=pk)
	
	if request.GET.get('archive_filename'):
		response = download_archive_pdf(eventinfo, request.GET.get('archive_filename'))
		if response:
			return response

	archive_path = eventinfo.get_archive_path()
	filelisting = FileListing(archive_path)
	context = {}
	files = []
	for f in filelisting.listing():
		_obj = {}
		archive_date = datetime.strptime(f, "%Y%m%d-%H%M%S.zip")
		_obj['archive_date'] = archive_date
		_obj['archive_date_verbose'] = archive_date.strftime('%A %B %d, %Y')
		# http://kits.ser.local:8111/uploads/kits/53-HARTNEWOMEEXPO-20170610/archive/20170501-132847.zip
		_obj['url'] = '/uploads/kits/%s/archive/%s' % (eventinfo.filebrowser_dir_name, f)
		_obj['filename'] = f
		files.append(_obj)	
	context['archive'] = sorted(files, key=lambda x: x['archive_date'])
	context['eventinfo'] = eventinfo
	return render(request, 'kitcreate/archive_list.html', context)
view_kit_archive = staff_member_required(view_kit_archive)

def copy_to_network_drive(request, pk):
	"""
	Copy service kit PDF to network drive.
	"""
	messages.warrning(request, 'Copy To Network Drive is depreciated')
	logger.error(Exception("Copy To Network Drive is depreciated"))	
	return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))	
	
	eventinfo = EventInfo.objects.get(pk=pk)
	if os.path.exists(eventinfo.get_pdf()) and eventinfo.status in ['approved', 'published']:
		try:
			_copy_to_network_drive(eventinfo)
			messages.success(request, '%s copied to network drive' % (eventinfo.get_output_filename()))
		except Exception, e:
			messages.error(request, 'Could not copy file to network drive: %s' % (e))
			logger.error(e)			
	else:
		messages.info(request, 'Could not copy file at this time')

	return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))	

copy_to_network_drive = staff_member_required(copy_to_network_drive)

def _copy_to_network_drive(eventinfo):
	"""
	Copies the pdf to network drive defined in settings.NETSHARE_PDF_REPO
	"""
	pdf_repo = getattr(settings,'NETSHARE_PDF_REPO', None)
	
	if not pdf_repo: 
		raise Exception('Django App setting "NETSHARE_PDF_REPO" is not defined')
	if not os.path.exists(pdf_repo):
		raise Exception('NETSHARE_PDF_REPO path "%s" does not exist' % pdf_repo)
	
	filepath_a = os.path.join(eventinfo.output_dir, eventinfo.get_output_filename())
	filepath_b = os.path.join(pdf_repo, eventinfo.get_output_filename())
	copyfile(filepath_a, filepath_b)
	return True
		

def create_output_filename(eventinfo, filetype):
	"""Helper method to create the finished Service Kit file name"""
	return '%s.%s' % (str(eventinfo.event_name).translate(None, ''.join(['/', ' '])),filetype)

def get_pricelist_prices(prices, service_type):

	def context_labor(queryset):
		results = {}
		for x in queryset:
			results["%s__st__adv" % x.product.product_id] = "%.2f" % (x.advance_price)
			results["%s__st__std" % x.product.product_id] = "%.2f" % (x.standard_price)
			results["%s__ot__adv" % x.product.product_id] = "%.2f" % (1.50 * x.advance_price)
			results["%s__ot__std" % x.product.product_id] = "%.2f" % (1.50 * x.standard_price)
		return results


	def context_mh(queryset):
		results = {}
		for x in queryset:
			results["%s__stst__std" % (x.product.product_id)] = "%.2f" % (1.00 * x.advance_price)
			results["%s__stot__std" % (x.product.product_id)] = "%.2f" % (1.30 * x.advance_price)
			results["%s__otot__std" % (x.product.product_id)] = "%.2f" % (1.60 * x.advance_price)
			results["%s__stst__sh" % (x.product.product_id)] = "%.2f" % (1.30 * x.advance_price)
			results["%s__stot__sh" % (x.product.product_id)] = "%.2f" % (1.60 * x.advance_price)
			results["%s__otot__sh" % (x.product.product_id)] = "%.2f" % (1.90 * x.advance_price)	
		return results

	def context_furniture(queryset):
		results = {}
		for x in queryset:
			results["%s__adv" % x.product.product_id] = "%.2f" % (x.advance_price)
			results["%s__std" % x.product.product_id] = "%.2f" % (x.standard_price)
		return results
	
	form_context_func = {
		'Furniture': context_furniture,
		'Labor': context_labor,
		'MaterialHandling': context_mh
	}
	return form_context_func.get(service_type, context_furniture)(prices)

import hashlib
def get_merged_form_path(eventinfo, form):	
	hasher = hashlib.sha1(form.title)
	filename_hash = str(hasher.hexdigest()[:5])
	return os.path.join(eventinfo.output_dir, "%s%s" % (filename_hash, form.document.filename))

def render_forms(eventinfo):
	"""
	Renders the context data to the forms 
	OR
	Performs mail merge. Merging EventInfo data and the .docx forms
	"""
	context = ServiceKitContext(eventinfo).__dict__
	# perform the merge
	
	
	docs = []

	if not eventinfo.service_kit:
		return docs
	
	for form in eventinfo.service_kit.forms.all():
		# logger.info("Can we add page numbers here? Sequenctial page numbers may not work as a service kit form can have multiple pages. How about instead of page numbers, use \"Kit Section: #1\"?")
		# can we add page numbers here?
		if not form.document or not form.has_form:
			form_upload_link = reverse('file_edit_form', kwargs={'pk':form.pk})
			raise Exception('The Serivce Kit Form Object "%s" has no file attached. <a href="%s">Click here to upload the correct file to the object.</a>' % 
							(form.title, form_upload_link))
		if 'docx' not in form.document.extension:
			# copyfile(form.document.path_full, os.path.join(eventinfo.output_dir, form.document.filename))
			copyfile(form.document.path_full, get_merged_form_path(eventinfo, form))
			continue

		# What we're saying.
		# Check the price level on the form.
		# If that price level is mapped to a PriceLevel 
		# Get the prices and service type for that form to create the context for the form data.
		# Templates, man.
		
		# What about when weh ave labor 125 and forklift 152, how does the data work...
		# how do we say forklift is for 152 and labor is 125?
		# import ipdb; ipdb.set_trace()
		price_level = eventinfo.price_levels.filter(servicekitform=form).first()
		if price_level and hasattr(price_level, 'servicepricelistmap') and price_level.servicepricelistmap:
			price_list = price_level.servicepricelistmap.price_list
			service_type = price_level.type.title
			prices = price_list.prices.filter(price_tier="Default")
			pricelist_prices = get_pricelist_prices(prices, service_type)
			context.update(pricelist_prices)

		doc = MailMerge(form.document.path_full)		
		for key, value in context.items():
			# if context data is list, treat it as a table else it's normal field
			try:
				if type(value) == list:
					doc.merge_rows(key, value)
				else:
					preserve_breaks = key in ['booth_info', 'notes', 'internal_notes', 'note']
					doc.merge(preserve_breaks=preserve_breaks, **{key:value})
			except Exception, e:
				raise e
		
		# write the merged document to the kit's directory
		# doc.write(os.path.join(eventinfo.output_dir, form.document.filename))
		doc.write( get_merged_form_path(eventinfo, form) )
		docs.append(doc)
	return docs

def get_merged_forms(eventinfo):
	"""returns an ordered list of the rendered forms filepath"""
	# import ipdb; ipdb.set_trace()
	# filelisting = list(FileListing(eventinfo.output_dir).listing())
	results = []
	if not eventinfo.service_kit:
		return results
	for form in eventinfo.service_kit.forms.all():

		full_form_path = get_merged_form_path(eventinfo, form)
		# if os.path.basename(full_form_path) in filelisting:
		if os.path.exists(full_form_path):
			# results.append(os.path.join(eventinfo.output_dir, form.document.filename))
			results.append( full_form_path )
	return results

def get_form_field_values(eventinfo):
	""" 
	Gets forms with ServiceKitFields and their respetive ServiceKitFormFieldValue's
	:returns [
		{
			form_title: '', form_fields: [
				{form_label: '', 'field_value': ''},
			]
		},
	]
	"""
	results = []
	if not eventinfo.service_kit:
		return results
	for _servicekitform in eventinfo.service_kit.forms.filter(form_fields__isnull=False).distinct():
		_fields = []		
		for kitfieldvalue in ServiceKitFieldValue.objects.filter(kit=eventinfo.service_kit, field__form=_servicekitform):
			_fields.append({'field_label': kitfieldvalue.field.label, 'field_value':kitfieldvalue.value})		
		results.append({'form_title': _servicekitform.title,'form_fields': _fields})	
	return results	

# misc functions...
def select_form(request):
	"""
	Redirect users to type of form they select to create (servicekit, proposal, ect)
	"""

	form = SelectKitForm(request.POST or None)
	if request.POST and form.is_valid():
		option = form.cleaned_data.get('options')
		# if option.title == 'Service Kit':
		if option == 'servicekit':
			return HttpResponseRedirect(reverse("servicekit_wizard2_new"))
		# if option.title == 'Contract':
		# 	return HttpResponseRedirect(reverse("contract_wizard"))
	return render(request, 'kitcreate/select-form.html', {'form':form})
select_form = staff_member_required(select_form)
# not sure what demo_popup_main/window do
# 
def demo_popup_main(request):
	context = {}
	return render(request, 'kitcreate/popup-main.html', context)
demo_popup_main = staff_member_required(demo_popup_main)

def demo_popup_window(request, pk=1):
	context = {}
	return render(request, 'kitcreate/popup-win.html', context)
demo_popup_window = staff_member_required(demo_popup_window)


# handler404 and hander500 are suppose to replace djangos default handlers, but they are not working
def handler404(request):
	response = render_to_response('404.html', {}, context_instance=RequestContext(request))
	response.status_code = 404
	return response


def handler500(request):
	response = render_to_response('500.html', {}, context_instance=RequestContext(request))
	response.status_code = 500
	return response

# helpers
def add_business_days(from_date, number_of_days):
	"""Helper method to add business dates to a <datetime>"""
	to_date = from_date
	while number_of_days:
		to_date += timedelta(1)
		if to_date.weekday() < 5: # i.e. is not saturday or sunday
			number_of_days -= 1
	return to_date

def minus_business_days(from_date, number_of_days):
	"""Helper method to minus business dates to a <datetime>"""
	to_date = from_date
	while number_of_days:
		to_date -= timedelta(1)
		if to_date.weekday() < 5: # i.e. is not saturday or sunday
			number_of_days -= 1
	return to_date

def not_a_weekend_date(from_date, number_of_days):
	"""Helper method to minus business dates to a <datetime>"""
	to_date = from_date - timedelta(number_of_days)
	while to_date.weekday() > 4:
		to_date -= timedelta(1)			
	return to_date	


# api methods...
def fetch_event_data(request, pk):
	"""Api call to lookup an event by PK"""
	event = EventData.objects.get(pk=pk)
	return JsonResponse(event.data, safe=False)

def update_all_events(request):
	"""
	Checks Epmiddleware for latest updates from EventPath
	Adds new events, updates data for existing events
	Epmiddleware->Eventpath.Events->Epmiddleware->KitCreate
	"""
	end_point = settings.EPMIDDLEWARE_API_UPDATEEVENTS_ENDPOINT
	r = requests.get(end_point)
	if r.status_code != 200:
		messages.error(request, 'Error fetching events: %s' % r.text)
		logger.error('Error fetching events: %s' % r.text)
		return HttpResponseRedirect(reverse('admin:kitcreate_eventdata_changelist'))

	events = r.json()
	
	if not events:
		messages.error(request, 'No Data Returned from EventPath')
		logger.error('Error fetching events: %s' % r.text)
		return HttpResponseRedirect(reverse('admin:kitcreate_eventdata_changelist'))

	added_events = []
	updated_events = 0
	for event in events:		
		_obj, created = EventData.objects.get_or_create(
			event_code=event['EventCode'], 
			event_subcode=event['EventSubCode']
		)
		if created:
			_obj.description = event['Description']

		_obj.data = event
		_obj.save()
		if created:
			added_events.append(_obj.event_code)
		else:
			updated_events += 1
	if added_events:
		html = '<p>%s Events Updated</p><p>Added Events</p><ul>%s</ul>' % (updated_events, ''.join(['<li>%s</li>' % x for x in added_events]))
	else:
		html = '<p>%s Events Updated</p><p>0 New Events Added</p>' % (updated_events)
	messages.success(request, mark_safe(html)) 
	return HttpResponseRedirect(reverse('admin:kitcreate_eventdata_changelist'))

def update_all_places(request):
	"""
	Similar to update_all_events, but updates places.
	"""
	end_point = settings.EPMIDDLEWARE_API_UPDATEPLACES_ENDPOINT
	r = requests.get(end_point)
	added_places = []
	updated_places = 0
	if r.status_code != 200:
		messages.error(request, 'Error fetching places: %s' % r.text)
		logger.error('Error fetching places: %s' % r.text)
		return HttpResponseRedirect(reverse('admin:kitcreate_place_changelist'))

	places = r.json()
	
	if not places:
		messages.error(request, 'No Data Returned from EventPath')
		logger.error('Error fetching places: %s' % r.text)
		return HttpResponseRedirect(reverse('admin:kitcreate_place_changelist'))

	for place in places:	
		# if place['PlaceType'] === u'CUST-Job Mgmt':
		place_type = ''
		if place['PlaceType'] == u'CUST-Show Mgmt':
			place_type = 'showmgmt'

		if place['PlaceType'] == u'VEN-Facility':
			place_type = 'facility'

		if not place_type:
			continue

		_obj, created = Place.objects.get_or_create(code=place['PlaceCode'], type=place_type)

		if created:
			_obj.title = place['Description']
			_obj.save()
			added_places.append(str(_obj))
		else:
			updated_places += 1

	if added_places:
		html = '<p>%s Places Updated</p><p>Added Places</p><ul>%s</ul>' % (updated_places, ''.join(['<li>%s</li>' % x for x in added_places]))
	else:
		html = '<p>%s Places Updated</p><p>0 New Places Added</p>' % (updated_places)
	messages.success(request, mark_safe(html)) 
	return HttpResponseRedirect(reverse('admin:kitcreate_place_changelist'))

def _expire_servicekits(qs=None):
	results = []
	qs = qs or EventInfo.objects.filter(active=True)
	for x in qs:
		if x.is_expired:
			results.append('%s, %s' %(x.pk, str(x)))
			x.servicekitstatus = x.SERVICEKITSTATUS.expired
			x.active = False
			x.save()
	return results

def expire_servicekits(request):
	expired_kits = _expire_servicekits()
	html = '<p>Following events are now expired.</p><ul>%s</ul>' % (''.join(['<li>%s</li>' % x for x in expired_kits]))
	messages.success(request, mark_safe(html))
	return HttpResponseRedirect(reverse('kitcreate_home'))

expire_servicekits = staff_member_required(expire_servicekits)	


def internal_files(request):
	if request.user.is_staff:
		response = HttpResponse(status=200)
		response['Content-Type'] = ''
		response['X-Accel-Redirect'] = '/internalfiles/' + request.path
		return response
	else:
		return HttpResponse(status=404)

def create_service_kit_queue(request, eventinfo_pk, task_pk):
	context = {}
	eventinfo = get_object_or_404(EventInfo, pk=eventinfo_pk)
	task = Task.objects.filter(pk=task_pk).first()
	context['task'] = task
	context['eventinfo'] = eventinfo
	return render(request, 'kitcreate/create_kit_queue.html', context)

