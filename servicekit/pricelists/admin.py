from django.contrib import admin
from django.core.urlresolvers import reverse
from django.db import models

from pricelists.models import Product, Pricelist, Price, Supplier, PricelistGroup, FormTemplate, PricelistLink
from easy_select2 import select2_modelform


class SupplierAdmin(admin.ModelAdmin):
	'''
		Admin View for Supplier
	'''
	pass

admin.site.register(Supplier, SupplierAdmin)

PriceForm = select2_modelform(Price, attrs={'width': '250px'})
class PriceAdmin(admin.ModelAdmin):
	'''
		Admin View for Price
	'''
	list_display = ('product', 'price_tier','pricelist', 'advance_price', 'standard_price')
	list_filter = ('product', 'price_tier','pricelist', 'advance_price', 'standard_price')
	fields = ('product', 'price_tier','pricelist', 'advance_price', 'standard_price')
	form = PriceForm
admin.site.register(Price, PriceAdmin)


class PriceInline(admin.TabularInline):
	'''
		Tabular Inline View for Price
	'''
	model = Price
	extra = 0
	fields = ('pricelist', 'price_tier', 'advance_price', 'standard_price')

class PriceAdmin(admin.ModelAdmin):
	'''
		Admin View for Price
	'''
	list_display = ('product', 'pricelist', "advance_price", "standard_price")
	list_filter = ('product', 'pricelist')
	
class ProductAdmin(admin.ModelAdmin):
	'''
		Admin View for Product
	'''
	list_display = ('product_id', 'item_name', 'supplier',
					'published_to_store', 'published_to_admin')
	list_filter = ('product_id', 'item_name', 'supplier')
	search_fields = ('product_id', 'item_name', 'supplier__title',)
	inlines = [
		PriceInline,
	]
	# raw_id_fields = ('',)
	# readonly_fields = ('',)
	# search_fields = ('',)


class PriceInline2(admin.TabularInline):
	'''
		Tabular Inline View for Price
	'''
	model = Price
	extra = 0
	fields = ('product', 'price_tier', 'advance_price', 'standard_price')


class PricelistAdmin(admin.ModelAdmin):
	'''
		Admin View for Pricelist
	'''
	list_display = ('title', 'import_pricelist_link', 'export_pricelist_link')
	list_filter = ('title',)
	search_fields = ('title',)
	fields = ('title',)
	inlines = [
		PriceInline2,
	]

	def export_pricelist_link(self, obj):
		return '<a href="%s">%s</a>' % (reverse('pricelists:export', kwargs={'pk':obj.pk}), 'Export')
	export_pricelist_link.allow_tags = True
	export_pricelist_link.short_description = 'Export Pricelist'

	def import_pricelist_link(self, obj):
		return '<a href="%s">%s</a>' % (reverse('pricelists:import', kwargs={'pk':obj.pk}), 'Import')
	import_pricelist_link.allow_tags = True
	import_pricelist_link.short_description = 'Import Pricelist'

# from django import forms
# class PricelistGroupForm(forms.ModelForm):
# 	pricelist_s = forms.ModelMultipleChoiceField(
# 		queryset=Pricelist.objects.all(), 
# 		required=False,
# 		widget=admin.widgets.FilteredSelectMultiple(
# 	  		verbose_name='Pricelists',
# 	  		is_stacked=False
# 		)
# 	)

# 	class Meta:
# 		model = PricelistGroup
# 		fields = ("title", 'pricelists')

PricelistGroupForm = select2_modelform(PricelistGroup, attrs={'width': '250px'})
class PricelistGroupAdmin(admin.ModelAdmin):
	'''
		Admin View for PricelistGroup
	'''
	form = PricelistGroupForm
	list_display = ('title', 'export_pricelist_group_link')
	list_filter = ('title',)
	filter_horizontal = ('pricelists',)    
	# filter_vertical  = ('pricelists',)    
	# formfield_overrides = {
	#     models.ManyToManyField: {'widget': admin.widgets.FilteredSelectMultiple('Pricelists', True) }
	# }

	class Media:
		js = (
			"easy_select2/js/init.js",
			"easy_select2/js/easy_select2.js",
		)

	def export_pricelist_group_link(self, obj):
		return '<a href="%s">%s</a>' % (reverse('pricelists:export_group', kwargs={'pk': obj.pk}), 'Export')
	export_pricelist_group_link.allow_tags = True
	export_pricelist_group_link.short_description = 'Export Pricelist'

admin.site.register(PricelistGroup, PricelistGroupAdmin)

admin.site.register(Pricelist, PricelistAdmin)

admin.site.register(Product, ProductAdmin)


class FormTemplateAdmin(admin.ModelAdmin):
	'''
		Admin View for FormTempalte
	'''
	list_display = ('title', 'service_type', 'template')
	list_filter = ('title',)
	search_fields = ('title',)
	fields = ('title', 'service_type', 'pricelists', 'template')
	filter_horizontal = ['pricelists']
admin.site.register(FormTemplate, FormTemplateAdmin)

PricelistLinkForm = select2_modelform(PricelistLink, attrs={'width': '250px'})
class PricelistLinkAdmin(admin.ModelAdmin):
	'''
		Admin View for PricelistLink
	'''
	list_display = ('pricelist',)
	fields = ('pricelist', 'service_kit_forms',)
	filter_horizontal = ("service_kit_forms",)
	form = PricelistLinkForm
admin.site.register(PricelistLink, PricelistLinkAdmin)
