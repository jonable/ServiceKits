from __future__ import unicode_literals
import os
from collections import OrderedDict
from datetime import timedelta, datetime

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.forms.utils import pretty_name
from django.utils.text import slugify
from django.db import models
from jsonfield import JSONField
from filebrowser.base import FileObject
from filebrowser.fields import FileBrowseField
from filebrowser.sites import site
from sortedm2m.fields import SortedManyToManyField

from model_utils.fields import StatusField, MonitorField
from model_utils import Choices, FieldTracker

class Place(models.Model):
	"""
	People, person, company, ... model
	"""
	type_choices = [
		('facility', 'Facility',),
		('showmgmt', 'Show Mgmt',),
		('salesperson', 'Sales Person',),
		('terminal', 'Terminal',),
		('carrier', 'Carrier',),
		('other', 'Other')
	]
	title    = models.CharField(max_length=255)
	code     = models.CharField(max_length=255, blank=True)
	type     = models.CharField(max_length=255, choices=type_choices)
	address1 = models.CharField(max_length=255, blank=True)
	address2 = models.CharField(max_length=255, blank=True)
	city     = models.CharField(max_length=255, blank=True)
	state    = models.CharField(max_length=255, blank=True)
	zip      = models.CharField(max_length=255, blank=True)

	def __unicode__(self):
		return "%s -- %s" % (self.title, self.code)

class EventData(models.Model):
	"""Copy of EventPath Event Data"""
	description   = models.CharField("Event Name", max_length=255, blank=True)
	event_code    = models.CharField(max_length=255)
	event_subcode = models.CharField(max_length=255)	
	data          = JSONField('EventData', default='[""]')

	def __str__(self):
		return "%s - %s" % (self.event_code, self.event_subcode)

	class Meta:
		unique_together = ('event_code', 'event_subcode',)
		index_together = ('event_code', 'event_subcode',)

		verbose_name = 'Events'
		verbose_name_plural = 'Events'

class EventSchedule(models.Model):
	"""
	Schedule line items for an Event.
	"""
	date_types = [		
		("company_in", "Company Move in"),
		("company_out", "Company Move out"),		
		("exhibitor_in", "Exhibitor Move in"),
		("exhibitor_out", "Exhibitor Move out"),
		("event_date", "Event Date"),
		# ("discount", "Discount Deadline"),
		("discount_date", "Discount Deadline"),
		("carrier_pickup", "Carrier Pickup"),
		("advance_ship_date", "Advance Shipping Start Date"),
		("direct_ship_date", "Direct Shipping Start Date"),
		("thirty_days_prior", 'Thirty Days Prior')
	]
	_default_time_format = '%I:%M %p'
	_default_date_format = '%m-%d-%Y'

	type       = models.CharField(max_length=255, choices=date_types)
	date       = models.DateField()
	start_time = models.TimeField(blank=True, null=True)
	end_time   = models.TimeField(blank=True, null=True)
	note       = models.CharField(max_length=255, blank=True)
	event      = models.ForeignKey('EventInfo', related_name='schedule', blank=True)
	
	def __unicode__(self):
		return self.type

	class Meta:
		ordering = ['date', 'start_time', 'end_time']

	def _to_datetime(self, time_type='start_time'):

		# 'start_time', 'end_time'
		date = self.date
		time = getattr(self, time_type, None) or datetime.strptime('00:00', '%H:%M').time()		
		# log a warning if the time isn't set. not sure how best to handle this.
		return datetime.combine(date, time)

	@property 
	def type_name(self):
		for x in self.date_types:
			if self.type in x:
				return x[1]
		return self.type

	@property
	def full_date(self):
		return self.date.strftime('%B %d, %Y')

	@property
	def day_of_week(self):
		return self.date.strftime("%A")

	# @property
	# def abbrv_date(self):
	# 	"""
	# 	
	# 	"""
	# 	return self.date.strftime(self._default_time_format)

	@property
	def start_time_str(self):
		"""
		:return <string> start time.
		"""
		if not self.start_time:
			return ''
		return self.start_time.strftime(self._default_time_format)
	@property
	def end_time_str(self):
		"""
		:return <string> end time.
		"""
		if not self.end_time:
			return ''
		return self.end_time.strftime(self._default_time_format)

	@property
	def start_and_end_time(self):
		"""
		:return <string> "StartTime - EndTime"
		"""
		if not self.start_time and not self.end_time:
			return ''
		if self.start_time and not self.end_time:
			return "%s - ..." % self.start_time_str
		if self.end_time and not self.start_time:
			return "... - %s " % self.end_time_str
		result = '%s - %s'
		return result % (self.start_time.strftime(self._default_time_format), self.end_time.strftime(self._default_time_format))

