"""
Convert EventPath dates into dates useable in ServiceKit app.
"""
from datetime import datetime

DATE_FORMAT_1 = "%Y%m%d"
DATE_FORMAT_2 = "%m/%d/%Y"
TIME_FORMAT_1 = "%I:%M %p"
TIME_FORMAT_2 = "%I:%M%p"

LOCAL_FIELD_COMPANY_IN        = "company_in"
LOCAL_FIELD_COMPANY_OUT       = "company_out"
LOCAL_FIELD_EXHIBITOR_IN      = "exhibitor_in"
LOCAL_FIELD_EXHIBITOR_OUT     = "exhibitor_out"
LOCAL_FIELD_EVENT_DATE        = "event_date"
LOCAL_FIELD_DISCOUNT_DATE     = "discount_date"
LOCAL_FIELD_CARRIER_PICKUP    = "carrier_pickup"
LOCAL_FIELD_ADVANCE_SHIP_DATE = "advance_ship_date"
LOCAL_FIELD_DIRECT_SHIP_DATE  = "direct_ship_date"

LOCAL_FIELDS = [
	LOCAL_FIELD_COMPANY_IN,
	LOCAL_FIELD_EXHIBITOR_IN,
	LOCAL_FIELD_EVENT_DATE,
	LOCAL_FIELD_EXHIBITOR_OUT,
	LOCAL_FIELD_COMPANY_OUT,
	
	LOCAL_FIELD_DISCOUNT_DATE,
	LOCAL_FIELD_CARRIER_PICKUP,
	LOCAL_FIELD_ADVANCE_SHIP_DATE,
	LOCAL_FIELD_DIRECT_SHIP_DATE,
]

