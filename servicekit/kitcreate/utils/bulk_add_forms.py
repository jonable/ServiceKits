import os
from filebrowser.sites import site
from filebrowser.base import FileObject
from kitcreate.models import ServiceKit, ServiceLevel, ServiceType, ServiceKitForm, FormVersion
from django.conf import settings

LEVEL_BASE_NAME	= [
	"SER Material Handling",
	"SER Labor",
	"SER Furn",
	"default_dir",
]

os.path.join(site.storage.location, site.directory)
forms_dir = os.path.join(base_dir, 'documents/forms')

furn_dir  = os.path.join(forms_dir, 'furn')
labor_dir = os.path.join(forms_dir, 'labor')
mh_dir    = os.path.join(forms_dir, 'material_handling')
default_dir = os.path.join(forms_dir, 'default')

from kitcreate.utils import labor_util, mh_util, std_furn_util, defaults_util


def get_logger():
	import logging
	logger = logging.getLogger("kitcreate.bulk_add_forms")
	logger.setLevel(logging.DEBUG)
	ch = logging.StreamHandler()
	ch.setLevel(logging.DEBUG)
	ch.setFormatter(logging.Formatter('[%(levelname)s]: %(message)s'))
	logger.addHandler(ch)
	return logger 
log = get_logger()

def replace_forms():

	# look through directy and check if a file has a ServiceKitForm, else make one.
	for dirlist in os.walk(furn_dir):
		for filename in dirlist[-1]:
			if filename == '.DS_Store' or '~$' in filename:
				continue	
		ServiceKitForm.objects.filter(document__icontains='')

def servicekitform_exists(filepath):
	"""Check if the filepath has a corresponding ServiceKitForm"""
	return ServiceKitForm.objects.filter(document__icontains=filepath).exists()
# 
# 
# if wipping data, remove_existing
# else ignore and just add new files and ignore existing
def get_content_type_for_model(obj):
    from django.contrib.contenttypes.models import ContentType
    return ContentType.objects.get_for_model(obj, for_concrete_model=False)

def adminlog(obj, change=False, addition=False, deletion=False):
	from django.contrib.admin.models import LogEntry, CHANGE, ADDITION, DELETION
	flag = None
	if change:
		flag = CHANGE
	if addition:
		flag = ADDITION
	if deletion:
		flag = DELETION
	
	from django.contrib.auth.models import User
	user =  User.objects.filter(is_superuser=True).first()
	LogEntry.objects.log_action(
		user_id=user.pk, content_type_id=get_content_type_for_model(obj).pk, 
		object_id=obj.pk, object_repr=str(obj), 
		action_flag=flag ,change_message="bulk_add_forms_run"
	)

def report_missing():
	""" 
	Look through teh servicekits and see if any files are missing or there are trouble with the file paths
	"""
	results = []
	for x in ServiceKitForm.objects.all():
		if not x.document.exists:
			results.append(x)
		try:
			x.document.path_full
		except Exception:
			results.append(x)
	return results

def bulk_update_forms():
	""" 
	Helper method, calls into the different modules run method 
	Each module is response for rendering the base level templates and moving them into their respective ./uploads/documents/forms directory
	for instance standard_furn_form's base template means all the pricing data is setup... not describing this well
	Two level of tempaltes. Base template and Half Pre rendered template?
	"""
	log.info("NOTE TO JONATHAN: FORMS MAY NOT BE COPYING OVER TO ./forms please fix")
	log.info('updating labor forms')
	labor_util.run()
	log.info('updating MH forms')
	mh_util.run()
	log.info('updating Furn forms')
	std_furn_util.run()
	log.info('updating Default forms')
	defaults_util.run()