class EventInfoManager(models.Manager):
	"""
	Model manager for EventInfo.
	"""
	def order_by_event_date(self, reverse=False):	
		"""
		Order EventInfo objects by first event date.	
		"""
		_event_date = []
		for eventinfo in self.all():
			event_dates = eventinfo.schedule.filter(type='event_date')
			if event_dates:
				_event_date.append(eventinfo.schedule.filter(type='event_date').first())
		# return [x.event for x in sorted(_event_date, key=lambda x:x.date)]
		# pk_list = [x.id for x in EventInfo.objects.event_date_order()]
		pk_list = [eventschedule.event.id for eventschedule in sorted(_event_date, key=lambda eventschedule:eventschedule.date, reverse=reverse)]		
		clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(pk_list)])
		ordering = 'CASE %s END' % clauses
		return self.filter(pk__in=pk_list).extra(select={'ordering': ordering}, order_by=('ordering',))
				
	def filter_by_month(self, months=None, reverse=False):
		"""
		Filter QS by month	
		:months [ints] list of months to filter by (months are interger representations)
		"""
		_event_date = []
		months = months or []
		for eventinfo in self.all():
			event_dates = eventinfo.schedule.filter(type='event_date')
			derp = None
			if event_dates:
				derp = event_dates.first()
				if derp.date.month in months:				
					_event_date.append(derp)
		# return [x.event for x in sorted(_event_date, key=lambda x:x.date)]
		# pk_list = [x.id for x in EventInfo.objects.event_date_order()]
		pk_list = [eventschedule.event.id for eventschedule in sorted(_event_date, key=lambda eventschedule:eventschedule.date, reverse=reverse)]		
		clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(pk_list)])
		ordering = 'CASE %s END' % clauses
		return self.filter(pk__in=pk_list).extra(select={'ordering': ordering}, order_by=('ordering',))		


	def filter_by_daterange(self, start_date=None, end_date=None, reverse=False):
		"""
		Filter QS by a date range	
		:start_date, end_date <datetime object>
		"""
		EVENTINFO_DEFAULT_RANGE = (30, 1)
		_event_date = []
		start_date = start_date # or (datetime.now() - timedelta(EVENTINFO_DEFAULT_RANGE[0]))
		end_date   = end_date # or (datetime.now() + timedelta(EVENTINFO_DEFAULT_RANGE[1]))
		
		for eventinfo in self.all():
			event_dates = eventinfo.schedule.filter(type='event_date')
			derp = None
			if event_dates:
				derp = event_dates.first()
				if start_date and end_date:
					# if derp.date >= start_date.date() and derp.date <= end_date.date():				
					if derp.date >= start_date and derp.date <= end_date:				
						_event_date.append(derp)
				elif start_date and not end_date:
					if derp.date >= start_date.date():
						_event_date.append(derp)
				elif end_date and not start_date:
					if derp.date <= end_date.date():
						_event_date.append(derp)

		pk_list = [eventschedule.event.id for eventschedule in sorted(_event_date, key=lambda eventschedule:eventschedule.date, reverse=reverse)]		
		# kitcreate_eventinfo.id needed else operationalerror thrown.
		clauses = ' '.join(['WHEN kitcreate_eventinfo.id=%s THEN %s' % (pk, i) for i, pk in enumerate(pk_list)])
		ordering = 'CASE %s END' % clauses
		return self.filter(pk__in=pk_list).extra(select={'ordering': ordering}, order_by=('ordering',))		

	def filter_by_daterange2(self, start_date=None, end_date=None, reverse=False):
		return self.filter(event_start_date__range=(start_date,end_date))


