"""
This module was used to generate labor forms
ADV-ST (+0%)
ADV-OT (+50%)
ADV-DT (+100%)
FL-ST (+30%)
FL-OT (+95%)
FL-DT (+160%)

"""
import os, sys
from collections import OrderedDict
from mailmerge import MailMerge
from filebrowser.sites import site

import logging
logger = logging.getLogger('django')

os.path.join(site.storage.location, site.directory)
forms_dir = os.path.join(base_dir, 'documents/forms')
templates_dir = os.path.join(base_dir, 'documents/templates')
OUTPUT_DIR = os.path.join(forms_dir, 'labor')

sys.path.append(os.path.join(os.path.expanduser('~'), 'Projects', 'utilities'))
from csv_to_xls import open_workbook, xls_to_dict
PRICING_DATA_WORKBOOK  = os.path.join(templates_dir, '_data/labor_rates.xls')

LABOR_BASE_PRICES = []
try:
	workbook = open_workbook(PRICING_DATA_WORKBOOK)
	_labor_rate_sheet = xls_to_dict(workbook.sheet_by_name('rates'))
	LABOR_BASE_PRICES = [float(x['rate']) for x in _labor_rate_sheet]
	
except Exception, e:
	logger.error("Couldn't get labor rates %s" % e)
	LABOR_BASE_PRICES = [75, 80, 85, 152, 125, 180.25, 204.75, 98.00]

# LABOR_BASE_PRICES = [75, 80, 85, 152, 125, 180.25, 204.75]	

TEMPLATE_FILES = {
	"booth_labor": os.path.join(templates_dir, "labor", "booth_labor.docx"),
	"forklift": os.path.join(templates_dir, "labor", "forklift.docx"),
	"porter": os.path.join(templates_dir, "labor", "porter.docx"),
}


fake_event_info = {
	'event_header_date': 'Feb 10-12, 2017',
	'discount_date': "Feb 01, 2017",
	'event_name': 'Fake Event Expo 2017',
	'facility': 'DCU Center',
	'facility_title': 'DCU Center',
	'facility_address1': 'Major Taylor Blvd',
	'facility_address2': '',
	'facility_city': 'Worcester',
	'facility_state': 'MA',
	'facility_zip': '01605',
	'sales_tax': 'MA 6.25%',
	# 'ser_pl_id': 'SERPL118',

	'advance_ship_date': "Feb 01, 2017",
	'direct_ship_date': "Feb 10, 2017",
	'terminal_address1': "35B New Street",
	'terminal_address2': "",
	'terminal_city': "Worcester",
	'terminal_state': "MA",
	'terminal_title': "SER exposition services",
	'terminal_zip': "01605"
 }

# the below explains how SER handles MH pricing
LABOR_PRICE_RULES = {
	'adv_st_rate': 0.0,
	'adv_ot_rate': .50,
	'adv_dt_rate': 1.00,
	'std_st_rate': 0.30,
	'std_ot_rate': 0.95,
	'std_dt_rate': 1.60
}


ignorefields = (
	'discount_date',
	'event_header_date',
	'event_name',
	'facility',
	'facility_city',
	'facility_state',
	'sales_tax',
	'thirty_days_prior'
)


def round_price(price):	
	if type(price) == float:
		price = "%.2f" % round(price, 2)
	else:
		price = 'N/A'
	return price

def convert(base_rate):
	result = OrderedDict()
	for key, percent in LABOR_PRICE_RULES.items():		
		result[key] = "%.2f" % round(base_rate * (1+percent), 2)
	return result

def get_merge_data(base_labor_prices):
	results = {}
	for rate in base_labor_prices:
		results[rate] = []
		results[rate] = convert(rate)
	return results

def merge_labor_form(data, template_filename, output_filename, context=None):		
	doc = MailMerge(template_filename, ignorefields=ignorefields)
	doc.merge(**data)
	if context:
		doc.merge(**context)
	doc.write(output_filename)
	return doc

def merge_remaining_forms(forms_list, context=None):
	for form in forms_list:
		doc = MailMerge(os.path.join(templates_dir, 'labor', '%s.docx' % (form)), ignorefields=ignorefields)
		if context:
			doc.merge(**context)
		doc.write(os.path.join(OUTPUT_DIR, '%s.docx' % (form)))

def _merge_labor_form(labor_type, template_path):
	if not os.path.exists(OUTPUT_DIR):
		os.makedirs(OUTPUT_DIR)

	labor_data = get_merge_data(LABOR_BASE_PRICES)
	for level, data in labor_data.items():
		context = {}
		context['ser_pl_id'] = "SER%s" % (level)
		merge_labor_form(
			data, 
			template_path, 
			os.path.join(OUTPUT_DIR, '%s_%s.docx' % (labor_type, level)), 
			context
		)	


def run():

	if not os.path.exists(OUTPUT_DIR):
		os.makedirs(OUTPUT_DIR)

	labor_data = get_merge_data(LABOR_BASE_PRICES)
	for level, data in labor_data.items():
		context = {}
		context['ser_pl_id'] = "SER%s" % (level)
		for labor_type, TEMPLATE_FILE in TEMPLATE_FILES.items():
			merge_labor_form(
				data, 
				TEMPLATE_FILE, 
				os.path.join(OUTPUT_DIR, '%s_%s.docx' % (labor_type, level)), 
				context
			)

	merge_remaining_forms(["booth_cleaning", "banner_hanging", "non_official_service_contractor"])
# def get_merge_data(data, base_mh_prices):

# 	results = {}
# 	for pl in base_mh_prices:
# 		adv = pl[0]
# 		direct = pl[1]
# 		results[adv] = []
# 		for row in data:
# 			# mh_type = row.get('mh_type')
# 			obj = {}
# 			for field_title, percent in row.items():
# 				val = None
# 				if field_title == 'mh_type':
# 					obj[field_title] = percent
# 					continue
# 				if 'adv' in field_title:
# 					val = adv 
# 				if 'dir' in field_title:
# 					val = direct 
				
# 				if 'min' in field_title:
# 					obj[field_title] = str(round(((val * (1+percent))*2),2))
# 				else:
# 					obj[field_title] = str(round((val * (1+percent)),2))
# 			results[adv].append(obj)
# 	return results
