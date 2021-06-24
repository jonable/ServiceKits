import sys, os
import xlrd
import zipfile
import tempfile


from copy import deepcopy
from collections import OrderedDict
sys.path.append(os.path.join(os.path.expanduser('~'), 'Projects', 'utilities'))
from csv_to_xls import open_workbook, xls_to_dict, dict_to_xls2
from mailmerge import MailMerge

from django.utils.text import slugify
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.shortcuts import render
from django import forms
from django.utils import timezone

from filebrowser.sites import site

from pricelists.models import Product, Price, Pricelist, PricelistGroup

from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
staff_member_required = user_passes_test(
	lambda u: u.is_authenticated() and u.is_active and u.is_staff)

class StaffMemberRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
	def test_func(self):
		u = self.request.user
		return u.is_authenticated() and u.is_active and u.is_staff
# view_kit_archive = staff_member_required(view_kit_archive)


class UploadPriceList(forms.Form):
	"""
	Form to upload pricelist
	"""	
	file = forms.FileField(widget=forms.ClearableFileInput(
		attrs={'accept': '.xls, .xlsx'}))
	price_tier = forms.ChoiceField(choices=Price.PRICE_TIER)
	# def __init__(self, *args, **kwargs):
	# 	super(UploadPriceList, self).__init__(*args,**kwargs)
	# 	self.fields['user1'].choices = [(x.pk, x.get_full_name()) for x in User.objects.all()]
	def __init__(self, *args, **kwargs):
		
		super(UploadPriceList, self).__init__(*args, **kwargs)
		
		for visible in self.visible_fields():
			visible.field.widget.attrs['class'] = 'form-control'

def handle_uploaded_file(fileobj):
	return xlrd.open_workbook(file_contents=fileobj.read())
	# return open_workbook(f)

class ImportResult(): pass	

def get_field_map(keys=None):
	field_map = {
		"product_id_type": "Product ID Type",
		"product_id": "Product ID",
		"item_name": "Item Name",
		"published_to_store": "Published to Store",
		"published_to_admin": "Published to Admin",
		"advance_price": "Advance Price",
		"standard_price": "Standard Price",
	}

	if not keys:
		return field_map

	for key in keys:
		if not key:			
			# WHO KNOWS WHAT WILL HAPPEN!?
			continue

		_key = key.rstrip()
		for field, value in field_map.items():
			# some code so either supplier or event pricelist can be imported.
			if _key == 'Product ID':
				field_map['product_id'] = key
			if "Publish to Storefront" in _key:
				field_map["published_to_store"] = key
			if "Publish in Admin" in _key:
				field_map["published_to_admin"] = key

			if _key == value or value in _key:
				field_map[field] = key
	return field_map


def process_import(data, pricelist, price_tier, update=True):
	# match items (check for new)
	results = []
	if not data:
		return results
	
	field_map = get_field_map(keys=data[0].keys())
	for row in data:
		result_obj = ImportResult()
		product = Product.objects.filter(product_id=row.get(field_map['product_id'])).first()
		result_obj.product_added = 0
		if not product:
			product = Product.objects.create(
				product_id=row.get(field_map['product_id']),
				item_name=row.get(field_map['item_name']),
				published_to_store=row.get(field_map['published_to_store']),
				published_to_admin=row.get(field_map['published_to_admin'])	
			)
			result_obj.product_added = 1
		if update:
			product.item_name = row.get(field_map['item_name']) or product.item_name
			product.published_to_store=row.get(field_map['published_to_store'])
			product.published_to_admin=row.get(field_map['published_to_admin'])	
			product.save()
		
		result_obj.product = product

		result_obj.pricelist = pricelist

		price, price_create = Price.objects.get_or_create(product=product, pricelist=pricelist, price_tier=price_tier)
		result_obj.price_added = 0
		if price_create:			
			price.advance_price=row.get(field_map['advance_price']) or 0.00
			price.standard_price=row.get(field_map['standard_price']) or 0.00
			result_obj.price_added = 1
		if not price_create and update:
			price.advance_price = row.get(field_map['advance_price']) or 0.00
			price.standard_price = row.get(field_map['standard_price']) or 0.00
		price.save()
		result_obj.price = price
		results.append(result_obj)		
	return results