class EventInfo(models.Model):
	"""
	Represents all the ServiceKit information for an Event. 
	"""
	objects = EventInfoManager()

	event_name  = models.ForeignKey('EventData', related_name='event_info')
	event_mgmt  = models.ForeignKey('Place', related_name="event_mgmt")
	facility    = models.ForeignKey('Place', related_name="facility")
	salesperson = models.ForeignKey('Place', related_name="salesperson")
	carrier     = models.ForeignKey('Place', related_name="carrier", blank=True, null=True)
	adv_wh      = models.ForeignKey('Place', related_name="adv_wh", blank=True, null=True)
	dir_wh      = models.ForeignKey('Place', related_name="dir_wh", blank=True, null=True)
	service_kit = models.ForeignKey('ServiceKit', blank=True, null=True)
	output_dir  = models.CharField('Output Directory', blank=True, null=True, max_length=255)
	price_levels = models.ManyToManyField('ServiceLevel', blank=True)
	# event_website = ''
	# sales tax?
	booth_info = models.TextField(blank=True, help_text="please describe all standard booth equipment for this event")
	sales_tax  = models.CharField(max_length=255, blank=True, null=True)
	carpet     = models.TextField(blank=True, help_text="please describe carpet for this event")
	notes      = models.TextField(blank=True)
	internal_note = models.TextField(blank=True)
	
	STATUS = Choices('draft', 'review', 'approved', 'published', 'expired')
	status = StatusField()
	status_changed = MonitorField(monitor='status')
	status_tracker = FieldTracker(fields=['status'])

	SERVICEKITSTATUS = Choices(
		('ae_pulled', 'AE Pulled'),
		('given_to_ae', 'Given to AE'),
		('completed_by_ae', 'Completed by AE'),
		('proofed_by_exhibitor_services', 'Proofed by Exhibitor services', ),
		('sent_to_sm','Sent to SM'),
		('approved_goshow', 'Approved, Ready For Boomer'),
		('list_received','List received'),
		('published','Published, Sent To Exhibitors'),
		('expired','Expired/Archived'),
	)

	servicekitstatus = StatusField(choices_name='SERVICEKITSTATUS', default='ae_pulled')
	# because ae_pulled is initial status, needs a date and can't default to none (the system won't fill in the date..)
	ae_pulled	                  = MonitorField(monitor="servicekitstatus", when=['ae_pulled'], blank=True, null=True)
	given_to_ae                   = MonitorField(monitor="servicekitstatus", when=['given_to_ae'], blank=True, default=None, null=True)
	completed_by_ae               = MonitorField(monitor="servicekitstatus", when=['completed_by_ae'], blank=True, default=None, null=True)
	proofed_by_exhibitor_services = MonitorField(monitor="servicekitstatus", when=['proofed_by_exhibitor_services'], blank=True, default=None, null=True)
	sent_to_sm                    = MonitorField(monitor="servicekitstatus", when=['sent_to_sm'], blank=True, default=None, null=True)
	approved_goshow               = MonitorField(monitor="servicekitstatus", when=['approved_goshow'], blank=True, default=None, null=True)
	list_received                 = MonitorField(monitor="servicekitstatus", when=['list_received'], blank=True, default=None, null=True)
	published                     = MonitorField(monitor="servicekitstatus", when=['published'], blank=True, default=None, null=True)

	STOREFRONTSTATUS = Choices('pending','draft', 'review', 'approved', 'published', 'expired')
	storefrontstatus = StatusField(choices_name='STOREFRONTSTATUS', default=STOREFRONTSTATUS.pending)
	storefrontstatus_changed = MonitorField(monitor='storefrontstatus')
	storefrontstatus_tracker = FieldTracker(fields=['storefrontstatus'])

	# Meta Fields for Indexing...
	active           = models.BooleanField(default=True)
	event_start_date = models.DateTimeField(blank=True, null=True)
	event_end_date   = models.DateTimeField(blank=True, null=True)

	form_version = models.ForeignKey("kitcreate.FormVersion", blank=True, null=True, related_name="events")
	
	modified_on = models.DateTimeField(auto_now=True, blank=True, null=True)

	def __unicode__(self):
		return "%s - %s" % (self.event_name.event_code, self.event_name.event_subcode)

	@property
	def is_editable(self):
		# return (not self.status in ['approved', 'published', 'expired'])
		return not (self.servicekitstatus in [self.SERVICEKITSTATUS.approved_goshow, self.SERVICEKITSTATUS.list_received, self.SERVICEKITSTATUS.published, self.SERVICEKITSTATUS.expired])

	@property
	def is_expired(self):

		if self.servicekitstatus == self.SERVICEKITSTATUS.expired:
			return True

		today             = datetime.now().date()
		expired_threshold = today - timedelta(settings.EXPIRED_DAYS_THRESHOLD)
		event_date        = self.schedule.filter(type='event_date').first()
		
		if event_date and (event_date.date <= expired_threshold):
			return True
			
	def _update_event_dates(self):
		"Cache event start and end date on the model"
		eventdates = EventSchedule.objects.filter(event=self, type='event_date')
		if eventdates.count() == 1:
			event_start_date = eventdates.first()
			self.event_start_date = event_start_date._to_datetime(time_type='start_time')
			self.event_end_date   = event_start_date._to_datetime(time_type='end_time')
			self.save()
		
		if eventdates.count() >= 2:
			event_start_date = eventdates.first()
			self.event_start_date = event_start_date._to_datetime(time_type='start_time')
			event_end_date   = eventdates.last()
			self.event_end_date = event_end_date._to_datetime(time_type='end_time')
			self.save()
		return self.event_start_date, self.event_end_date


	def get_event_date(self):
		"""
		:return <string> "Event Start Date - Event End Date"
		"""
		# eventdates = self.schedule.filter(type='event_date')
		eventdates = EventSchedule.objects.filter(event=self, type='event_date')
		if eventdates.count() == 1:
			date = eventdates.first()
			return date.full_date
		if eventdates.count() >= 2:
			date1 = eventdates.first()
			date2 = eventdates.last()
			if date1.date == date2.date:
				return '%s' % (date1.date.strftime('%B %d, %Y'))
			
			if date1.date.month != date2.date.month:
				return '%s - %s' % (date1.date.strftime('%B %d'), date2.date.strftime('%B %d, %Y'))

			return '%s - %s' % (date1.date.strftime('%B %d'), date2.date.strftime('%d, %Y'))

	def get_direct_ship_dates(self):
		""" 
		Get the direct ship dates from an event's schedule
		"""
		def is_consecutive(datelist):
			"""
			Check for consecutive dates.
			"""
			datelist.sort()
			previousdate = datelist[0]
			for i in range(1, len(datelist)):
				#if (datelist[i] - previousdate).days == 1 or (datelist[i] - previousdate).days == 0:  # for Definition 1
				if (datelist[i] - previousdate).days == 1:    # for Definition 2
					previousdate = datelist[i]
				else:
					previousdate = previousdate + timedelta(days=-1)
			if datelist[-1] == previousdate:
				return True
			else:
				return False	

		eventschedule = self.schedule.filter(type="direct_ship_date").order_by('date', 'start_time')
		# if only 2 direct ship dates
		if eventschedule.count() == 2:
			first_date = eventschedule.first()
			last_date  = eventschedule.last()
			return '%s - %s' % (first_date.date.strftime('%B %d'), last_date.date.strftime('%d, %Y'))
		# if more than two direct ship dates.
		if eventschedule.count() > 2:
			# if dates are consecutive, use a hyphen %d-%d
			if is_consecutive([x.date for x in self.schedule.filter(type="direct_ship_date").order_by('date', 'start_time')]):
				first_date = eventschedule.first()
				last_date  = eventschedule.last()
				return '%s - %s' % (first_date.date.strftime('%B %d'), last_date.date.strftime('%d, %Y'))
			# else list individual dates.
			else:
				result = ''				
				last = eventschedule.count() - 1
				for i, x in enumerate(eventschedule):
					# we only have 1
					if last == 0 :
						result = x.get('date')
					# first item
					elif i == 0:
						result += x.date.strftime('%B %d')
						result += ', '
					elif i == last:
						result += x.date.strftime('%d, %Y')
					else:
						result += x.date.strftime('%d')
						# next item is last
						if (i+1) == last:
							result += ', and '
						else:	
							result += ', '
			return result
		# if only one date, use full date.
		if eventschedule:
			return eventschedule[0].full_date
		return ''
		

	def get_discount_date(self):
		""" 
		Get an event's discount date.
		"""
		discount_date = self.schedule.filter(type='discount_date')
		if discount_date:
			return discount_date.full_date

	def get_event_schedule(self):
		"""
		Get an event's schedule. Primarly used to create the EventSchedule in the mail merge.
		:return [{'EventSchedule.type'}: 'value']
		"""
		# this should go in a ModelManger class or the self...
		eventschedule = self.schedule.all().order_by('date', 'start_time')
		# will need to test order
		results = []
		for date_type, title in EventSchedule.date_types:
			for date in eventschedule.filter(type=date_type):
				row = OrderedDict()
				# Day Month Day Year start end time
				row[date_type] = "%s %s" % (date.full_date, date.start_and_end_time)
				row['%s_note' % date_type] = date.note
				results.append(row)
		return results

	def get_event_schedule2(self):
		"""
		
		"""
		# Should rename this...
		# this should go in a ModelManger class or the self...
		eventschedule = self.schedule.all()
		# will need to test order
		# results = []
		table = OrderedDict()
		for date_type, title in EventSchedule.date_types:
			table[date_type] = []
			for date in eventschedule.filter(type=date_type):
				obj = {}
				# Day Month Day Year start end time
				obj['day_of_week'] = date.day_of_week
				obj['date']        = date.full_date
				obj['start']       = date.start_time_str 
				obj['end']         = date.end_time_str
				obj['note']        = date.note
				# obj['_eventschedule']        = date
				table[date_type].append(obj)
		return table

	@property
	def servicekitstatus_html_color(self):
		GREEN = "#90ee90"
		RED = "#ee9090"
		# there may be a field 
		if (self.servicekitstatus in [
					self.SERVICEKITSTATUS.ae_pulled,
					self.SERVICEKITSTATUS.given_to_ae,
					self.SERVICEKITSTATUS.completed_by_ae,
					self.SERVICEKITSTATUS.proofed_by_exhibitor_services
				]):
			return RED
		
		if (self.servicekitstatus in [
					self.SERVICEKITSTATUS.sent_to_sm,
					self.SERVICEKITSTATUS.approved_goshow, 
					self.SERVICEKITSTATUS.list_received, 
					self.SERVICEKITSTATUS.published]
				):
			return GREEN

		if self.servicekitstatus == self.SERVICEKITSTATUS.expired:
			return None

	@property
	def servicekitstatus_xls_color(self):
		GREEN = "light_green"
		# RED = "red"
		RED = 'light_red'
		# there may be a field 
		if (self.servicekitstatus in [
					self.SERVICEKITSTATUS.ae_pulled,
					self.SERVICEKITSTATUS.given_to_ae,
					self.SERVICEKITSTATUS.completed_by_ae,
					self.SERVICEKITSTATUS.proofed_by_exhibitor_services
				]):
			return RED
		
		if (self.servicekitstatus in [
					self.SERVICEKITSTATUS.sent_to_sm,
					self.SERVICEKITSTATUS.approved_goshow, 
					self.SERVICEKITSTATUS.list_received, 
					self.SERVICEKITSTATUS.published]
				):
			return GREEN
		
		if self.servicekitstatus == self.SERVICEKITSTATUS.expired:
			return None


	@property
	def current_servicekitstatus_update(self):
		status_date = getattr(self, self.servicekitstatus, None)
		if status_date:
			return status_date.strftime('%m/%d/%y %I:%M %p')
		return ''
	
	@property
	def filebrowser_dir_name(self):
		return "%s-%s" % (self.pk, self._filename)

	@property
	def _filename(self):
		"""
		Service Kit file name.
		"""
		# JPOLEDISTSERV-20170404
		event_code = slugify(self.event_name.event_code).upper()
		event_subcode = slugify(self.event_name.event_subcode)
		return "%s-%s" % (event_code, event_subcode)
		
	def get_output_filename(self, file_type='pdf'):
		"""
		Get the filename of created service kit file
		"""
		# modified_timestamp = self.modified_on.strftime("%s")		
		return '%s.%s' % (self._filename, file_type)
	
	def get_pdf(self):
		"""
		Get the service kit pdf.
		"""

		event_name = self._filename
		new_directory_name = "%s-%s" % (self.pk, event_name)
		if not self.output_dir:
			return ''
		return os.path.join(site.storage.location, site.directory, 'kits', new_directory_name, self.get_output_filename())

	def get_pdf_url(self):
		"""
		Get a url to the pdf.
		"""
		pdf_file_object = FileObject(self.get_pdf())
		if self.get_pdf() and pdf_file_object.exists:
			event_name = self._filename
			new_directory_name = "%s-%s" % (self.pk, event_name)
			url = os.path.join(site.directory, 'kits', new_directory_name, self.get_output_filename())
			return url
			# return pdf_file_object.url

	def get_archive_path(self):
		"""
		Get path to archive service kit.
		"""
		if self.output_dir:
			return os.path.join(self.output_dir, 'archive')