def run(update_files=True, remove_existing=False):
	"""
	This method deals with tying the ServiceKitForm to the correct ServiceLevels 
	This method does not render templates nor move the form files from template into forms 
	(see kitecreate.utils.bulk_update_forms)
	:remove_existing this will delete all to ServiceKitForms with a registered service level (furn, labor, mh, default)
	:returns [<ServiceKitForm>] returns a list of ServiceKitForm with missing files sericekitform.document != exist 
	"""
	# I KNOW! this could be heaveily refactored
	# 
	
	log.info("JONATHAN: FORMS MAY NOT BE COPYING OVER TO ./forms please fix")
	furniture_service_type        = ServiceType.objects.filter(title='Furniture').first()
	labor_service_type            = ServiceType.objects.filter(title='Labor').first()
	materialhandling_service_type = ServiceType.objects.filter(title='MaterialHandling').first()
	default_service_type          = ServiceType.objects.filter(title="Default").first()

	if remove_existing:
		log.info('Removing Existing Forms')
		for x in [furniture_service_type, labor_service_type, materialhandling_service_type, default_service_type]:
			obj = ServiceKitForm.objects.filter(level__type=x)
			name = obj.title
			adminlog(obj, deletion=True)
			obj.delete()
			log.info('Service Kit Form %s removed' % name)
	
	if update_files:
		log.info('Updating form template files')
		bulk_update_forms()

	for dirlist in os.walk(furn_dir):
		for filename in dirlist[-1]:
			if filename == '.DS_Store' or '~$' in filename:
				continue
			
			if servicekitform_exists(os.path.join(furn_dir, filename)):
				continue
			
			# check if we have a furn form or a led light form
			# get the service levels for the form or add new service levels
			_name, ext = os.path.splitext(filename)
			if 'STD_FURN' in _name:
				level = _name.replace('STD_FURN_', '')
				service_levels = ServiceLevel.objects.filter(title="SER Furniture %s" % level)
				if not service_levels:
					title = "SER Furniture %s" % level
					service_levels = [ServiceLevel.objects.create(title=title, type=furniture_service_type)]
					log.info('Service Level Created for: %s' % (title))
			
			elif 'LED_LIGHTS' in _name:
				level = _name.replace('LED_LIGHTS_', '')
				service_levels = ServiceLevel.objects.filter(title="SER Furniture %s" % level)
				if not service_levels:
					title = "SER Furniture %s" % level
					service_levels = [ServiceLevel.objects.create(title=title, type=furniture_service_type)]
					log.info('Service Level Created for: %s' % (title))

			# else we give the servive kit form all service levels in the type levels
			else:
				service_levels = ServiceLevel.objects.filter(type=furniture_service_type)
			
			log.info("File not found %s adding file to ServiceKitForm" % _name)

			servicekitform = ServiceKitForm(title=_name)
			servicekitform.save()
			servicekitform.level.add(*[x for x in service_levels])
			servicekitform.document = FileObject(os.path.join(furn_dir, filename))
			servicekitform.save()
			adminlog(servicekitform, addition=True)


	for dirlist in os.walk(mh_dir):
		for filename in dirlist[-1]:
			if filename == '.DS_Store' or '~$' in filename:
				continue
			if servicekitform_exists(os.path.join(mh_dir, filename)):
				continue				
			# std_furn only belong to one pricelevel, make it so
			_name, ext = os.path.splitext(filename)
			if 'MH_' in _name:
				level = _name.replace('MH_', '')
				if 'ADV_ONLY' in _name:
					level = _name.replace('MH_ADV_ONLY_', '')
				service_levels = ServiceLevel.objects.filter(title="SER Material Handling %s" % level)
				if not service_levels:
					title = "SER Material Handling %s" % level
					service_levels = [ServiceLevel.objects.create(title=title, type=materialhandling_service_type)]
					log.info('Service Level Created for: %s' % (title))
			# else add it to all furniture levels
			else:
				service_levels = ServiceLevel.objects.filter(type=materialhandling_service_type)
			
			log.info("File not found %s adding file to ServiceKitForm" % _name)
			servicekitform = ServiceKitForm(title=_name)
			servicekitform.save()
			servicekitform.level.add(*[x for x in service_levels])
			servicekitform.document = FileObject(os.path.join(mh_dir, filename))
			servicekitform.save()
			adminlog(servicekitform, addition=True)

	for dirlist in os.walk(labor_dir):
		for filename in dirlist[-1]:
			if filename == '.DS_Store' or '~$' in filename:
				continue
			if servicekitform_exists(os.path.join(labor_dir, filename)):
				continue							
			_name, ext = os.path.splitext(filename)
			if 'booth_labor' in _name or 'porter' in _name or 'forklift' in _name:
				level = _name.split('_')[-1]
				service_levels = ServiceLevel.objects.filter(title="SER Labor %s" % level)
				if not service_levels:
					title = "SER Labor %s" % level
					service_levels = [ServiceLevel.objects.create(title=title, type=labor_service_type)]
					log.info('Service Level Created for: %s' % (title))
			else:
				service_levels = ServiceLevel.objects.filter(type=labor_service_type)

			log.info("File not found %s adding file to ServiceKitForm" % _name)
			servicekitform = ServiceKitForm(title=_name)
			servicekitform.save()
			servicekitform.level.add(*[x for x in service_levels])
			servicekitform.document = FileObject(os.path.join(labor_dir, filename))
			servicekitform.save()
			adminlog(servicekitform, addition=True)

	for dirlist in os.walk(default_dir):
		for filename in dirlist[-1]:
			if filename == '.DS_Store' or '~$' in filename:
				continue
			if servicekitform_exists(os.path.join(default_dir, filename)):
				continue							
			_name, ext = os.path.splitext(filename)
			service_levels = ServiceLevel.objects.filter(title='default_items')
			
			log.info("File not found %s adding file to ServiceKitForm" % _name)
			servicekitform = ServiceKitForm(title=_name)
			servicekitform.save()
			servicekitform.level.add(*[x for x in service_levels])
			servicekitform.document = FileObject(os.path.join(default_dir, filename))
			servicekitform.save()
			adminlog(servicekitform, addition=True)

	return report_missing()

