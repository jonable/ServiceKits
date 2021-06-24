import os
import json
import re

from datetime import datetime, timedelta

from django.template.loader import render_to_string

from kitcreate.models import (
	Place, EventInfo, ServiceKitForm, ServiceType,
	ServiceKit, EventData, EventSchedule, ServiceKitFieldValue
)

class ServiceKitContext(object):
	"""Context object to be sent to the mail merge"""
	def __init__(self, eventinfo):			
			schedule          = eventinfo.get_event_schedule2()
			carrier_pickup    = ''
			advance_ship_date = ''
			direct_ship_date  = ''
			discount_date     = ''
			thirty_days_prior = ''

			if schedule.get('carrier_pickup'):
				carrier_pickup = schedule.get('carrier_pickup')[0]
				carrier_pickup = "%s, %s %s" % (carrier_pickup['day_of_week'], carrier_pickup['date'], carrier_pickup['start'])

			if schedule.get('advance_ship_date'):
				advance_ship_date = schedule.get('advance_ship_date')[0]['date']

			if schedule.get('direct_ship_date'):
				# direct_ship_date = schedule.get('direct_ship_date')[0]['date']
				# last = len(schedule.get('direct_ship_date')) - 1
				# for i, x in enumerate(schedule.get('direct_ship_date')):
				# 	# we only have 1
				# 	if last == 0 :
				# 		direct_ship_date = x.get('date')
				# 	# first item
				# 	elif i == 0 or i != last:
				# 		direct_ship_date += x.get('date')
				# 		direct_ship_date += ', '
				# 	elif i == last:
				# 		direct_ship_date += x.get('date')
				direct_ship_date = eventinfo.get_direct_ship_dates()
				
			if schedule.get('discount_date'):
				discount_date = schedule.get('discount_date')[0]['date']

			if schedule.get('thirty_days_prior'):
				thirty_days_prior = schedule.get('thirty_days_prior')[0]
				thirty_days_prior = thirty_days_prior['date']
			else:
				company_in = eventinfo.schedule.filter(type="company_in").order_by('date').first()
				if company_in and company_in.type == 'company_in' and company_in.date:
					thirty_days_prior = company_in.date - timedelta(30)
					thirty_days_prior = thirty_days_prior.strftime('%B %d, %Y')

			# exhibitor_in = eventinfo.schedule.filter(type="exhibitor_in").order_by('date').first()
			# if not thirty_days_prior and (exhibitor_in and exhibitor_in.date):
			# 	thirty_days_prior = exhibitor_in.date - timedelta(30)
			# 	thirty_days_prior = thirty_days_prior.strftime('%B %d, %Y')				


			self.event_name        = eventinfo.event_name.description
			self.event_header_date = eventinfo.get_event_date()
			self.sales_tax         = eventinfo.sales_tax
			self.booth_info        = eventinfo.booth_info
			self.carpet            = eventinfo.carpet 
			self.notes			   = eventinfo.notes								

			self.carrier_pickup    = carrier_pickup
			self.advance_ship_date = advance_ship_date
			self.direct_ship_date  = direct_ship_date
			
			# only one...
			self.discount          = discount_date
			self.discount_date     = discount_date
			self.discount_deadline = discount_date
			self.thirty_days_prior = thirty_days_prior


			self.exhibitor_in      = schedule.get('exhibitor_in')
			self.exhibitor_out     = schedule.get('exhibitor_out')			
			self.event_date        = schedule.get('event_date')
			
			# this also does dir_wh...
			self.facility          = eventinfo.facility.title
			self.facility_title    = eventinfo.facility.title 			
			self.facility_address1 = eventinfo.facility.address1
			self.facility_address2 = eventinfo.facility.address2
			self.facility_city     = eventinfo.facility.city    
			self.facility_state    = eventinfo.facility.state     
			self.facility_zip      = eventinfo.facility.zip     
			
			# change terminal to adv_wh
			if eventinfo.adv_wh:
				self.terminal_address1 = eventinfo.adv_wh.address1
				self.terminal_address2 = eventinfo.adv_wh.address2
				self.terminal_city     = eventinfo.adv_wh.city
				self.terminal_state    = eventinfo.adv_wh.state
				self.terminal_title    = eventinfo.adv_wh.title
				self.terminal_zip      = eventinfo.adv_wh.zip
			else:
				self.terminal_address1 = ''
				self.terminal_address2 = ''
				self.terminal_city     = ''
				self.terminal_state    = ''
				self.terminal_title    = ''
				self.terminal_zip      = ''
 
		 # 'led_light',
		 # 'led_top_arm',
		 # 'led_upright_base',

		 # 'ser_pl_id',
 
