"""
Creates word XML elements
"""
import os
from lxml import etree
from lxml.etree import Element
from mailmerge import MailMerge

# doc.zip.open('word/_rels/document.xml.rels')

def rid_exists(doc):
	# tree = etree.parse(doc.zip.open('word/_rels/document.xml.rels'))
	tree = doc.relationship
	# chec if id is in thing.
	for i, x in enumerate(tree.getroot()):
		if "i" in x.attrib['Id']:
			return True

def generate_rid(doc): 
	# tree = etree.parse(doc.zip.open('word/_rels/document.xml.rels'))
	tree = doc.relationship
	return "rId%s" % (len(tree.getroot())+1)

def build_relationship(doc, filepath):
	'<Relationship Id="rId21" Target="NULL" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"/>'
	'<Relationship Id="rId20" Target="file:////" TargetMode="External" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/oleObject"/>'
	# tree = etree.parse(doc.zip.open('word/_rels/document.xml.rels'))
	tree = doc.relationship
	root = tree.getroot()
	img_rid = generate_rid(doc) 
	image = Element('{http://schemas.openxmlformats.org/package/2006/relationships}Relationship')
	image.attrib['Id'] = img_rid
	image.attrib['Target'] = "NULL"
	image.attrib['Type'] = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
	root.append(image)

	file_rid = generate_rid(doc)
	filer = Element('{http://schemas.openxmlformats.org/package/2006/relationships}Relationship')
	filer.attrib['Id'] = file_rid
	filer.attrib['Target'] = filepath
	filer.attrib['TargetMode'] = "External"
	filer.attrib['Type'] = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/oleObject"
	root.append(filer)
	return {'image': image, 'file': filer}

def create_shape_id(shape_id):
	# id neeeds to be a 4 digit number unique
	return '_x0000_i%s' % ("1%03d" % shape_id)

def build_shape(shape_id, r_id):
	shape = Element('{urn:schemas-microsoft-com:vml}shape') 
	shape.attrib['type'] = '#_x0000_t75'
	shape.attrib['id'] = create_shape_id(shape_id)
	nsmap = dict(
		r="http://schemas.openxmlformats.org/officeDocument/2006/relationships",
		o="urn:schemas-microsoft-com:office:office"
	)
	image = Element('{urn:schemas-microsoft-com:vml}imagedata', nsmap=nsmap)
	image.attrib['{http://schemas.openxmlformats.org/package/2006/relationships}id'] = r_id
	image.attrib['{urn:schemas-microsoft-com:office:office}title'] = ""
	shape.append(image)
	return shape

def build_oleobject(shape_id, r_id):
	nsmap = dict(
		r="http://schemas.openxmlformats.org/officeDocument/2006/relationships",
		o="urn:schemas-microsoft-com:office:office"
	)

	oleobject = Element("{urn:schemas-microsoft-com:office:office}OLEObject", nsmap=nsmap, DrawAspect="Content", ProgID="Word.Document.12", Type="Link", UpdateMode="Always")
	oleobject.attrib['ShapeID'] = create_shape_id(shape_id)
	oleobject.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'] = r_id

	LinkType = Element("{urn:schemas-microsoft-com:office:office}LinkType")
	LinkType.text = "Picture"

	LockedField = Element("{urn:schemas-microsoft-com:office:office}LockedField")
	LockedField.text = "false"

	FieldCodes = Element("{urn:schemas-microsoft-com:office:office}FieldCodes")
	FieldCodes.text = "\\f 0"       
	print FieldCodes.text
	oleobject.append(LinkType)
	oleobject.append(LockedField)
	oleobject.append(FieldCodes)
	return oleobject

def build_msword_filepath(filepath):
	return "file:///%s"%os.path.abspath(filepath)

def add_doc_link(doc, filepath):
	shape_ids = None
	msfilepath = build_msword_filepath(filepath)
	for part in doc.parts.values():
		if 'document' not in part.getroot().tag:
			continue
		shape_ids = [int(shape.attrib['id'][-4:]) for shape in part.findall('.//{urn:schemas-microsoft-com:vml}shape')]
		root = part.getroot()
		body = root.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}body')
		if shape_ids:
			shape_id = max(shape_ids)+1
		else:
			shape_id = 21
		relationships = build_relationship(doc, msfilepath)
		image_r_id = relationships['image'].attrib['Id']
		file_r_id = relationships['file'].attrib['Id']

		paragraph = Element('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p')
		doc_relationship_ele = Element('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r')
		doc_object_ele = Element('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}object')
		
		doc_object_ele.append(build_shape(shape_id, image_r_id))
		doc_object_ele.append(build_oleobject(shape_id, file_r_id))

		doc_relationship_ele.append(doc_object_ele)
		paragraph.append(doc_relationship_ele)
		body.append(paragraph)  

		pagebreak = Element('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}br')
		pagebreak.attrib['{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type'] = 'page'
		body.append(pagebreak)


# def main():
# 	doc = MailMerge('/Users/jonathannable/Desktop/master.docx')
# 	filepath = "/Users/jonathannable/Desktop/doc1.docx"
# 	add_doc_link(doc, filepath)
# 	# doc.write('/Users/jonathannable/Desktop/results.docx')
# 	return doc

# MERGING
# from kitcreate.merge_documents import add_doc_link
# from mailmerge import MailMerge
# from kitcreate.models import *

# event  = EventInfo.objects.get(pk=17)
# master = ServiceKitForm.objects.last()
# cover  = ServiceKitForm.objects.get(pk=9)
# doc    = MailMerge(master.document.path_full)
# # fields = doc.get_merge_fields()
# doc.merge(
# 	facility=event.facility.title, 
# 	facility_city=event.facility.city, 
# 	facility_state=event.facility.state, 
# 	event_name=event.event_name.description, 
# 	event_header_date=event.get_event_date()
# )

# filelist = [x.document.path_full for x in [master, cover]]
# [filelist.append(x.document.path_full)for x in event.service_kit.forms.all()]

# for x in filelist:
# 	add_doc_link(doc, x)
# doc.write('/Users/jonathannable/Desktop/output.docx')


# class MergeHelper(object):
# 	def __init__(self, instance):
# 		self.facility          = instance.facility.title
# 		self.facility_address  = instance.facility.address
# 		self.facility_address1 = instance.facility.address1
# 		self.facility_city     = instance.facility.city 
# 		self.facility_state    = instance.facility.state
# 		self.facility_zip      = instance.facility.zip
# 		self.event_name        = instance.event_name.description
# 		self.event_header_date = instance.get_event_date()
# 		self.discount_date     = instance.get_discount_date()


