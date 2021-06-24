from urllib import urlencode

from django import forms
from django.db.models.fields import BLANK_CHOICE_DASH
from django.forms import formset_factory
from django.forms.utils import flatatt
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string
from django.forms import inlineformset_factory
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User, Group

from model_utils import Choices

from easy_select2 import Select2, Select2Multiple

from kitcreate.models import *

def inject_boostrap_class(self):
	for visible in self.visible_fields():
		visible.field.widget.attrs['class'] = 'form-control'

class DateTypeInput(forms.DateInput):
	input_type = 'date'
	def __init__(self,*args,**kwargs):
		super(DateTypeInput, self).__init__(*args,**kwargs)

class TimeTypeInput(forms.TimeInput):
	input_type = 'time' 
	def render(self, name, value, *args, **kwargs):
		if value:
			value = value.strftime('%H:%M')
		derp = super(TimeTypeInput, self).render(name, value, *args, **kwargs)    	
		return derp
	 
class EventScheduleForm(forms.ModelForm):
	form_title = 'Event Schedule'
	form_index = 2

	class Meta:
		model = EventSchedule
		fields = ["type", "date", "start_time", "end_time", "note",]
		extra=7,
		widgets = {
			# 'type': Select2(attrs={'width': '300px'}),
			'date': DateTypeInput(),
			# 'start_time': TimeTypeInput(),
			# 'end_time':TimeTypeInput()
		}

	def __init__(self, *args, **kwargs):
		super(EventScheduleForm, self).__init__(*args, **kwargs)
		inject_boostrap_class(self)

EventScheduleFormFormset = inlineformset_factory(
		EventInfo, EventSchedule, form=EventScheduleForm, extra=7,
		# fields=["type", "date", "start_time", "end_time", "note",], 
		# widgets={
		# 	# 'type': Select2(attrs={'width': '300px'}),
		# 	# 'type': forms.Select(choices=[('exhibitor_out', 'Exhibitor Move-Out'),]),
		# 	'date': DateTypeInput(),
		# 	# 'start_time': TimeTypeInput(),
		# 	# 'end_time':TimeTypeInput()		
		# }
	)
EventScheduleFormFormset.form_title = 'Event Schedule'
EventScheduleFormFormset.form_index = 2

class Select2Wrapper(Select2):
	""" 
	Adds edit and create icons to select2 field.
	"""
	class Media:
		js = (			
			# 'admin/js/jquery.min.js',
			'/static/admin/js/jquery.init.js',
			'admin/js/admin/RelatedObjectLookups.js',
		)
	def __init__(self, popup_add_link=None, popup_change_link=None, additional_parms=None ,*args, **kwargs):
		super(Select2Wrapper, self).__init__(*args, **kwargs)
		self.popup_add_link = popup_add_link
		self.popup_change_link = popup_change_link
		self.additional_parms = additional_parms or {}


	def render(self, name, value, *args, **kwargs):
		output = super(Select2Wrapper, self).render(name, value, *args, **kwargs)
		popup_links = ''
		additional_parms = urlencode(self.additional_parms)

		if self.popup_change_link:
			change_link_url = reverse('admin:%s' % self.popup_change_link, args=('__fk__',))
			popup_links += mark_safe(
			"""
			<a id="change_id_%(name)s" class="popup-change-item"  href="%(href)s?_to_field=id&_popup=1&%(additional_parms)s" onclick="return showChangeRelatedObjectPopup(this);" alt="%(alt)s"><img src="/static/admin/img/icon-changelink.svg" alt="Change"></a>
			""" 
			% ({'href':change_link_url, 'alt':_('Edit Record'), 'name':name, 'additional_parms':additional_parms})
			)

		if self.popup_add_link:
			add_link_url = reverse(
				'admin:%s' 
				% self.popup_add_link,
			)					
			popup_links += mark_safe(
			"""
			<a id="add_id_%(name)s" class="popup-add-item" href="%(href)s?_to_field=id&_popup=1&%(additional_parms)s" onclick="return showAddAnotherPopup(this);" alt="%(alt)s"><img src="/static/admin/img/icon-addlink.svg" alt="Add"></a>""" 
			% ({'href':add_link_url, 'alt':_('Add Another'), 'name':name, 'additional_parms':additional_parms})
			)

		return output + popup_links