@receiver(post_save, sender=EventInfo, dispatch_uid='eventinfo_status_update')
def status_update(sender, instance, **kwargs):
	pass
	# workflow 
	# status == 'approved' and storefrontstatus == 'pending' 
	# then storefrontstatus == 'draft'
	# storefrontstatus == 'published' and status == 'approved' 
	# then status == 'published'
	# else storefrontstatus == 'approved'

class ServiceType(models.Model):
	"""
	Define the main types of service provided in a servicek it.
	Labor, Furniture, Material Handling, ect.
	"""
	title       = models.CharField(max_length=255)
	description = models.TextField(blank=True)	
	
	def __unicode__(self):
		return self.title
	
class ServiceLevel(models.Model):
	"""
	Define the pricelevels available with in a service 
	"""
	title       = models.CharField(max_length=255)
	description = models.TextField(blank=True)		
	type        = models.ForeignKey('ServiceType')

	def __unicode__(self):
		return self.title

class ServiceKit(models.Model):
	"""
	Container for Service Kit Forms.
	"""
	title       = models.CharField(max_length=255)
	description = models.TextField(blank=True)	
	forms       = SortedManyToManyField('ServiceKitForm')

	def __unicode__(self):
		return self.title


# Set ServiceKitForm form_version == 'v1' after merging... 
# Set all exiisting EventInfo to == 'v1'
# ServiceKitForm.objects.all().update(form_version=v1)
# EventInfo.objects.all().update(form_version=v1)
class FormVersion(models.Model):
	title = models.CharField(max_length=255)
	path  = FileBrowseField("Path", max_length=200, directory="documents/forms/", extensions=[""], blank=True, null=True, help_text="Select Version Directory")
	config = JSONField(blank=True, null=True)

	def __unicode__(self):
		return self.title