def import_pricelist(request, pk):
	context = {}
	pricelist = get_object_or_404(Pricelist, pk=pk)
	if request.method == 'POST':
		form = UploadPriceList(request.POST, request.FILES)
		if form.is_valid():
			workbook = handle_uploaded_file(request.FILES['file'])
			sheet = workbook.sheet_by_index(0)
			data = xls_to_dict(sheet)
			price_tier = form.cleaned_data['price_tier']
			with transaction.atomic():
				import_results = process_import(data, pricelist, price_tier)
			context['import_results'] = import_results
	else:
		form = UploadPriceList()
	context['form'] = form
	context['pricelist'] = pricelist
	return render(request, 'pricelists/import.html', context=context)

import_pricelist = staff_member_required(import_pricelist)

def download_workbook(data, report_name):
	workbook = dict_to_xls2(data)
	response = HttpResponse(content_type='application/vnd.ms-excel')
	response['Content-Disposition'] = 'attachment; filename="%s.xls"' % (
		report_name)
	workbook.save(response)
	return response

def export_pricelist(request, pk):
	field_map = {
		"product_id": "Product ID", 
		"item_name": "Item Name\n", 
		"published_to_store": "Published to Store",
		"published_to_admin": "Published to Admin",
		"advance_price": "Advance Price",
		"standard_price": "Standard Price\n",
		"advanced_split_type": "Advanced Split Type",
		"advanced_split_amount": "Advanced Split Amount",
		"standard_split_type": "Standard Split Type",
		"standard_split_amount": "Standard Split Amount",
	}
	pricelist = get_object_or_404(Pricelist, pk=pk)
	results = {}

	for x,price_tier in Price.PRICE_TIER:
		data = []
		for price in pricelist.prices.filter(price_tier=price_tier):
			obj = OrderedDict()
			obj[field_map.get('product_id')] = price.product.product_id
			obj[field_map.get("item_name")] = price.product.item_name
			if price_tier == "Default":
				obj[field_map.get("published_to_store")] = price.product.published_to_store
				obj[field_map.get("published_to_admin")] = price.product.published_to_admin
			obj[field_map.get("advance_price")] = price.advance_price
			obj[field_map.get("standard_price")] = price.standard_price
			obj[field_map.get("advanced_split_type")] = price.advanced_split_type
			obj[field_map.get("advanced_split_amount")] = price.advanced_split_amount
			obj[field_map.get("standard_split_type")] = price.standard_split_type
			obj[field_map.get("standard_split_amount")] = price.standard_split_amount
			data.append(obj)
		if data:
			results[price_tier] = []
			results[price_tier] = data
	if not results:
		raise Exception('Pricelist contains no data to export')
	return download_workbook(results, "pl-%s" % (pricelist.title))
export_pricelist = staff_member_required(export_pricelist)