class Select2MultipleWrapper(Select2Multiple):
	""" 
	Adds edit and create icons to Select2Multiple field.
	"""
	class Media:
		js = (			
			# 'admin/js/jquery.min.js',
			'/static/admin/js/jquery.init.js',
			'admin/js/admin/RelatedObjectLookups.js',
		)
	def __init__(self, popup_add_link=None, popup_change_link=None, additional_parms=None ,*args, **kwargs):
		super(Select2MultipleWrapper, self).__init__(*args, **kwargs)
		self.popup_add_link = popup_add_link		
		self.additional_parms = additional_parms or {}


	def render(self, name, value, *args, **kwargs):
		output = super(Select2MultipleWrapper, self).render(name, value, *args, **kwargs)
		popup_links = ''
		additional_parms = urlencode(self.additional_parms)

		if self.popup_add_link:
			add_link_url = reverse(
				'admin:%s' 
				% self.popup_add_link,
			)					
			popup_links += mark_safe(
			"""
			<a id="add_id_%(name)s" class="popup-add-item" href="%(href)s?_to_field=id&_popup=1&%(additional_parms)s" onclick="return showAddAnotherPopup(this);" alt="%(alt)s"><img src="/static/admin/img/icon-addlink.svg" alt="Add"></a>""" 
			% ({'href':add_link_url, 'alt':_('Add Another'), 'name':name, 'additional_parms':additional_parms})
			)

		return output + popup_links

class AutoFillSelect2Widget(Select2Wrapper):
	"""
	Loads eventinfo_autofill.js
	eventinfo_autofill.js autofills EventPath data into a form when users changes selected events.
	"""
	class Media:
		js = ('kitforms/js/eventinfo_autofill.js',)	

class EventInfoAdminForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		super(EventInfoAdminForm, self).__init__(*args,**kwargs)
		self.fields["event_name"].queryset  = EventData.objects.all().order_by('event_code')
		self.fields["event_name"].queryset  = EventData.objects.all().order_by('event_code')
		self.fields["event_mgmt"].queryset  = Place.objects.filter(type='showmgmt')
		self.fields["facility"].queryset    = Place.objects.filter(type='facility')
		self.fields["salesperson"].queryset = Place.objects.filter(type='salesperson')
		self.fields["carrier"].queryset     = Place.objects.filter(type='terminal')
		self.fields["adv_wh"].queryset      = Place.objects.filter(type='terminal')
		self.fields["dir_wh"].queryset      = Place.objects.filter(type__in=['facility', 'terminal'])
	
	class Meta:
		model = EventInfo
		fields = ["event_name","event_mgmt","facility", "sales_tax", "salesperson","carrier","adv_wh","dir_wh","booth_info","carpet", "notes", "form_version"]
		widgets = {
			"event_name": Select2(attrs={'width': '300px'}),
			"event_mgmt": Select2(attrs={'width': '300px'}),
			"facility": Select2(attrs={'width': '300px'}),
			"salesperson": Select2(attrs={'width': '300px'}),
			"carrier": Select2(attrs={'width': '300px'}),
			"adv_wh": Select2(attrs={'width': '300px'}),
			"dir_wh": Select2(attrs={'width': '300px'})
		}