EP_DATE_FIELDS = [
	{
		'ep_field': 'CompanyBDownEndDate',
		'_group': 'CompanyBDown',
		'local_field': LOCAL_FIELD_COMPANY_OUT,
		'field_type': 'date',
		'format': DATE_FORMAT_1,
		'value': '',
	},
	{
		'ep_field': 'CompanyBDownEndTime',
		'_group': 'CompanyBDown',
		'local_field': LOCAL_FIELD_COMPANY_OUT,
		'field_type': 'end_time',
		'format': [TIME_FORMAT_1,TIME_FORMAT_2],
		'value': '',
	},
	{
		'ep_field': 'CompanyBDownStartDate',
		'_group': 'CompanyBDown',
		'local_field': LOCAL_FIELD_COMPANY_OUT,
		'field_type': 'date',
		'format': DATE_FORMAT_1,
		'value': '',
	},
	{
		'ep_field': 'CompanyBDownStartTime',
		'_group': 'CompanyBDown',
		'local_field': LOCAL_FIELD_COMPANY_OUT,
		'field_type': 'start_time',
		'format': [TIME_FORMAT_1,TIME_FORMAT_2],
		'value': '',
	},
	{
		'ep_field': 'CompanySetupEndDate',
		'_group': 'CompanySetup',
		'local_field': LOCAL_FIELD_COMPANY_IN,
		'field_type': 'date',
		'format': DATE_FORMAT_1,
		'value': '',
	},
	{
		'ep_field': 'CompanySetupEndTime',
		'_group': 'CompanySetup',
		'local_field': LOCAL_FIELD_COMPANY_IN,
		'field_type': 'end_time',
		'format': [TIME_FORMAT_1,TIME_FORMAT_2],
		'value': '',
	},
	{
		'ep_field': 'CompanySetupStartDate',
		'_group': 'CompanySetup',
		'local_field': LOCAL_FIELD_COMPANY_IN,
		'field_type': 'date',
		'format': DATE_FORMAT_1,
		'value': '',
	},
	{
		'ep_field': 'CompanySetupStartTime',
		'_group': 'CompanySetup',
		'local_field': LOCAL_FIELD_COMPANY_IN,
		'field_type': 'start_time',
		'format': [TIME_FORMAT_1,TIME_FORMAT_2],
		'value': '',
	},
	{
		'ep_field': 'DiscountCutoffDate',
		'_group': 'DiscountCutoffDate',
		'local_field': LOCAL_FIELD_DISCOUNT_DATE,
		'field_type': 'date',
		'format': DATE_FORMAT_1,
		'value': '',
	},
	{
		'ep_field': 'EventEndDate',
		'_group': 'EventEnd',
		'local_field': LOCAL_FIELD_EVENT_DATE,
		'field_type': 'date',
		'format': DATE_FORMAT_1,
		'value': '',
	},
	{
		'ep_field': 'EventEndTime',
		'_group': 'EventEnd',
		'local_field': LOCAL_FIELD_EVENT_DATE,
		'field_type': 'end_time',
		'format': [TIME_FORMAT_1,TIME_FORMAT_2],
		'value': '',
	},
	# {
	# 	'ep_field': 'EventSDate',
	# 	'local_field': LOCAL_FIELD_EVENT_DATE,
	# 	'field_type': 'date',
	# 	'format': DATE_FORMAT_2,
	#    'value': '',
	# },
	{
		'ep_field': 'EventStartDate',
		'_group': 'EventStart',
		'local_field': LOCAL_FIELD_EVENT_DATE,
		'field_type': 'date',
		'format': DATE_FORMAT_1,
		'value': '',
	},
	{
		'ep_field': 'EventStartTime',
		'_group': 'EventStart',
		'local_field': LOCAL_FIELD_EVENT_DATE,
		'field_type': 'start_time',
		'format': [TIME_FORMAT_1,TIME_FORMAT_2],
		'value': '',
	},
	{
		'ep_field': 'ExhibitorBDownEndDate',
		'_group': 'ExhibitorBDown',
		'local_field': LOCAL_FIELD_EXHIBITOR_OUT,
		'field_type': 'date',
		'format': DATE_FORMAT_1,
		'value': '',
	},
	{
		'ep_field': 'ExhibitorBDownEndTime',
		'_group': 'ExhibitorBDown',
		'local_field': LOCAL_FIELD_EXHIBITOR_OUT,
		'field_type': 'end_time',
		'format': [TIME_FORMAT_1,TIME_FORMAT_2],
		'value': '',
	},
	{
		'ep_field': 'ExhibitorBDownStartDate',
		'_group': 'ExhibitorBDown',
		'local_field': LOCAL_FIELD_EXHIBITOR_OUT,
		'field_type': 'date',
		'format': DATE_FORMAT_1,
		'value': '',
	},
	{
		'ep_field': 'ExhibitorBDownStartTime',
		'_group': 'ExhibitorBDown',
		'local_field': LOCAL_FIELD_EXHIBITOR_OUT,
		'field_type': 'start_time',
		'format': [TIME_FORMAT_1,TIME_FORMAT_2],
		'value': '',
	},
	{
		'ep_field': 'ExhibitorSetupEndDate',
		'_group': 'ExhibitorSetup',
		'local_field': LOCAL_FIELD_EXHIBITOR_IN,
		'field_type': 'date',
		'format': DATE_FORMAT_1,
		'value': '',
	},
	{
		'ep_field': 'ExhibitorSetupEndTime',
		'_group': 'ExhibitorSetup',
		'local_field': LOCAL_FIELD_EXHIBITOR_IN,
		'field_type': 'end_time',
		'format': [TIME_FORMAT_1,TIME_FORMAT_2],
		'value': '',
	},
	{
		'ep_field': 'ExhibitorSetupStartDate',
		'_group': 'ExhibitorSetup',
		'local_field': LOCAL_FIELD_EXHIBITOR_IN,
		'field_type': 'date',
		'format': DATE_FORMAT_1,
		'value': '',
	},
	{
		'ep_field': 'ExhibitorSetupStartTime',
		'_group': 'ExhibitorSetup',
		'local_field': LOCAL_FIELD_EXHIBITOR_IN,
		'field_type': 'start_time',
		'format': [TIME_FORMAT_1,TIME_FORMAT_2],
		'value': '',
	}
]


