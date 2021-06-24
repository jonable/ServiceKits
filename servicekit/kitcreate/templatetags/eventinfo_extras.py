from collections import OrderedDict
from django import template
# from django.contrib.admin.templatetags.admin_list import result_headers, result_hidden_fields, results



register = template.Library()

@register.filter
def wizard_stepper(steps):
	stepper = []
	# import ipdb; ipdb.set_trace()
	i = 0
	for form_index, form in steps._wizard.get_form_list().items():
		obj = {}
		obj['index'] = i + 1
		obj['title'] = form.form_title
		obj['active'] = False
		obj['complete'] = False
		# if the steps.index is greater than the form index
		# then it's complete
		if steps.index > i:
			obj['complete'] = True
		if form_index == steps.current:
			obj['active'] = True
		stepper.append(obj)
		i += 1
	return stepper


@register.assignment_tag
def get_pl_forms(eventinfo, pricelevel):
	"""
	Get the price level forms selected for this event
	"""
	return eventinfo.service_kit.forms.filter(level=pricelevel)

@register.assignment_tag
def get_additional_forms(eventinfo):
	"""
	Get additional forms
	"""
	if not eventinfo.service_kit:
		return []
	return eventinfo.service_kit.forms.filter(level=None)

@register.assignment_tag
def order_schedule(eventinfo):
	return eventinfo.schedule.order_by('date', 'start_time')
	# return sorted(eventinfo.schedule.all(), key=lambda x: LOCAL_FIELDS.index(x.type))

@register.assignment_tag
def order_schedule2(eventinfo):
	results = OrderedDict()

	for schedule_item in eventinfo.schedule.order_by('date', 'start_time'):
		_obj = OrderedDict()
		if not results.has_key(schedule_item.get_type_display()):
			results[schedule_item.get_type_display()] = []
		results[schedule_item.get_type_display()].append(schedule_item)
	results2 = []
	for key, value in results.items():
		_obj = {
			'schedule_type': key,
			'schedule_values': value
		}
		results2.append(_obj)
	return results2 


@register.assignment_tag
def order_schedule3(eventinfo):
	results = OrderedDict()

	for schedule_item in eventinfo.schedule.order_by('date', 'start_time'):
		_obj = OrderedDict()
		schedule_type_display = schedule_item.get_type_display()
		if schedule_type_display in ['Advance Shipping Start Date', 'Company Move in', 'Direct Shipping Start Date', 'Company Move out']:
			continue
		if not results.has_key(schedule_type_display):
			results[schedule_type_display] = []
		results[schedule_item.get_type_display()].append(schedule_item)
	results2 = []
	for key, value in results.items():
		_obj = {
			'schedule_type': key,
			'schedule_values': value
		}
		results2.append(_obj)
	return results2 

@register.simple_tag
def show_open_date(eventinfo):
	dates = eventinfo.schedule.filter(type='event_date')
	date1 = dates.first()
	date2 = dates.last()
	if dates and dates.count() == 1:
		return date1.date.strftime("%B %d, %Y")
	if date1 and date2:
		return  "%s - %s" % (date1.date.strftime("%B %d"), date2.date.strftime("%d, %Y"))
	return ''

@register.filter
def get_date_by_type(value, type):
    return value.schedule.filter(type=type)


@register.inclusion_tag('kitcreate/snippets/storefrontstatus-def.html', takes_context=True)
def storefront_help(context):
    return {
    	'status': context['eventinfo'].storefrontstatus
    }

@register.simple_tag
def show_servicekitstatus_date(eventinfo):
	return eventinfo.current_servicekitstatus_update


# @register.simple_tag
# def url_replace(request, field, value):
#     dict_ = request.GET.copy()
#     dict_[field] = value
#     return dict_.urlencode()

import urllib
@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    query = context['request'].GET.dict()
    query.update(kwargs)
    return urllib.urlencode(query)