class EventInfoForm(forms.ModelForm):
	form_title = 'Event Info'
	form_index = 1
	def __init__(self, *args, **kwargs):

		super(EventInfoForm, self).__init__(*args,**kwargs)
		
		# self.fields['event_name'].widget = CustomRelatedFieldWidgetWrapper(AutoFillSelect2Widget(attrs={'width': '300px'}),'/',True)
		self.fields["event_name"].queryset  = EventData.objects.all().order_by('event_code', '-event_subcode')
		self.fields["event_mgmt"].queryset  = Place.objects.filter(type='showmgmt')
		self.fields["facility"].queryset    = Place.objects.filter(type='facility')
		self.fields["salesperson"].queryset = Place.objects.filter(type='salesperson')
		self.fields["carrier"].queryset     = Place.objects.filter(type='terminal')
		self.fields["adv_wh"].queryset      = Place.objects.filter(type='terminal')
		self.fields["dir_wh"].queryset      = Place.objects.filter(type__in=['facility', 'terminal'])

		default_form_version = settings.FORM_VERSION
		form_version = FormVersion.objects.filter(title=default_form_version).first()
		if form_version:
			self.fields['form_version'].initial = form_version

		inject_boostrap_class(self)

		# import ipdb; ipdb.set_trace()
	
	class Meta:
		model = EventInfo
		fields = [
			"event_name", "event_mgmt", "facility",
			"sales_tax", "salesperson", "carrier", 
			"adv_wh","dir_wh","booth_info", 
			"carpet", "notes", "internal_note", 
			"form_version",
		]
		widgets = {
			"event_name": AutoFillSelect2Widget(popup_add_link="kitcreate_eventdata_add", popup_change_link="kitcreate_eventdata_change", attrs={'width': '300px'}),
			"event_mgmt": Select2Wrapper(additional_parms={'type':'showmgmt'}, popup_change_link="kitcreate_place_change",popup_add_link="kitcreate_place_add", attrs={'width': '300px'}),
			"facility": Select2Wrapper(additional_parms={'type':'facility'}, popup_change_link="kitcreate_place_change",popup_add_link="kitcreate_place_add", attrs={'width': '300px'}),
			"salesperson": Select2Wrapper(additional_parms={'type':'salesperson'}, popup_change_link="kitcreate_place_change",popup_add_link="kitcreate_place_add", attrs={'width': '300px'}),
			"carrier": Select2Wrapper(additional_parms={'type':'carrier'}, popup_change_link="kitcreate_place_change",popup_add_link="kitcreate_place_add", attrs={'width': '300px'}),
			"adv_wh": Select2Wrapper(additional_parms={'type':'terminal'}, popup_change_link="kitcreate_place_change",popup_add_link="kitcreate_place_add", attrs={'width': '300px'}),
			"dir_wh": Select2Wrapper(additional_parms={'type':'terminal'}, popup_change_link="kitcreate_place_change",popup_add_link="kitcreate_place_add", attrs={'width': '300px'})
		}
	

class PriceLevelForm(forms.Form):
	form_title = 'Price Level Selection'
	form_index = 3
	def __init__(self, *args, **kwargs):
		super(PriceLevelForm, self).__init__(*args,**kwargs)
		# creates dropdown list, by type, with available price levels.
		for service_type in ServiceType.objects.all().exclude(title="Default").order_by('title'):
			choices = []
			for x in service_type.servicelevel_set.all():
				choices.append((x.pk, x.title))
			
			# self.fields[service_type.title] = forms.ChoiceField(
			# 	required=False, 
			# 	choices=BLANK_CHOICE_DASH + choices, 
			# 	widget=Select2(attrs={'width': '300px'})
			# )

			self.fields[service_type.title] = forms.MultipleChoiceField(
				required=False, 		
				choices=BLANK_CHOICE_DASH + choices, 
				widget=Select2Multiple(select2attrs={'width': '300px'})
			)			

		inject_boostrap_class(self)

class ServiceSelectionForm(forms.Form):
	form_title = 'Service Selection'
	form_index = 4

	def __init__(self, servicelevel, form_version, *args, **kwargs):
		super(ServiceSelectionForm, self).__init__(*args,**kwargs)
		# Creates fields for each available form in a service level. 
		self._fieldsets = []
		self.servicelevel = servicelevel
		if form_version:
			self.form_version = form_version			
		else:
			self.form_version = FormVersion.objects.filter(
				title=settings.FORM_VERSION).first()

		for level_title, level_pks in self.servicelevel.items():
			if not level_pks:
				continue
			_fields = []

			servicekitforms = ServiceKitForm.objects.filter(
					level__pk__in=level_pks, 
					form_version=self.form_version
				).order_by('title').distinct()
			
			for servicekitform in servicekitforms:
				self.fields[servicekitform.title] = forms.BooleanField(required=False)
				self.fields[servicekitform.title]._servicekitform_pk = servicekitform.pk
				_fields.append(servicekitform.title)

			# Will only display services if they have level_pk
			# It maybe helpful to user to show Service Heading even if nothing is selected 
			self._fieldsets.append(({
				"key": level_pks, 
				"title":level_title, 
				"fields":_fields
			}))
		self.form_title = 'Service Selection'
		inject_boostrap_class(self)		
	
	def get_servicekitforms_pks(self):
		# if not valid, fail?
		pks = []
		for key, value in self.cleaned_data.items():
			if value:
				pks.append(self.fields[key]._servicekitform_pk)
		return pks

	def get_servicekitforms(self):
		return ServiceKitForm.objects.filter(pk__in=self.get_servicekitforms_pks())		

	def has_fieldsets(self):
		return True

	def fieldsets(self):
		# returns the fieldset dictionary for a template to use.
		results = []
		for fieldset in self._fieldsets:
			title = fieldset.get('title')
			fields = [self[x] for x in fieldset.get('fields')]
			results.append({
				"title": title,
				"fields": fields
			})
		return results

