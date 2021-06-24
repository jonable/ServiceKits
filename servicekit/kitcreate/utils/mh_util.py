"""
This module was used to generate material handling forms

[
	{
		"rows":[
			{
				"adv_price":
				"std_price"
				"description"
			},{...}
		],
		"heading": "",
		"note": ""
	}
]

"""
import sys, os
from collections import OrderedDict

sys.path.append(os.path.join(os.path.expanduser('~'), 'Projects', 'utilities'))
from kitcreate.mail_merge_utils import merge_std_furn_form
from filebrowser.sites import site

import logging
logger = logging.getLogger('django')

base_dir  = os.path.abspath(site.directory)
forms_dir = os.path.join(base_dir, 'documents/forms')
templates_dir = os.path.join(base_dir, 'documents', 'templates')

TEMPLATE_FILE = os.path.join(templates_dir, 'material_handling', 'material_handling.docx')
TEMPLATE_FILE_ADV_ONLY = os.path.join(templates_dir, 'material_handling', 'material_handling_adv_only.docx')
OUTPUT_DIR = os.path.join(forms_dir, 'material_handling')


sys.path.append(os.path.join(os.path.expanduser('~'), 'Projects', 'utilities'))
from csv_to_xls import open_workbook, xls_to_dict
PRICING_DATA_WORKBOOK  = os.path.join(templates_dir, '_data/mh_rates.xls')

MH_BASE_PRICES = []
try:
	workbook = open_workbook(PRICING_DATA_WORKBOOK)
	_labor_rate_sheet = xls_to_dict(workbook.sheet_by_name('rates'))
	MH_BASE_PRICES = [(float(x['adv_rate']), float(x['dir_rate'])) for x in _labor_rate_sheet]
except Exception, e:
	logger.error("Couldn't get MH rates %s" % e)
	MH_BASE_PRICES = [
		[69,65],
		[72,69],
		[85,82],
		[131,125],
		[74,71],
		[91,88],
		[137,131],
		[157.44,157.44]
	]

# MH_BASE_PRICES = [
# 	[69,65],
# 	[72,69],
# 	[85,82],
# 	[131,125],
# 	[74,71],
# 	[91,88],
# 	[137,131],
# 	[157.44,157.44]
# ]	
# the below explains how SER handles MH pricing
MH_PRICING_RULES = [{
		"mh_type": 'ST/ST',
		"mh_adv_std": 0.00,
		# "mh_adv_std_min": 0.00,
		"mh_adv_sh": 0.30,
		# "mh_adv_sh_min": 0.00,
		"mh_dir_std": 0.00,
		# "mh_dir_std_min": 0.00,
		"mh_dir_sh": 0.30,
		# "mh_dir_sh_min": 0.00,
	},{
		"mh_type": 'ST/OT',
		"mh_adv_std": 0.30,
		# "mh_adv_std_min": 0.00,
		"mh_adv_sh": 0.60,
		# "mh_adv_sh_min": 0.00,
		"mh_dir_std": 0.30,
		# "mh_dir_std_min": 0.00,
		"mh_dir_sh": 0.60,
		# "mh_dir_sh_min": 0.00,
	
	},{
		"mh_type": 'OT/OT',
		"mh_adv_std": 0.60,
		# "mh_adv_std_min": 0.00,
		"mh_adv_sh": 0.90,
		# "mh_adv_sh_min": 0.00,
		"mh_dir_std": 0.60,
		# "mh_dir_std_min": 0.00,
		"mh_dir_sh": 0.90,
		# "mh_dir_sh_min": 0.00,
	}
]

def round_price(price):	
	if type(price) == float:
		price = "%.2f" % round(price, 2)
	else:
		price = 'N/A'
	return price

def convert(adv, direct):
	"""
	Creates the material handling rates
	to be merged with the material handling form
	Example results
	[{
		'mh_adv_sh': '89.70',
		'mh_adv_sh_min': '179.40',
		'mh_adv_std': '69.00',
		'mh_adv_std_min': '138.00',
		'mh_dir_sh': '84.50',
		'mh_dir_sh_min': '169.00',
		'mh_dir_std': '65.00',
		'mh_dir_std_min': '130.00',
		'mh_type': 'ST/ST'
	}]
	:adv <float> advance rate to use 
	:direct <float> direct rate to use 
	:return [{}]
	"""
	results = []
	for row in MH_PRICING_RULES:
		obj = {}
		for field_title, percent in row.items():
			val = None
			if field_title == 'mh_type':
				obj[field_title] = percent
				continue
			if 'adv' in field_title:
				val = adv 
			if 'dir' in field_title:
				val = direct 
			
			val = round((val * (1+percent)),2)

			obj[field_title] = "%.2f" % val 
			obj["%s_min"%field_title] = "%.2f" % (val*2)

		results.append(obj)
	return results

def get_merge_data(base_mh_prices):
	results = {}
	for pl in base_mh_prices:
		adv = pl[0]
		direct = pl[1]
		results[adv] = []
		results[adv] = convert(adv, direct)
	return results


from mailmerge import MailMerge

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


ignorefields = (
	'advance_ship_date',
	'direct_ship_date',
	'discount_date',
	'event_header_date',
	'event_name',
	'facility',
	'facility_address1',
	'facility_address2',
	'facility_city',
	'facility_state',
	'facility_title',
	'facility_zip',
	'terminal_address1',
	'terminal_address2',
	'terminal_city',
	'terminal_state',
	'terminal_title',
	'terminal_zip',
	'thirty_days_prior'
)

def get_smallship_rate(data):
	data[0]['mh_dir_std']
	for x in data:
		if x['mh_type'] == 'ST/ST':
			return x['mh_dir_std'], x['mh_dir_std']
	return "0.00"

def merge_mh_form(data, template_filename, output_filename, context=None):		
	mh_smallship_adv, mh_smallship_dir = get_smallship_rate(data)
	doc = MailMerge(template_filename, ignorefields=ignorefields)
	# doc.merge_rows('mh_type', data)
	doc.merge_rows('mh_adv', data)
	doc.merge_rows('mh_dir', data)	
	doc.merge(**{'mh_smallship_adv': mh_smallship_adv, 'mh_smallship_dir': mh_smallship_dir})	
	if context:
		doc.merge(**context)
	# doc.merge(**fake_event_info)
	doc.write(output_filename)
	return doc

def run():

	if not os.path.exists(OUTPUT_DIR):
		os.makedirs(OUTPUT_DIR)
	mh_data = get_merge_data(MH_BASE_PRICES)
	for level, data in mh_data.items():
		context = {}
		context['ser_pl_id'] = "SER%s" % (level)
		larp = merge_mh_form(data, TEMPLATE_FILE, os.path.join(OUTPUT_DIR, 'MH_%s.docx' % (level)), context)
		darp = merge_mh_form(data, TEMPLATE_FILE_ADV_ONLY, os.path.join(OUTPUT_DIR, 'MH_ADV_ONLY_%s.docx' % (level)), context)
	return larp

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