def export_pricelist_group(request, pk):
	pricelist_group = get_object_or_404(PricelistGroup, pk=pk)
	results = {}
	field_map = {
		"product_id": "Product ID",
		"item_name": "Item Name\n",
		"published_to_store": "Published to Store",
		"published_to_admin": "Published to Admin",
		"advance_price": "Advance Price",
		"standard_price": "Standard Price\n",
		"advanced_split_type": "Advanced Split Type",
		"advanced_split_amount": "Advanced Split Amount",
		"standard_split_type": "Standard Split Type",
		"standard_split_amount": "Standard Split Amount",
	}
	results = {}
	for pricelist in pricelist_group.pricelists.all():
		for x, price_tier in Price.PRICE_TIER:
			for price in pricelist.prices.filter(price_tier=price_tier):
				if not results.get(price_tier):
					results[price_tier] = []
				obj = OrderedDict()
				obj[field_map.get('product_id')] = price.product.product_id
				obj[field_map.get("item_name")] = price.product.item_name
				if price_tier == "Default":
					obj[field_map.get("published_to_store")] = price.product.published_to_store
					obj[field_map.get("published_to_admin")] = price.product.published_to_admin
				obj[field_map.get("advance_price")] = price.advance_price
				obj[field_map.get("standard_price")] = price.standard_price
				obj[field_map.get("advanced_split_type")] = price.advanced_split_type
				obj[field_map.get("advanced_split_amount")] = price.advanced_split_amount
				obj[field_map.get("standard_split_type")] = price.standard_split_type
				obj[field_map.get("standard_split_amount")] = price.standard_split_amount
				results[price_tier].append(obj)
	if not results:
		raise Exception('Pricelist contains no data to export')
	return download_workbook(results, "pl-group-%s" % (pricelist_group.title))

export_pricelist_group = staff_member_required(export_pricelist_group)

# from filebrowser.sites import site
# base_dir = site.directory
# misc_dir = os.path.join(base_dir, 'documents', 'forms', 'misc' )
# _file = request.FILES.get('file')
# if _file:
# 	filename = _file.name
# 	full_filename = ("%s__%s" % (datetime.now().strftime("_temp_%Y%m%d-%H%M%S"), filename))
# 	full_path = os.path.join(misc_dir, full_filename)
from easy_select2 import Select2, Select2Multiple
class UploadServiceKitTemplate(forms.Form):
	"""
	Form to upload pricelist
	"""
	# widget=forms.FileInput(attrs={'multiple': True})
	file = forms.FileField(help_text="Select 1 or More files to merge pricelist data with.", widget=forms.ClearableFileInput(attrs={'accept': '.doc, .docx', 'multiple': True}))

	pricelist = forms.ChoiceField(choices=[], widget=Select2(attrs={'width': '200px'}))
	# pricelist2 = forms.MultipleChoiceField(choices=[], widget=Select2Multiple(attrs={'width': '200px'}))
	# pricelist_group = forms.ChoiceField(choices=[])
	# price_tier = forms.ChoiceField(choices=Price.PRICE_TIER, required=False)
	# service_type = forms.ChoiceField(choices=[('10','furniture'), ('20','labor'), ('30', 'mh')])

	price_tier = forms.ChoiceField(choices=Price.PRICE_TIER, required=False, widget=Select2(attrs={'width': '200px'}))
	service_type = forms.ChoiceField(choices=[('10','furniture'), ('20','labor'), ('30', 'mh')], widget=Select2(attrs={'width': '200px'}))
	
	test_form = forms.BooleanField(required=False, help_text='Check this to test forms. This will add event test data.')
	
	def __init__(self, *args, **kwargs):
		super(UploadServiceKitTemplate, self).__init__(*args, **kwargs)
		# self.fields['pricelist_group'].choices = [(None,'-----')]+[(x.pk, x.title) for x in PricelistGroup.objects.all()]
		self.fields['pricelist'].choices = [(None,'-----')]+[(x.pk, x.title) for x in Pricelist.objects.all()]
	
		# self.fields['pricelist2'].choices = [(None,'-----')]+[(x.pk, x.title) for x in Pricelist.objects.all()]

		self._upload_files = []

		# for i in range(1, 11):
		# 	self.fields['file__{0}'.format(i)] = forms.FileField(
		# 		required=False, 
		# 		widget=forms.ClearableFileInput(attrs={'accept': '.doc, .docx'})
		# 	)
		# 	self._upload_files.append('file__{0}'.format(i))

		for visible in self.visible_fields():
			visible.field.widget.attrs['class'] = 'form-control'

	def get_upload_files(self):
		return [self.__getitem__(field_name) for field_name in self._upload_files]

def handle_uploaded_file2(f, filepath):
	with open(filepath, 'wb+') as destination:
		for chunk in f.chunks():
			destination.write(chunk)