class SelectFormWidget(forms.widgets.Input):
	"""Create a widget to allow user to select exisiting or upload new forms"""	
	template_name = 'kitcreate/widgets/select_form_widget.html'
	input_type = 'text'

	def render(self, name, value, attrs=None): 	
		href = "%s?_popup=1" % reverse('servicekitforms_listview')
		repr_value = ''
		attrs.update({'class':'form-control'})

		final_attrs = self.build_attrs(attrs, extra_attrs=dict(type=self.input_type, name=name))
		
		if value and value != 'None':
			repr_value = ServiceKitForm.objects.get(pk=value).title

		context = {
			'url': href,
			'name': name,
			'value': value,
			'id': attrs.get('id'),
			'attrs': flatatt(final_attrs),
			'repr_value': repr_value
		}        
		return mark_safe(render_to_string(self.template_name, context))

	class Media:
		js = ('kitforms/js/select_form_widget.js',)

# DocForm.model just needs a Filebrowser.FileObject(path/to/upload/file)
# process_step_files(self, form):
class AdditionalFormsForm(forms.Form):
	form_title = 'Additional Form'
	form_index = 5
	form = forms.CharField(max_length=50, widget=SelectFormWidget())
	# document = forms.FileField()
	# document = FileBrowseFormField
	def __init__(self, *args, **kwargs):
		super(AdditionalFormsForm, self).__init__(*args, **kwargs)
		inject_boostrap_class(self)

AdditionalFormsFormset = formset_factory(AdditionalFormsForm, extra=7, can_delete=True)
AdditionalFormsFormset.form_title = "%s's" % AdditionalFormsForm.form_title
AdditionalFormsFormset.form_index = 5
AdditionalFormsFormset.form_description = """Use this form to include additional forms, like facility forms"""


class SortSkFormsForm(forms.ModelForm):
	"""
	Used to sort ServiceKitForms
	"""
	def __init__(self, eventinfo, *args, **kwargs):

		super(SortSkFormsForm, self).__init__(*args,**kwargs)
		inject_boostrap_class(self)
		obj = kwargs.get('instance', None)
		if obj:		
			# stupd af code down below but kinda working
			# ideally original selected forms from wizard should persist even if unchecked
			if eventinfo:
				levels_pk = []
				# find all the selected forms (user added forms would be missed otherwise)
				sk_forms      = [x.pk for x in obj.forms.all()]
				# gather all the price levels from the event
				price_levels  = [x.pk for x in eventinfo.price_levels.all()]
				# gather the default items
				default_items = [x.pk for x in ServiceLevel.objects.filter(type__title="Default")]
				# merge the two and remove duplicate pks
				levels_pk  = set(price_levels + default_items)
				# look for forms with the price levels or if they are in the service kit
				derp = ServiceKitForm.objects.filter(level__in=levels_pk, form_version=eventinfo.form_version)
				qs = ServiceKitForm.objects.filter(pk__in=set(sk_forms + [x.pk for x in derp]))			
				self.fields['forms'].queryset = qs
			else:			
				default_form_version = settings.FORM_VERSION
				form_version = FormVersion.objects.filter(title=default_form_version).first()
				# self.fields['forms'].queryset = obj.forms	
				self.fields['forms'].queryset = obj.forms.filter(form_version=form_version)
		
				
	class Meta:
		model = ServiceKit
		fields = ['forms']

class EventInfoStatusForm(forms.ModelForm):
	notify = forms.CharField(widget=forms.HiddenInput(), required=False)
	
	def __init__(self, *args, **kwargs):
		super(EventInfoStatusForm, self).__init__(*args, **kwargs)
		defaultgroup = None
		defaultgroup = Group.objects.filter(name="EventCoordinators").first()
		if defaultgroup:
			defaultgroup = defaultgroup.pk
		self.fields['status'].widget.attrs.update({
			'title': 'Service Kit Status',
			'data-defaultgroup': defaultgroup
		})
	
	class Meta:
		model = EventInfo
		fields = ('status', 'notify')

