from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.text import slugify
from filebrowser.fields import FileBrowseField
# Create your models here.

class Supplier(models.Model):
	# a collection of products
	title = models.CharField(max_length=255, blank=True, null=True)

	def __str__(self):
		return "%s" % (self.title)

class Product(models.Model):
	# an inventory or line item in boomer
	supplier              = models.ForeignKey(Supplier, blank=True, null=True)
	product_id            = models.CharField(max_length=255, blank=True, null=True)
	item_name             = models.CharField(max_length=255, blank=True, null=True)
	published_to_store    = models.CharField(max_length=255, blank=True, null=True, choices=[('y', 'y'), ('n', 'n')])
	published_to_admin    = models.CharField(max_length=255, blank=True, null=True, choices=[('y', 'y'), ('n', 'n')])
	
	def __str__(self):
		return "%s (%s)" % (self.item_name, self.product_id)

	def get_admin_url(self):
		return reverse("admin:%s_%s_change" % (self._meta.app_label, self._meta.model_name), args=(self.id,))

class Pricelist(models.Model):
	# a collection of prices
	title = models.CharField(max_length=255, blank=True, null=True)
	
	def __str__(self):
		return "%s" % (self.title)
	
	class Meta:
		ordering = ['-title',]

	@property
	def slugify(self):
		return slugify(self.title)

	def get_admin_url(self):
		return reverse("admin:%s_%s_change" % (self._meta.app_label, self._meta.model_name), args=(self.id,))

	def get_export_url(self):
		return reverse("pricelists:export", kwargs={'pk': self.pk})

class PricelistGroup(models.Model):
	title = models.CharField(max_length=255, blank=True, null=True)
	pricelists = models.ManyToManyField(Pricelist, blank=True)

class Price(models.Model):
	# a product price, for a price level. 
	product = models.ForeignKey(Product, related_name="prices")
	pricelist = models.ForeignKey(Pricelist, related_name="prices")
	PRICE_TIER = [('Default', 'Default'), ('Show Organizer', 'Show Organizer')]
	price_tier = models.CharField(max_length=255, default="Default", choices=PRICE_TIER)
	advance_price         = models.FloatField(default=0.0)
	standard_price        = models.FloatField(default=0.0) 
	advanced_split_type   = models.CharField(max_length=255, default="Amount")
	advanced_split_amount = models.IntegerField(default=0)
	standard_split_type   = models.CharField(max_length=255, default="Amount")
	standard_split_amount = models.IntegerField(default=0)

	def __str__(self):
		# return "%s %s/%s" % (self.product, self.advance_price, self.standard_price)
		return "%s" % (self.product)
   	
	def get_admin_url(self):		
		return reverse("admin:%s_%s_change" % (self._meta.app_label, self._meta.model_name), args=(self.id,))


class FormTemplate(models.Model):
	title = models.CharField(max_length=255, blank=True, null=True)
	pricelists = models.ManyToManyField(Pricelist)
	service_type = models.CharField(
		max_length=55, choices=[('10', 'furniture'), ('20', 'labor'), ('30', 'mh')])
	template = FileBrowseField("Template", max_length=200, directory="documents/templates/2018_revision/",
	                           extensions=[".docx", '.doc', '.pdf'], blank=True, null=True, help_text=".docx files only")


class PricelistLink(models.Model):
	pricelist = models.ForeignKey(Pricelist, related_name="links")
	# service_level = models.ForeignKey("kitcreate.ServiceLevel", related_name="links")
	service_kit_forms = models.ManyToManyField("kitcreate.ServiceKitForm", related_name="pricelist_links")

	def __str__(self):
		return self.pricelist.title