def context_labor(queryset):
	results = {}
	for x in queryset:
		results["%s__st__adv" % x.product.product_id] = "%.2f" % (x.advance_price)
		results["%s__st__std" % x.product.product_id] = "%.2f" % (x.standard_price)
		results["%s__ot__adv" % x.product.product_id] = "%.2f" % (1.50 * x.advance_price)
		results["%s__ot__std" % x.product.product_id] = "%.2f" % (1.50 * x.standard_price)
	return results


def context_mh(queryset):
	results = {}
	for x in queryset:
		results["%s__stst__std" % (x.product.product_id)] = "%.2f" % (1.00 * x.advance_price)
		results["%s__stot__std" % (x.product.product_id)]  ="%.2f" % ( 1.30 * x.advance_price)
		results["%s__otot__std" % (x.product.product_id)] = "%.2f" % (1.60 * x.advance_price)
		results["%s__stst__sh" % (x.product.product_id)] = "%.2f" % (1.30 * x.advance_price)
		results["%s__stot__sh" % (x.product.product_id)] = "%.2f" % (1.60 * x.advance_price)
		results["%s__otot__sh" % (x.product.product_id)] = "%.2f" % (1.90 * x.advance_price)	
	return results

def context_furniture(queryset):
	results = {}
	for x in queryset:
		results["%s__adv" % x.product.product_id] = "%.2f" % (x.advance_price)
		results["%s__std" % x.product.product_id] = "%.2f" % (x.standard_price)
	return results

def add_test_form_data(data):
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
		'terminal_zip': "01605",
		"thirty_days_prior": 'Feb 10, 2017'
	}
			
	return data.update(fake_event_info)


def create_archive(filelist):
	""" 
	Create a zip archive of the files for download
	"""
	

	tmp = tempfile.NamedTemporaryFile()
	# with tempfile.SpooledTemporaryFile() as tmp:
	with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as archive:
		arcname = './docs/'
		for x in filelist:
			filename = os.path.basename(x[1])
			_file = x[0]
			# make sure we're at the start...
			_file.seek(0)
			archive.write(_file.name, arcname=os.path.join(arcname, filename))

	# Reset file pointer
	tmp.seek(0)

	return tmp

		# Write file data to response
		# return HttpResponse(tmp.read(), content_type='application/x-zip-compressed')