class GSContext(object):
	def __init__(self, eventinfo):
		
		discount_date  = eventinfo.schedule.filter(type='discount_date').order_by('date', 'start_time', 'end_time').first()
		carrier_pickup = eventinfo.schedule.filter(type='carrier_pickup').order_by('date', 'start_time', 'end_time').first()
		exhibitor_in   = eventinfo.schedule.filter(type='exhibitor_in').order_by('date', 'start_time', 'end_time').first()
		exhibitor_out  = eventinfo.schedule.filter(type='exhibitor_out').order_by('date', 'start_time', 'end_time').first()
		event_start    = eventinfo.schedule.filter(type='event_date').order_by('date', 'start_time', 'end_time').first()
		event_end      = eventinfo.schedule.filter(type='event_date').order_by('date', 'start_time', 'end_time').last()

		self.hidwork_statetax = eventinfo.sales_tax
		self.name             = eventinfo.event_name and eventinfo.event_name.description or ''
		self.event_id         = eventinfo.event_name and eventinfo.event_name.event_code or ''
		self.client_name      = eventinfo.event_mgmt and eventinfo.event_mgmt.title or ''                                 
		self.location         = eventinfo.facility and eventinfo.facility.title or ''
		self.terminal         = eventinfo.adv_wh and eventinfo.adv_wh.title or ''                                    
		self.carrier_name     = "1 - SER Logistics"
		self.salesman         = eventinfo.salesperson and eventinfo.salesperson.title or ''
		self.coordinator      = ""                                    
		self.email            = ""                          
		
		date_fmt_1 = '%m-%d-%Y'
		time_fmt_1 = '%H:%M:00'
		time_fmt_2 = '%I:%M %p'
		self.adv_cutoff       = discount_date.date.strftime(date_fmt_1) if discount_date and discount_date.date else ''
		
		self.move_in          = exhibitor_in.date.strftime(date_fmt_1) if exhibitor_in and exhibitor_in.date else ''
		self.move_in_start    = exhibitor_in.start_time.strftime(time_fmt_1) if exhibitor_in and exhibitor_in.start_time else ''
		self.move_in_end      = exhibitor_in.end_time.strftime(time_fmt_1) if exhibitor_in and exhibitor_in.end_time else ''
		
		self.open             = event_start.date.strftime(date_fmt_1) if event_start and event_start.date else ''
		self.close            = event_end.date.strftime(date_fmt_1) if event_end and event_end.date else ''
		
		self.move_out         = exhibitor_out.date.strftime(date_fmt_1) if exhibitor_out and exhibitor_out.date else ''
		self.move_out_start   = exhibitor_out.start_time.strftime(time_fmt_1) if exhibitor_out and exhibitor_out.start_time else ''
		self.move_out_end     = exhibitor_out.end_time.strftime(time_fmt_1) if exhibitor_out and exhibitor_out.end_time else ''
		
		self.vacat_by         = "%s - %s" % ((carrier_pickup.date.strftime('%B %d %Y') if carrier_pickup and carrier_pickup.date else ''), (carrier_pickup.start_time.strftime(time_fmt_2) if carrier_pickup and carrier_pickup.start_time else ''))


		# POSSIBLE ISSUE
		parsed_tax = re.findall(r"[-+]?\d*\.\d+|\d+", eventinfo.sales_tax)
		if parsed_tax:
			sales_tax = parsed_tax[0]
		else:
			sales_tax = ''
		self.tax1             = sales_tax
		self.booth_size1      = ""                                       
		self.booth_size2      = ""                                       

		self.web_order_cutoff        = self.adv_cutoff
				
		self.pulloutdisplay          = "0"
		self.widget_title            = "."
		
		context = {}
		context['eventinfo'] = eventinfo
		context['sk'] = ServiceKitContext(eventinfo).__dict__

		context['no_direct_shipments'] = False
		material_handling_type = ServiceType.objects.filter(title="MaterialHandling").first()
		if material_handling_type and eventinfo.service_kit:
			for form in eventinfo.service_kit.forms.filter(level__type=material_handling_type):
				if 'adv' in form.title.lower():
					context['no_direct_shipments'] = True	
					break

		self.important_title       = 'Event Information'
		self.important_title_notes = render_to_string('kitcreate/snippets/event_notes.html', context)
		
		self.move_in_notes           = render_to_string('kitcreate/snippets/move_in_notes.html', context)
		self.move_out_notes          = render_to_string('kitcreate/snippets/move_out_notes.html', context)
		self.show_hours_notes        = render_to_string('kitcreate/snippets/show_hours_notes.html', context)
		self.ordering_deadline_notes = render_to_string('kitcreate/snippets/ordering_deadline_notes.html', context)
		
		self.shipping_details        = render_to_string('kitcreate/snippets/shipping_details.html', context)
		
		self._facility = {}
		self._facility['company']       = eventinfo.facility and eventinfo.facility.title or ''
		self._facility['client']        = eventinfo.facility and eventinfo.facility.title or '' 			
		self._facility['bill_address']  = eventinfo.facility and eventinfo.facility.address1 or ''
		self._facility['bill_address1'] = eventinfo.facility and eventinfo.facility.address2 or ''
		self._facility['bill_city']     = eventinfo.facility and eventinfo.facility.city or ''    
		self._facility['state']         = eventinfo.facility and eventinfo.facility.state or ''     
		self._facility['bill_pincode']  = eventinfo.facility and eventinfo.facility.zip or ''    
		self._facility['cl_type']        = 'Conv. Center'
		self._facility['mail_status']   = True
		
		self._event_mgmt = {}
		self._event_mgmt['company']       = eventinfo.event_mgmt and eventinfo.event_mgmt.title or ''
		self._event_mgmt['client']        = eventinfo.event_mgmt and eventinfo.event_mgmt.code or ''
		self._event_mgmt['bill_address']  = eventinfo.event_mgmt and eventinfo.event_mgmt.address1 or ''
		self._event_mgmt['bill_address1'] = eventinfo.event_mgmt and eventinfo.event_mgmt.address2 or ''
		self._event_mgmt['bill_city']     = eventinfo.event_mgmt and eventinfo.event_mgmt.city or ''
		self._event_mgmt['state']         = eventinfo.event_mgmt and eventinfo.event_mgmt.state or ''
		self._event_mgmt['bill_pincode']  = eventinfo.event_mgmt and eventinfo.event_mgmt.zip or ''
		self._event_mgmt['mail_status']   = True

		self._adv_wh = {}
		self._adv_wh['company']       = eventinfo.adv_wh and eventinfo.adv_wh.title or ''
		self._adv_wh['client']        = eventinfo.adv_wh and eventinfo.adv_wh.code or ''
		self._adv_wh['bill_address']  = eventinfo.adv_wh and eventinfo.adv_wh.address1 or ''
		self._adv_wh['bill_address1'] = eventinfo.adv_wh and eventinfo.adv_wh.address2 or ''
		self._adv_wh['bill_city']     = eventinfo.adv_wh and eventinfo.adv_wh.city or ''
		self._adv_wh['state']         = eventinfo.adv_wh and eventinfo.adv_wh.state or ''
		self._adv_wh['bill_pincode']  = eventinfo.adv_wh and eventinfo.adv_wh.zip or ''
		self._adv_wh['cl_type']     = 'Terminal'
		self._adv_wh['mail_status']   = True		

	def to_json(self):
		return json.dumps(self.__dict__)