def get_all_serviceform_formnames():
	""" 
	Gets a list of the forms ServiceKitForm file names based on service type
	:results {
		'service type': 'service level form file name... (filename)'
	}
	"""
	results = {
		'Furniture': [],
		'MaterialHandling': [],
		'Labor': [],
		'Default': []
	}
	herpderp = [(furn_dir, 'Furniture'), (mh_dir, 'MaterialHandling'), (labor_dir, 'Labor'), (default_dir, 'Default')]
	for x in herpderp:
		for dirlist in os.walk(x[0]):
			for filename in dirlist[-1]:
				if filename == '.DS_Store' or '~$' in filename:
					continue
				_name, ext = os.path.splitext(filename)	
				results[x[1]].append(_name)			
	return results

def fix_servicelevels(clear_levels=False):
	"""
	Fix ServiceLevels on ServiceKitForm 
	:clear_levels <bool> clear the ServiceKitForm of any ServiceLevel attached
	"""
	
	if clear_levels:
		for x in ServiceKitForm.objects.all():
			x.level.clear()

	for category, formnames in get_all_serviceform_formnames().items():
		# get the servive type
		service_type = ServiceType.objects.filter(title=category).first()
		for x in formnames:
			# if any of the following are true apply the correct service level to the ServivceKitForm
			if 'STD_FURN' in x:
				level = x.replace('STD_FURN_', '')
				service_levels = ServiceLevel.objects.filter(title="SER Furniture %s" % level)
			elif 'LED_LIGHTS' in x:
				level = x.replace('LED_LIGHTS_', '')
				service_levels = ServiceLevel.objects.filter(title="SER Furniture %s" % level)
			elif 'MH_' in x:
				level = x.replace('MH_', '')
				service_levels = ServiceLevel.objects.filter(title="SER Material Handling %s" % level)				
			# elif 'booth_labor' in x or 'porter' in x or 'forklift' in x:
			elif 'booth_labor' in x:
				level = x.split('_')[-1]
				service_levels = ServiceLevel.objects.filter(title="SER Labor %s" % level)
			# else apply all the servive levels based on the servive type 
			else:
				service_levels = ServiceLevel.objects.filter(type=service_type)				
			servicekitform = ServiceKitForm.objects.filter(title=x).first()
			servicekitform.level.add(*[x for x in service_levels])

