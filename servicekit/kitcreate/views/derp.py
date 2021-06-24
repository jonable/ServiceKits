

from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic.base import TemplateView


class TestUpgrade(TemplateView):

	template_name = "kitcreate/v2/_demo.html"

	def get_context_data(self, *args, **kwargs):
		context = super(TestUpgrade, self).get_context_data(*args, **kwargs)
		return context