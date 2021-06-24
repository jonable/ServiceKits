"""
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

from copy import deepcopy
from mailmerge import MailMerge
from filebrowser.sites import site
 
sys.path.append(os.path.join(os.path.expanduser('~'), 'Projects', 'utilities'))
from csv_to_xls import open_workbook, xls_to_dict

# from kitcreate.mail_merge_utils import merge_std_furn_form

os.path.join(site.storage.location, site.directory)
forms_dir = os.path.join(base_dir, 'documents', 'forms')
templates_dir = os.path.join(base_dir, 'documents', 'templates')

STD_FURN_TEMPLATE = os.path.join(templates_dir, 'furn', 'standard_furniture_form.docx')
OUTPUT_DIR    = os.path.join(forms_dir, 'furn')
PRICING_DATA  = os.path.join(templates_dir, '_data/std_furn_prices.xls')

LED_TEMPLATE = os.path.join(templates_dir, 'furn', 'led_lights.docx')


def run_for_sheet(sheet_name):
	if not os.path.exists(OUTPUT_DIR):
		os.makedirs(OUTPUT_DIR)	

	workbook = open_workbook(PRICING_DATA)
	
	try:
		sheet_names = workbook.sheet_by_name(sheet_name)
	except Exception, e:
		raise e
	
	headings = xls_to_dict(workbook.sheet_by_name('headings'))

	
	pricing = xls_to_dict(workbook.sheet_by_name(sheet_name))
	data = convert(headings, pricing)
	context = {}
	context['ser_pl_id'] = "SER%s" % (sheet_name)
	merge_std_furn_form(data, STD_FURN_TEMPLATE, os.path.join(OUTPUT_DIR, 'STD_FURN_%s.docx' % (sheet_name)), context)


def run():		
	print "JONATHAN don't forget to overwrite modular/gridwal/graphcs/ect forms in forms/furn dir"
	if not os.path.exists(OUTPUT_DIR):
		os.makedirs(OUTPUT_DIR)

	workbook = open_workbook(PRICING_DATA)
	sheet_names = workbook.sheet_names()
	sheet_names.pop(sheet_names.index('headings'))
	headings = xls_to_dict(workbook.sheet_by_name('headings'))

	for sheet_name in sheet_names:
		pricing = xls_to_dict(workbook.sheet_by_name(sheet_name))
		data = convert(headings, pricing)
		context = {}
		context['ser_pl_id'] = "SER%s" % (sheet_name)
		merge_std_furn_form(data, STD_FURN_TEMPLATE, os.path.join(OUTPUT_DIR, 'STD_FURN_%s.docx' % (sheet_name)), context)

	for sheet_name in sheet_names:
		pricing = xls_to_dict(workbook.sheet_by_name(sheet_name))
		context = {}
		context['ser_pl_id'] = "SER%s" % (sheet_name)
		merge_ledlight_form(pricing, LED_TEMPLATE, os.path.join(OUTPUT_DIR, 'LED_LIGHTS_%s.docx' % (sheet_name)), context)

	context = {}
	extra_forms_list = [
		"booth_equipment_special",
		"computer_kiosk",
		"graphics",
		"gridwall",
		"modular_rental",
		"showcases",
		'counters',
		'floral',
		'gondolas'
	]
	merge_remaining_forms(extra_forms_list, context=context)



def convert(headings, data):
	"convert data in pricelevel.xls to the above data structure"
	results = OrderedDict()

	for row in data:
		for header in headings:			
			if header['Item'] == row['Item']:

				if not row.get('Advance'):
					continue
				category = header['Category']
				if not results.has_key(header['Category']):
					results[category] = {}
					results[category]['rows'] = []
					results[category]['note'] = ''
					results[category]['heading'] = category
				if header.get('Note'):
					results[category]['note'] = header.get('Note')					
				temp = {}
				adv_price = row.get('Advance', 0.00)
				std_price = row.get('Regular', 0.00)
				if type(adv_price) == float:
					adv_price = "%.2f" % round(adv_price, 2)
				else:
					adv_price = 'N/A'
				
				if type(std_price) == float:
					std_price = "%.2f" % round(std_price, 2)
				else:
					std_price = 'N/A'
				
				unit = header.get('Unit', '')
				if unit:				
					adv_price = "%s %s" % (adv_price, unit)
					std_price = "%s %s" % (std_price, unit)

				temp['adv_price'] = adv_price 
				temp['std_price'] = std_price
				temp['description'] = row.get('Item')				

				results[category]['rows'].append(temp)

		results[category]['rows']

	return results.values()

 
fake_event_info = {
	'event_header_date': 'Feb 10-12, 2017',
	'discount_date': "Feb 01, 2017",
	'event_name': 'Fake Event Expo 2017',
	'facility': 'DCU Center',
	'facility_city': 'Worcester',
	'facility_state': 'MA',
	'sales_tax': 'MA 6.25%',
	# 'ser_pl_id': 'SERPL118',
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

def merge_remaining_forms(forms_list, context=None):
	for form in forms_list:
		doc = MailMerge(os.path.join(templates_dir, 'furn', '%s.docx' % (form)), ignorefields=ignorefields)
		if context:
			doc.merge(**context)
		doc.write(os.path.join(OUTPUT_DIR, '%s.docx' % (form)))


# USE merge_rows2 to MERGE STANDARD_FURN_FORMS
def merge_std_furn_form(data, template_filename, output_filename, context=None, open=False):
	"""furn form"""

	doc = MailMerge(template_filename, ignorefields=ignorefields)
	merge_rows2(doc, 'furn_category', data)
	if context:
		doc.merge(**context)
	doc.write(output_filename)
	if open:
		os.system("open "+output_filename)
	return doc

def merge_ledlight_form(data, template_filename, output_filename, context=None, open=False):
	# "LED Lamp with clamp"
	# at ${{led_light_adveach
	# at ${{led_light_stdeach
	# at ${{led_upright_base_adv each
	# at ${{led_upright_base_std each
	# at ${{led_top_arm_adv each
	# at ${{led_top_arm_std each
# USE merge_rows2 to MERGE STANDARD_FURN_FORMS
	derp = {}
	for row in data:
		adv_price = row.get('Advance', 0.00)
		std_price = row.get('Regular', 0.00)
		if type(adv_price) == float:
			adv_price = "%.2f" % round(adv_price, 2)
		else:
			adv_price = 'N/A'
		
		if type(std_price) == float:
			std_price = "%.2f" % round(std_price, 2)
		else:
			std_price = 'N/A'

		if '8\' High Upright' in row['Item']:
			derp['led_upright_base_adv'] = adv_price
			derp['led_upright_base_std'] = std_price
		if 'Top Arms' in row['Item']:
			derp['led_top_arm_adv'] = adv_price
			derp['led_top_arm_std'] = std_price
		if 'LED Lamp' in row['Item']:
			derp['led_light_adv'] = adv_price
			derp['led_light_std'] = std_price
	doc = MailMerge(template_filename, ignorefields=ignorefields)
	doc.merge(**derp)
	if context:
		doc.merge(**context)
	doc.write(output_filename)
	return doc
# 
def merge_rows2(doc, anchor, tables):
	table, idx, template = doc._MailMerge__find_row_anchor(anchor)
	# headings_template = table[3]
	table2, idx2, template2 = doc._MailMerge__find_row_anchor('description')
	table3, idx3, template3 = doc._MailMerge__find_row_anchor('furn_category_note')
	
	if table is not None and len(tables) > 0:
		del table[idx3]
		del table[idx2]
		# del table[3]
		del table[idx]

		count = idx
		for tbl in tables:
			rows = tbl['rows']
			row = deepcopy(template)
			doc.merge([row], furn_category=tbl['heading'])
			table.insert(count, row)			
			count += 1
			# table.insert(count, deepcopy(headings_template))
			# count += 1
			for row_data in rows:
				row = deepcopy(template2)
				doc.merge([row], **row_data)
				table.insert(count, row)
				count +=1
			if tbl.get('note'):
				row = deepcopy(template3)
				doc.merge([row], furn_category_note=tbl.get('note'))
				table.insert(count, row)
				count +=1
