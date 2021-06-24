import sys, os
from copy import deepcopy
from mailmerge import MailMerge

# doc = MailMerge('/Users/jonathannable/Desktop/furniture-table-test.docx')
# doc.merge_rows('furn_category', herp)
# doc.merge_rows('furn_subcategory', larp)
# doc.merge_rows('description', derp)
# doc.write('./output.docx')

# from copy import deepcopy
# doc = MailMerge('/Users/jonathannable/Desktop/furniture-table-test.docx')
# # get the table to use
# table = doc._MailMerge__find_row_anchor('furn_category')[0]
# # get parent to add table too
# parent = table.getparent()
# # copy the table as a template
# table_template = deepcopy(table)
# # add template to the parent
# parent.addnext(table_template)

# count = 0
# for j, table in enumerate(tables):
# 	print j, table['heading'], count
# 	count += 1
# 	for i, row_data in enumerate(table['rows']):
# 		print i, row_data['description'], count
# 		count += 1


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


DEFAULT_DIR = './servicekits/masters/new_masters/'
DEFAULT_OUTPUT_DIR = './servicekits/masters/new_masters/tests/'

def restruc_data(data):
	from collections import OrderedDict
	# furn = xls_to_dict(open_workbook('/Users/jonathannable/Desktop/furn-118.xls').sheet_by_index(0))	
	result = OrderedDict()
	for x in data:
		if not x['Heading']:
			continue
		heading = x['Heading']
		if not result.has_key(heading):
			result[heading] = {
				'heading': x.get('Heading', '').strip(),
				'rows': [],
				'note': ''
			}
		result[heading]['rows'].append({
			'description': x.get('description', '').strip(),
			'adv_price': str(x['adv_price']),
			'std_price': str(x['std_price'])
		})		
		result[heading]['note'] = x.get('note', '')
	return result.values()


def run2(data):	
	"""eventschedule form"""
	
	filename = 'event_schedule.docx'
	doc = MailMerge(os.path.join(DEFAULT_DIR,filename))
	for table, values in data.items():
		if table == 'carrier_pickup':
			doc.merge(**{table:values[0]['start']})
		elif table == 'discount':
			doc.merge(**{table:values[0]['date']})
		else:
			doc.merge_rows(table, values)
	doc.merge(**fake_event_info)			
	doc.write(os.path.join(DEFAULT_OUTPUT_DIR, filename))
	os.system("open "+os.path.join(DEFAULT_OUTPUT_DIR, filename))
	return doc

# USE merge_rows2 to MERGE STANDARD_FURN_FORMS
def merge_std_furn_form(data, template_filename, output_filename, context=None, open=False):
	"""furn form"""
	# doc = MailMerge('/Users/jonathannable/Desktop/furniture-table-test.docx')
	# filename = 'furniture_form.docx'
	doc = MailMerge(template_filename)
	merge_rows2(doc, 'furn_category', data)
	if context:
		doc.merge(**context)
	doc.merge(**fake_event_info)
	doc.write(output_filename)
	if open:
		os.system("open "+output_filename)
	return doc

# USE merge_rows2 to MERGE STANDARD_FURN_FORMS
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





# from docx import Document
# p = Document().add_paragraph()
# trying to add another table, need to insert a line break first
def merge_rows3(doc, anchor, tables):
	table, idx, template = doc._MailMerge__find_row_anchor(anchor)
	headings_template = table[3]
	table2, idx2, template2 = doc._MailMerge__find_row_anchor('description')
	
	parent = table.getparent()
	table = deepcopy(table)

	for j, tbl in enumerate(tables):
		
		table_template = deepcopy(table)

		rows = tbl['rows']
		row = deepcopy(template)
		doc.merge([row], furn_category=tbl['heading'])
		table_template.insert(2, row)
		# idx + 1 = 2				
		
		table_template.insert(3, deepcopy(headings_template))
		count = 4
		for i, row_data in enumerate(rows):
			row = deepcopy(template2)
			doc.merge([row], **row_data)
			table_template.insert(count, row)
			count += 1

		parent.addnext(table_template)

def merge_rows(self, anchor, rows):
	table, idx, template = self.__find_row_anchor(anchor)
	if table is not None:
		if len(rows) > 0:
			del table[idx]
			for i, row_data in enumerate(rows):
				row = deepcopy(template)
				self.merge([row], **row_data)
				table.insert(idx + i, row)
		else:
			# if there is no data for a given table
			# we check whether table needs to be removed
			if self.remove_empty_tables:
				parent = table.getparent()
				parent.remove(table)

from mailmerge import *
def run():
	doc  = MailMerge('master.docx')
	docs = [
		MailMerge('doc1.docx'), 
		MailMerge('doc2.docx')
	]
	children = step1(docs)
	return step2(doc, children)

def step1(docs):
	"""
	:docs [MailMerge] list of documents to merge
	documents are added order supplied 
	a line break is supplied between pages 
	"""
	children = []
	for doc in docs:
		for part in doc.parts.values():
			root = part.getroot()

			tag = root.tag
			# if tag is a footer or hreader, pass
			if tag == '{%(w)s}ftr' % NAMESPACES or tag == '{%(w)s}hdr' % NAMESPACES:
				continue	
			for child in root:
				root.remove(child)
				children.append(deepcopy(child))
	return children

def step2(masterdoc, children):
	"""
	:masterdoc <MailMerge> main document to add children too...
	:children see step1 
	"""
	for part in masterdoc.parts.values():
		root = part.getroot()
		tag = root.tag
		# if tag is a footer or hreader, pass
		if tag == '{%(w)s}ftr' % NAMESPACES or tag == '{%(w)s}hdr' % NAMESPACES:
			continue

		for i, child in enumerate(children):
			if i > 0:
				pagebreak = Element('{%(w)s}br' % NAMESPACES)
				pagebreak.attrib['{%(w)s}type' % NAMESPACES] = 'page'
				root.append(pagebreak)	
			root.append(child)

		# fix the margins
		# part -> document -> body -> sectPr -> pgMar
		# <w:pgMar w:top="288" w:right="288" w:bottom="288" w:left="288" w:header="720" w:footer="720" w:gutter="0"/>
		# findall?
		pgMar = part.find('.//{%(w)s}pgMar' % NAMESPACES)
		if pgMar is not None:
			
			pgMar.attrib['{%(w)s}left'% NAMESPACES] = "288"
			pgMar.attrib['{%(w)s}right'% NAMESPACES] = "288"
			pgMar.attrib['{%(w)s}top'% NAMESPACES] = "288"
			pgMar.attrib['{%(w)s}bottom'% NAMESPACES] = "288"
			pgMar.attrib['{%(w)s}gutter'% NAMESPACES] = "0"
			# not sure...
			# pgMar.attrib['{%(w)s}header'% NAMESPACES] = "0"
			# pgMar.attrib['{%(w)s}footer'% NAMESPACES] = "0"
			# 
			# 
			# print pgMar.attrib['{%(w)s}left'% NAMESPACES] 
			# print pgMar.attrib['{%(w)s}right'% NAMESPACES] 
			# print pgMar.attrib['{%(w)s}top'% NAMESPACES] 
			# print pgMar.attrib['{%(w)s}bottom'% NAMESPACES] 
			# print pgMar.attrib['{%(w)s}gutter'% NAMESPACES]

	return masterdoc