class ServiceKitForm(models.Model):
	"""
	Defines a form to be used in a ServiceKit document.
	"""
	title       = models.CharField(max_length=255)
	description = models.TextField(blank=True)	
	document    = FileBrowseField("Template", max_length=200, directory="documents/forms/", extensions=[".docx", '.doc', '.pdf'], blank=True, null=True, help_text=".docx files only")
	level        = models.ManyToManyField('ServiceLevel', blank=True)		
	display_order = models.IntegerField(default=10)
	form_version = models.ForeignKey(FormVersion, blank=True, null=True, related_name="service_kit_forms")
	active   = models.BooleanField(default=True)
	
	class Meta:
		ordering = ['display_order', 'title']

	def __unicode__(self):
		return self.title
	
	@property
	def has_form(self):
		if self.document:
			return self.document.exists
		return False

	def get_url(self):
		if settings.MEDIA_ROOT in self.document.path:
			url = self.document.path.split(settings.MEDIA_ROOT)
			url = url[-1]
			if url and url[0] != '/':
				url = "/%s" % (url)
			return url
		return ''

class ServiceKitField(models.Model):
	# currently not used...
	"""Additional Fields for a form"""

	form     = models.ForeignKey(ServiceKitForm, related_name='form_fields')
	title    = models.CharField('VarName', max_length=255)
	label    = models.CharField(blank=True, null=True,  max_length=255)
	required = models.BooleanField(default=False)
	help_text = models.TextField(blank=True)

	def __unicode__(self):
		return self.title

	def save(self, *args, **kwargs):
		if not self.label:
			self.label = pretty_name(self.title)
		super(ServiceKitField, self).save(*args, **kwargs)		

