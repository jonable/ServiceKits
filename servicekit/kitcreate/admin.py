from django.core.urlresolvers import reverse
# from django.http import HttpResponseRedirect
from django.contrib import admin
from django.conf import settings
from django import forms

from kitcreate.models import *
# Register your models here.
from kitcreate.forms import EventInfoAdminForm


def view_service_kit(obj):
	"""
	Create a link if an event data has a service kit.
	"""
	eventinfo = obj.event_info.last()
	if eventinfo:	
		return "<a href=\"%s\">View ServiceKit</a>" % reverse('servicekit_complete', args=(eventinfo.pk,))
	return "<a href=\"%s\">No Kit Created</a>" % reverse('servicekit_wizard2_new')
view_service_kit.short_description = 'ServiceKit'
view_service_kit.allow_tags = True

class EventDataAdmin(admin.ModelAdmin):
	search_fields = ['description', 'event_code']
	list_display = ('event_code', 'description', 'event_subcode', view_service_kit)
admin.site.register(EventData, EventDataAdmin)

class PlaceAdmin(admin.ModelAdmin):
	list_display = ['title', 'code', 'type', 'city', 'state', 'zip']
	search_fields = ['title', 'code', 'type']
admin.site.register(Place, PlaceAdmin)

class EventScheduleAdmin(admin.ModelAdmin):
	pass	
admin.site.register(EventSchedule, EventScheduleAdmin)

class EventScheduleInlineAdmin(admin.TabularInline): 
	model = EventSchedule


def view_servicekit_pdf(obj):
	# if EventInfo has a service kit, create a link to it.
	result = ''
	result += '<a href="%s" target="_blank">SITE</a> | ' % (reverse('servicekit_complete', args=(obj.pk,)))
	if obj.get_pdf_url():
		result += "<a href=\"%s%s\" target=\"_blank\">PDF</a>" % (settings.MEDIA_URL, obj.get_pdf_url())
		new_directory_name = "%s-%s" % (obj.pk, obj._filename)
		fb_browse = os.path.join('kits', new_directory_name)
		result += ' | '
		result += "<a href=\"%s?dir=%s\" target=\"_blank\">DIR</a>" % (reverse('filebrowser:fb_browse'), fb_browse)	
	return result 
view_servicekit_pdf.short_description = 'View'
view_servicekit_pdf.allow_tags = True

class EventInfoAdmin(admin.ModelAdmin):
	form = EventInfoAdminForm	
	inlines = (EventScheduleInlineAdmin,)
	list_display = ["event_name", "event_mgmt", "facility", "salesperson", view_servicekit_pdf, "status", 'storefrontstatus']
	search_fields = ["event_name__description", "event_mgmt__title", "salesperson__title", "status"]
	filter_horizontal = ('price_levels',)
	fieldsets = (
		(None, {'fields': [
			"service_kit","event_name","event_mgmt",
			"facility","salesperson","carrier",
			"adv_wh","dir_wh","booth_info",
			"notes","price_levels","output_dir",
			"internal_note", "form_version"
		]}),
		('Event Info Status', {'fields': 
			(
				"status","status_changed",
				"storefrontstatus","storefrontstatus_changed",
				"servicekitstatus", "ae_pulled","given_to_ae","completed_by_ae","proofed_by_exhibitor_services","sent_to_sm","approved_goshow","list_received","published"
			)})
	)


admin.site.register(EventInfo, EventInfoAdmin)

class ServiceTypeAdmin(admin.ModelAdmin):
	pass
admin.site.register(ServiceType, ServiceTypeAdmin)

class ServiceLevelAdminForm(forms.ModelForm):
	class Meta:
		model = ServiceLevel
		fields = ('title', 'description', 'type')

	def clean(self):
		title =  self.cleaned_data.get('title')
		# level_type =  self.cleaned_data.get('type')
		like_titles = ServiceLevel.objects.filter(title__icontains=title)
		if like_titles:			
			raise forms.ValidationError("A similar Service Level exists. Please select the existing level, or use a unique name.")
		return self.cleaned_data

class ServiceLevelAdmin(admin.ModelAdmin):
	form = ServiceLevelAdminForm
	list_display = ('title',)
	list_filter = ('title',)
	search_fields = ('title',)
admin.site.register(ServiceLevel, ServiceLevelAdmin)

class ServiceKitFormInline(admin.TabularInline):
	model           = ServiceKit.forms.through
	fields          = ('servicekitform', 'view_form',)
	readonly_fields = ('servicekitform', 'view_form',)
	extra           = 0
	def view_form(self, obj):
		"""
		Create a link to view a form in filebrowser app.
		"""
		result = ""
		try:
			if obj.servicekit and  obj.servicekitform:
				eventinfo  = obj.servicekit.eventinfo_set.last()
				form_title =  obj.servicekitform.document.filename
				url = "/uploads/kits/%s-%s/%s" % (eventinfo.pk, eventinfo._filename, form_title)	
				result += "<a href=\"%(url)s\" target=\"_blank\">%(url)s</a>" % ({'url':url})
		except Exception:
			pass
		return result
	view_form.allow_tags = True

class ServiceKitAdmin(admin.ModelAdmin):
	inlines = [ServiceKitFormInline]
	list_display = ("title","description")
	list_filter = ("title","description")
	search_fields = ("title","description")
	
admin.site.register(ServiceKit, ServiceKitAdmin)

def display_servicekitform_levels(obj):
	 return ', '.join([x.title for x in obj.level.all()])
display_servicekitform_levels.short_description = 'Levels'

def has_form(obj):
	return obj.has_form 
has_form.boolean = True



class FormVersionAdmin(admin.ModelAdmin):
	'''
		Admin View for FormVersion
	'''
	list_display = ('title','path',)
	list_filter = ('title',)

admin.site.register(FormVersion, FormVersionAdmin)


class ServiceKitFieldInlineAdmin(admin.TabularInline): 
	model = ServiceKitField

class ServiceKitFormAdmin(admin.ModelAdmin):
	filter_horizontal = ('level',)
	list_display = ('title', display_servicekitform_levels, 'form_version', has_form)
	search_fields = ('title',  "level__title", 'form_version__title')
	save_as = True
	def changelist_view(self, request, extra_context=None):
		extra_context = extra_context or {}
		extra_context['is_add_form'] = '_addform' in request.GET
		return super(ServiceKitFormAdmin, self).changelist_view(request, extra_context=extra_context)

	def add_view(self, request, form_url='', extra_context=None):
		extra_context = extra_context or {}
		# extra_context['osm_data'] = self.get_osm_info()
		return super(ServiceKitFormAdmin, self).add_view(
			request, form_url, extra_context=extra_context,
		)

admin.site.register(ServiceKitForm, ServiceKitFormAdmin)



class ServicePriceListAdmin(admin.ModelAdmin):
	pass	
admin.site.register(ServicePriceListMap, ServicePriceListAdmin)