def create_form(request):
	context = {}
	form_context_func = {
		'10': context_furniture,
		'20': context_labor,
		'30': context_mh
	}
	form = UploadServiceKitTemplate(request.POST or None, request.FILES or None)
	
	if form.is_valid():	
		
		base_dir = os.path.join(site.storage.location, site.directory)
		misc_dir = os.path.join(base_dir, 'documents', 'forms', 'misc' )
		
		pricelist = form.cleaned_data.get('pricelist')
		pricelist = Pricelist.objects.get(pk=pricelist)
		
		pricelist_slug = pricelist.slugify
		prices = pricelist.prices.filter(price_tier="Default")
		service_type = form.cleaned_data['service_type']
		pricelist_prices = form_context_func.get(service_type, context_furniture)(prices)

		# toying with adding multiple pricelist... but it's not great.
		# pricelist2 = form.cleaned_data.get('pricelist2')
		# pricelist2 = Pricelist.objects.filter(pk__in=form.cleaned_data.get('pricelist2'))

		# form_context = {}
		# for pl in pricelist2:
		# 	for price_func in form_context_func.values():
		# 		derp =  price_func(pricelist.prices.filter(price_tier="Default"))
		# 		form_context.update(derp)
		


		ignorefields = []
		test_form = form.cleaned_data['test_form']
		if test_form:
			add_test_form_data(pricelist_prices)
		else:			
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
				'thirty_days_prior',
				'sales_tax'
			)
		
		_files = form.files.getlist('file')
		tmp_files = []
		for _file in _files:
			filename = _file.name							
			# full_filename = ("%s__%s" % (timezone.now().strftime("_temp_%Y%m%d-%H%M%S"), filename))			

			full_filename = ("%s__%s" % (pricelist_slug, filename))			
			
			if test_form:
				full_filename = '_%s_%s' % ('TEST', full_filename)

			full_path = os.path.join(misc_dir, full_filename)
			handle_uploaded_file2(_file, full_path)


			tmp = tempfile.NamedTemporaryFile()

			output_filename = '%s-ServiceKitForm' % (pricelist_slug)
		
			if test_form:
				output_filename = '_%s_%s' % ('TEST', output_filename)

			doc = MailMerge(full_path, ignorefields=ignorefields)
			doc.merge(**pricelist_prices)
			# doc.merge(**form_context)
			doc.write(tmp)
			tmp.seek(0)
			tmp_files.append((tmp, full_path))
			os.remove(full_path)
		
		if len(tmp_files) > 1:
			archive = create_archive(tmp_files)
			# response = HttpResponse(tmp.read(), content_type='application/x-zip-compressed')
			response = HttpResponse(archive.read(), content_type='application/zip')
			response['Content-Disposition'] = 'attachment; filename="%s.zip"' % output_filename
			return response


		response = HttpResponse(tmp.read(), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
		response['Content-Disposition'] = 'attachment; filename=%s.docx' % output_filename
		response['Content-Length'] = os.path.getsize(tmp.name)
		return response
			
	context['form'] = form
	return render(request, 'pricelists/create_form.html', context=context)
create_form = staff_member_required(create_form)


def batch_create_form(formtemplate):
	form_context_func = {
		'10': context_furniture,
		'20': context_labor,
		'30': context_mh
	}
	print("SETUP CONFIGURABLE OUTPUT DIR")
	for pricelist in formtemplate.pricelists.all():

		service_type = formtemplate.service_type
		prices = pricelist.prices.filter(price_tier="Default")
		pricelist_prices = form_context_func.get(service_type, context_furniture)(prices)

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
		# tmp = tempfile.NamedTemporaryFile()

		output_dir = os.path.abspath("/Users/jonathannable 1/Desktop/revised/%s/") % (formtemplate.get_service_type_display())
		filename = os.path.join(output_dir, "%s_%s.docx" % (slugify(formtemplate.title), slugify(pricelist.title)))
		doc = MailMerge(formtemplate.template.path_full, ignorefields=ignorefields)
		doc.merge(**pricelist_prices)
		doc.write(filename)

class UploadPriceList2(forms.Form):
	"""
	Form to upload pricelist
	"""
	title = forms.CharField(required=False)
	file = forms.FileField(widget=forms.ClearableFileInput(attrs={'accept': '.xls, .xlsx'}), required=False)
	price_tier = forms.ChoiceField(choices=Price.PRICE_TIER, required=False)	
	# def __init__(self, *args, **kwargs):
	# 	super(UploadPriceList, self).__init__(*args,**kwargs)
	# 	self.fields['user1'].choices = [(x.pk, x.get_full_name()) for x in User.objects.all()]


from django.forms import formset_factory
PricelistFormSet = formset_factory(UploadPriceList2, extra=20)

def bulk_import_pricelists(request):
	context = {}

	formset = PricelistFormSet(request.POST or None, request.FILES or None)
	if formset.is_valid():
		for form in formset.cleaned_data:
			title = form.get('title')
			if not title:
				continue			
			pricelist = Pricelist.objects.create(title=title)
			workbook = handle_uploaded_file(form['file'])
			sheet = workbook.sheet_by_index(0)
			data = xls_to_dict(sheet)
			price_tier = form['price_tier']
			with transaction.atomic():
				import_results = process_import(data, pricelist, price_tier)
	context['formset'] = PricelistFormSet()

	return render(request, 'pricelists/bulk_import.html', context=context)

bulk_import_pricelists = staff_member_required(bulk_import_pricelists)