class EventInfoStorefrontStatusForm(forms.ModelForm):
	notify2 = forms.CharField(widget=forms.HiddenInput(), required=False)
	
	def __init__(self, *args, **kwargs):
		super(EventInfoStorefrontStatusForm, self).__init__(*args, **kwargs)
		defaultgroup = None
		defaultgroup = Group.objects.filter(name="CustomerService").first()
		if defaultgroup:
			defaultgroup = defaultgroup.pk
		self.fields['storefrontstatus'].widget.attrs.update({
			'title': 'Storefront Status',
			'data-defaultgroup': defaultgroup
		})
		inject_boostrap_class(self)
		
	class Meta:
		model = EventInfo
		fields = ('storefrontstatus', 'notify2')

class Servicekits_FilterForm(forms.Form):
	_ORDER_BY_MAP = {
		'1':'event_name__event_code',
		'2':'event_mgmt__title',
		'3':'facility__title',
		'4':'salesperson__title',
		'5':'event_start_date',
		'6':'servicekitstatus'
	}
	_ORDER_BY = Choices(
		('1', 'Event Name'), 
		('2', 'Show Mgmt'),
		('3', 'Facility'), 
		('4', 'AE'), 
		('5', 'Start Date'), 
		('6', 'Servicekit Status')
	)

	search_text      = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Search By:Events, Mgmt, Facilities, AE'}))
	start_date       = forms.DateField(required=False, widget=DateTypeInput())
	end_date         = forms.DateField(required=False, widget=DateTypeInput())
	order_by         = forms.ChoiceField(choices=_ORDER_BY, required=False)
	servicekitstatus = forms.MultipleChoiceField(
		required=False, 		
		choices=EventInfo.SERVICEKITSTATUS,
		widget=Select2Multiple(select2attrs={'width': '300px'})
	)
	def __init__(self, *args, **kwargs):
		super(Servicekits_FilterForm, self).__init__(*args, **kwargs)
		inject_boostrap_class(self)
		
	def clean_order_by(self):
		"""Obscure table field names a weeeee bit."""
		result = None
		map_id = self.cleaned_data.get('order_by', '')
		if self._ORDER_BY_MAP.has_key(map_id):
			result = self._ORDER_BY_MAP.get(map_id)
		else:
			result = self._ORDER_BY_MAP.values()[0]
		return result


class ServicekitstatusForm(forms.ModelForm):
	send_notification = forms.CharField(widget=forms.HiddenInput(), required=False)
	search_query = forms.CharField(widget=forms.HiddenInput(), required=False)
	# redirect = forms.CharField(widget=forms.HiddenInput(), required=False)

	def __init__(self, *args, **kwargs):
		super(ServicekitstatusForm, self).__init__(*args, **kwargs)
		defaultgroup = None
		defaultgroup = Group.objects.filter(name="EventCoordinators").first()
		if defaultgroup:
			defaultgroup = defaultgroup.pk
		self.fields['servicekitstatus'].widget.attrs.update({
			'title': 'Servicekit Status',
			'data-defaultgroup': defaultgroup
		})
		inject_boostrap_class(self)
					
	class Meta:
		model = EventInfo
		fields = ('servicekitstatus', 'send_notification', 'search_query')

class InternalNoteForm(forms.ModelForm):
	class Meta:
		model = EventInfo
		fields = ['internal_note',]

class StatusMessageForm(forms.Form):
	status_type = forms.CharField(widget=forms.HiddenInput())
	status = forms.CharField()
	group  = forms.ChoiceField(required=False, widget=Select2(
		select2attrs={'width': '300px'}
	))
	emails = forms.MultipleChoiceField(required=False, widget=Select2Multiple(
		select2attrs={'width': '300px'}
	))	
	message = forms.CharField(widget=forms.Textarea)	

	def __init__(self, *args, **kwargs):
		kwargs.update({'auto_id':"statusmessageform__%s"})
		super(StatusMessageForm, self).__init__(*args, **kwargs)
		self.fields['group'].choices = BLANK_CHOICE_DASH + [(obj.pk, obj.name) for obj in Group.objects.all()]	
		
		
		if kwargs.has_key('initial'):
			self.fields['status_type'].initial = kwargs['initial'].get('status_type', '')

		if self.fields['status_type'].initial == 'status':
			self.fields['group'].initial = Group.objects.get(name="EventCoordinators").pk

		self.fields['emails'].choices = [(obj.pk, obj.email) for obj in User.objects.filter(is_active=True)]
		inject_boostrap_class(self)
		