class ServiceKitFieldValue(models.Model):
	# currently not used.
	"""Field values for ServiceKitFields"""
	field = models.ForeignKey(ServiceKitField)
	kit   = models.ForeignKey(ServiceKit, related_name="field_value")
	value = models.CharField('Field Value', max_length=25, blank=True, null=True)
	data  = JSONField('EventData', blank=True, null=True)	
	
	def __unicode__(self):
		return '%s = %s' % (self.field.title, self.value)

from pricelists.models import Pricelist
class ServicePriceListMap(models.Model):
	title    = models.CharField(max_length=255, blank=True, null=True)
	price_list = models.OneToOneField(Pricelist)
	service_level = models.OneToOneField(ServiceLevel)
	
	def __str__(self):
		return "%s to %s" % (self.service_level, self.price_list)

	# def save(self, *args, **kwargs):
	# 	if self.pk == None:
	# 		for price in self.price_list.prices.all():
	# 			price.service_level = self.service_list

	# 	super(ServicePriceListMap, self).save(*args, **kwargs)

# from django.contrib.auth.models import User, Group
# class NotificationGroup(models.Model):
# 	group    = models.ForeignKey('django.auth.Group')
# 	template = models.CharField(max_length=255, blank=True, null=True)
# 	subject  = models.CharField(max_length=255, blank=True, null=True)
# 	STATUS   = Choices('draft', 'review', 'approved', 'published', 'expired')
# 	status   = StatusField()
# 	active   = models.BooleanField(default=False)

# HOW DOES ONE FORMSET...

# class CloudConvertKit(models.Model):
# 	status_choices = [
# 		(0, 'none'),
# 		(1, 'active'),
# 		(2, 'expired'),
# 		(3, 'error'),
# 		(4, 'success')
# 	]
# 	url = models.CharField(max_length=255)	
# 	status = models.IntegerField(choices=status_choices)
# 	data = JSONField('Data', blank=True, null=True)
# 	eventinfo = models.ForeignKey('EventInfo', related_name='cloud_convert_process')