def fix_fileobject_paths():
	"""Attempts to fix any incorrectly set file paths on a ServiceKitForm object"""
	# FileBrowser Object wants a realtive path to the file
	# An absolute path messes with it.
	new_file_path = ''
	# os.path.join(site.storage.location, site.directory)
	# forms_dir = os.path.join(base_dir, 'documents/forms')

	# furn_dir  = os.path.join(forms_dir, 'furn')
	# labor_dir = os.path.join(forms_dir, 'labor')
	# mh_dir    = os.path.join(forms_dir, 'material_handling')
	# default_dir = os.path.join(forms_dir, 'default')

	furniture_service_type        = ServiceType.objects.filter(title='Furniture').first()
	labor_service_type            = ServiceType.objects.filter(title='Labor').first()
	materialhandling_service_type = ServiceType.objects.filter(title='MaterialHandling').first()
	default_service_type          = ServiceType.objects.filter(title="Default").first()

	for form in ServiceKitForm.objects.all():
		doc = form.document
		if form.level.filter(type=furniture_service_type):			
			new_file_path = os.path.join(furn_dir ,doc.filename)
		if form.level.filter(type=labor_service_type):
			new_file_path = os.path.join(labor_dir, doc.filename)
		if form.level.filter(type=materialhandling_service_type):
			new_file_path = os.path.join(mh_dir,doc.filename)
		if form.level.filter(type=default_service_type):
			new_file_path = os.path.join(default_dir,doc.filename)
		
		if not new_file_path or doc.path == new_file_path:
			continue
		if not new_file_path:
			print 'incorrect path', new_file_path
		print 'fixing %s with file path %s' % (form, new_file_path)
		form.document = FileObject(new_file_path)
		form.save()

def reset_default_servicekit_order():
	default_service_kit = ServiceKit.objects.filter(title=settings.KITFORMS_DEFAULT_SERVICEKIT_ORDER).first()
	if not default_service_kit:
		raise Exception('Default Service Kit (%s) Not found in Service Kits. Add a kit with the following name first.' % (
			settings.KITFORMS_DEFAULT_SERVICEKIT_ORDER, settings.KITFORMS_DEFAULT_SERVICEKIT_ORDER))

	default_type_order = ['Default', 'Furniture', 'MaterialHandling', 'Labor']
	form_order = []
	for type_title in default_type_order:
		servicetype = ServiceType.objects.filter(title=type_title).first()
		if not servicetype:
			raise Exception('Service Type %s not found' % type_title)
		child_levels = servicetype.servicelevel_set.all()
		for level in child_levels:
			[form_order.append(x.pk) for x in level.servicekitform_set.all(
                        ).order_by('display_order') if x.pk not in form_order]

	default_service_kit.forms.clear()
	default_service_kit.forms.set(form_order)
		
def import_v2_forms(forms_data):
	results = []
	# use this to import the mapped data. could create a mess....
	form_version = FormVersion.objects.filter(title="v2").first()
	for form in forms_data:
			service_level = ServiceLevel.objects.filter(
				title=form['level_title']).first()
			if not os.path.exists(form['base_dir']):
				# raise Exception("% doesnt exisits" % form['base_dir'])
				print("% doesnt exisits" % form['base_dir'])
				continue
			for f in form['forms']:
				if not os.path.exists(os.path.join(form['base_dir'], f)):
					print("% doesnt exisits" % os.path.join(form['base_dir'], f))
					continue

			for f in form['forms']:
				file_path = os.path.join(form['base_dir'], f)
				servicekitform, created = ServiceKitForm.objects.get_or_create(
					title=f, document=FileObject(file_path), form_version=form_version)
				servicekitform.save()
				if service_level:
					servicekitform.level.add(service_level)
					servicekitform.save()
				if created:
					results.append(servicekitform)
	return results