class UploadServiceKitForm(forms.ModelForm):
	"""
	Form for creating and updating a ServiceKitForm
	"""
	file = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={'accept':'.docx, .pdf, .doc'}))	
	title = forms.CharField(required=False)
	class Meta:
		model   = ServiceKitForm
		fields  = ['title', 'level', 'form_version']
		widgets = {
			# 'level': Select2Multiple(select2attrs={'width': '300px'})			
			'level': Select2MultipleWrapper(select2attrs={'width': '300px'}, popup_add_link="kitcreate_servicelevel_add")			
		}
		help_texts = {
			'level': 'Select a Service Level to attach this form to. If no Service Level exits, click the "+" to add a new level.'
		}

	def __init__(self, *args,**kwargs):		
		super(UploadServiceKitForm, self).__init__(*args, **kwargs)		
		if not self.instance.pk:
			self.fields['form_version'].initial = FormVersion.objects.first().pk
		# self.fields['level'].widget = Select2Multiple(select2attrs={'width': '300px'})
		inject_boostrap_class(self)

# MISC Forms.
class DynamicForm(forms.Form):
	def __init__(self, model_instance=None, *args, **kwargs):
		self.model_instance = model_instance
		super(DynamicForm, self).__init__(*args, **kwargs)
		if self.model_instance:
			self.add_the_fields()

	def add_the_fields(self, *args, **kwargs):
		for field in self.model_instance.fields.all().order_by('title'):
			# field.type.title #type of widget to use...
			# field.title # field name
			# field.description # label
			self.fields[field.title] = forms.CharField(
				label=field.description or field.title, 
				required=False, 
				widget=settings.KITFORMS_DOCFIELDTYPE_WIDGET_MAP[field.type.title]()
			)
class DemoTemplateForm(DynamicForm): pass
	# example useage of the DynamicForm
	# pass it a template to use and it will generate a form to input
	# views.wizard.get_form_kwargs(self, step):
	# if step == 'boothoptionsform':
	# 	return {"model_instance":DocTemplate.objects.all()[2]}

class ServiceKitFieldValueForm(forms.Form):	
	form_title = 'Extra Form Field Values'
	def __init__(self, servicekitforms, servicekit=None, *args, **kwargs):
		super(ServiceKitFieldValueForm, self).__init__(*args,**kwargs)

		self._fieldsets = []
		self.servicekit = servicekit
		self.servicekitforms = servicekitforms
		for servicekitform in self.servicekitforms:
			_fields = []
			for servicekitfield in servicekitform.form_fields.all().order_by('title'):
				value = None
				servicekitfieldvalue = ServiceKitFieldValue.objects.filter(field__title=servicekitfield.title, kit=self.servicekit).first()			

				if servicekitfieldvalue and servicekitfieldvalue.value:
					value = servicekitfieldvalue.value				

				field_title = "%s-%s" % (servicekitform.pk, servicekitfield.title)
				self.fields[field_title] = forms.CharField(
					label=servicekitfield.label, 
					required=False,
					initial=value
					# prefix=servicekitform.title
				)
				self.fields[field_title].servicekitfield_pk = servicekitfield.pk
				self.fields[field_title].servicekitform_pk = servicekitform.pk
				_fields.append(field_title)
			if _fields:
				self._fieldsets.append(({
					"key": servicekitform.pk, 
					"title": servicekitform.title, 
					"fields": _fields
				}))

	def has_fieldsets(self):
		return True

	def fieldsets(self):
		results = []
		for fieldset in self._fieldsets:
			title = fieldset.get('title')
			fields = [self[x] for x in fieldset.get('fields')]
			results.append({
				"title": title,
				"fields": fields
			})
		return results

	def save_values(self, servicekit):
		results = []
		for key, value in self.cleaned_data.items():
			_pk = self.fields[key].servicekitfield_pk			
			servicekitfield = ServiceKitField.objects.filter(pk=_pk).first()
			if not servicekitfield:
				continue
			servicekitfieldvalue, created = ServiceKitFieldValue.objects.get_or_create(
				field=servicekitfield, 
				kit=servicekit, 
			)
			if not value:
				servicekitfieldvalue.delete()
				continue
			servicekitfieldvalue.value = value
			servicekitfieldvalue.save()
			results.append(servicekitfieldvalue.pk)
		return results

# Used to select type of form user would like to create... servicekit, proposal, ect.
class SelectKitForm(forms.Form):
	# kit_type = forms.ModelChoiceField(queryset=DocType.objects.filter(parent__isnull=True))
	# options = forms.ModelChoiceField(queryset=DocType.objects.filter(parent__isnull=True), widget=Select2())
	options = forms.ChoiceField(choices=[('servicekit', 'ServiceKit')], widget=Select2())