# datetime.strptime('03:00 PM', '%I:%M %p').time()

TEST_DATA = {
	u'CompanyBDownEndDate': u'20170305',
	u'CompanyBDownEndTime': u'04:00 PM',
	u'CompanyBDownStartDate': u'20170305',
	u'CompanyBDownStartTime': u'04:00 PM',
	u'CompanySetupEndDate': u'20170301',
	u'CompanySetupEndTime': u'06:00 PM',
	u'CompanySetupStartDate': u'20170301',
	u'CompanySetupStartTime': u'07:00 AM',
	u'DiscountCutoffDate': u'',
	u'EventEndDate': u'20170305',
	u'EventEndTime': u'04:00 PM',
	u'EventSDate': u'03/03/2017',
	u'EventStartDate': u'20170303',
	u'EventStartTime': u'02:00 PM',
	u'ExhibitorBDownEndDate': u'20170305',
	u'ExhibitorBDownEndTime': u'12:00 PM',
	u'ExhibitorBDownStartDate': u'20170305',
	u'ExhibitorBDownStartTime': u'04:00 PM',
	u'ExhibitorSetupEndDate': u'20170303',
	u'ExhibitorSetupEndTime': u'01:00 PM',
	u'ExhibitorSetupStartDate': u'20170301',
	u'ExhibitorSetupStartTime': u'01:00 PM'
}


def try_format(value, formats):
	for format in formats:
		try:
			return datetime.strptime(value, format)
		except ValueError:
			pass            
	raise ValueError('No valid date format found for: "%s"' % (value))

import logging
logger = logging.getLogger('django')

def convert_date(map_obj):
	value      = map_obj.get('value')
	format     = map_obj.get('format')
	field_type = map_obj.get('field_type')
	dt = None
	
	if not value:
		return None
	try:
		if type(format) == list:
			dt = try_format(value, format)
		else:
			dt = datetime.strptime(value, format)
	except Exception, e:
		logger.error(e)
		return None

	if field_type in ['start_time', 'end_time']:
		return dt.time()
	return dt

from copy import deepcopy
def get_mapped_dates(event_data):
	"""
	:event_date JSON data of an eventpath Event table dump
	:returns [
		{
		'ep_field': EventPath Field,
		'_group': EventPath Field Group,
		'local_field': Local Application Field Name,
		'field_type': Type of field (date or time),
		'format': python datetime format to use to parse value ,
		'value': '',
	},]
	"""
	ep_date_fields = deepcopy(EP_DATE_FIELDS)
	for key, value in event_data.items():
		for map_obj in ep_date_fields:
			if key == map_obj.get('ep_field'):
				map_obj['value'] = value
				dt = convert_date(map_obj)
				map_obj['datetime_obj'] = dt
	return ep_date_fields

def get_eventschedule(mapped_objs):
	"""
	Converts get_mapped_dates results into a format able to be consumed by kitcreate.models.EventSchedule.	
	:mapped_objs [list] results of get_mapped_dates
	"""
	results = []
	group_dates = {}
	for map_obj in mapped_objs:
		_group = map_obj['_group']
		if not group_dates.has_key(_group):
			group_dates[_group] = []
		group_dates[_group].append(map_obj)

	for group, mapped_objs in group_dates.items():
		obj = {}
		for map_obj in mapped_objs:
			local_field     = map_obj['local_field']
			datetime_obj    = map_obj['datetime_obj']
			field_type      = map_obj['field_type']			
			obj['type']     = local_field
			obj[field_type] = datetime_obj
		if obj.get('date') or obj.get('start_time') or obj.get('end_time'):
			results.append(obj)
	
	return sorted(results, key=lambda x: LOCAL_FIELDS.index(x['type']))
	








