from kitcreate.models import ServicePriceListMap, ServiceType, ServiceKitForm


# def base_ServiceKitForms_map():
# 	return {
# 		'Labor': 'base_labor_template_v3'
# 		'Furniture': 'base_furniture_template_v3'
# 		'MaterialHandling': 'base_mh_template_v3'

# 	}

def create_form_title(servicekit_form, service_level):
	return '[{0}]{1} - {2}'.format(servicekit_form.form_version.title, servicekit_form.title, service_level.title,)

def bulk_create_forms(type, base_servicekit_form):
	results = []
	for service_map in ServicePriceListMap.objects.filter(service_level__type__title=type):		
		form_title = create_form_title(base_servicekit_form, service_map.service_level)
		# obj = ServiceKitForm.objects.create(
		# 	title=form_title, 
		# 	level=[service_map.service_level],
		# 	document=base_servicekit_form.document,
		# 	form_version=base_servicekit_form.form_version,
		# 	description=base_servicekit_form.description,
		# )
		obj = dict(
			title=form_title, 
			level=[service_map.service_level],
			document=base_servicekit_form.document,
			form_version=base_servicekit_form.form_version,
			description=base_servicekit_form.description,
		)		
		results.append(obj)
	return results

def bulk_create_forms2(type, base_servicekit_form):
	results = []
	for service_map in ServicePriceListMap.objects.filter(service_level__in=base_servicekit_form.level.all()):		
		form_title = create_form_title(base_servicekit_form, service_map.service_level)
		obj = ServiceKitForm.objects.create(
			title=form_title, 			
			document=base_servicekit_form.document,
			form_version=base_servicekit_form.form_version,
			description=base_servicekit_form.description,
		)
		obj.level.add(service_map.service_level)
		# obj = dict(
		# 	title=form_title, 
		# 	level=[service_map.service_level],
		# 	document=base_servicekit_form.document,
		# 	form_version=base_servicekit_form.form_version,
		# 	description=base_servicekit_form.description,
		# )		
		results.append(obj)
	return results

def create_all(base_forms_mapping):
	"""
	{
		'service_type': ServiceKitForm
	}
	"""
	# base_forms_mapping
	results = {}
	for service_type in ServiceType.objects.filter(title__in=base_forms_mapping.keys()):
		objects = bulk_create_forms(service_type, base_forms_mapping.get(service_type))
		results[service_level] = objects
	return results

def associate_forms(type, base_servicekit_form):
	results = []
	for service_map in ServicePriceListMap.objects.filter(service_level__type__title=type):		
		form_title = create_form_title(base_servicekit_form, service_map.service_level)
		# import ipdb; ipdb.set_trace()
		obj = ServiceKitForm.objects.filter(
			title=form_title,
			level=service_map.service_level,
			document=base_servicekit_form.document,
			form_version=base_servicekit_form.form_version,
		)
		results.append(obj)
	return results


def find_all_associate_forms(base_forms_mapping):
	"""
	{
		'service_type': ServiceKitForm
	}
	"""
	# base_forms_mapping
	results = {}
	for service_type in ServiceType.objects.filter(title__in=base_forms_mapping.keys()):
		objects = associate_forms(service_type, base_forms_mapping.get(service_type))
		results[service_level] = objects
	return results


