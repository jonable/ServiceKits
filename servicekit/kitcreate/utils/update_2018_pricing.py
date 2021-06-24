import os
import sys
from collections import OrderedDict
from mailmerge import MailMerge
from filebrowser.sites import site
from kitcreate.models import ServiceLevel, ServiceType, ServiceKitForm

import logging
logger = logging.getLogger('django')

base_dir = os.path.join(site.storage.location, site.directory)
forms_dir = os.path.join(base_dir, 'documents/forms')

data = [
    {
        'dir_name': 'labor',
        'name': 'Labor',
        'level_template': 'SER Labor %s',
        'data': [("NEW_booth_labor_82.0.docx", "82"),
                 ("NEW_booth_labor_88.0.docx", "88"),
                 ("NEW_booth_labor_94.0.docx", "94"),
                 ("NEW_booth_labor_98.0.docx", "98"),
                 ("NEW_booth_labor_108.0.docx", "108"),
                 ("NEW_booth_labor_138.0.docx", "138"),
                 ("NEW_booth_labor_168.0.docx", "168"),
                 ("NEW_booth_labor_198.0.docx", "198"),
                 ("NEW_booth_labor_225.0.docx", "225"),
                 ("NEW_forklift_82.0.docx", "82"),
                 ("NEW_forklift_88.0.docx", "88"),
                 ("NEW_forklift_94.0.docx", "94"),
                 ("NEW_forklift_98.0.docx", "98"),
                 ("NEW_forklift_108.0.docx", "108"),
                 ("NEW_forklift_138.0.docx", "138"),
                 ("NEW_forklift_198.0.docx", "198"),
                 ("NEW_forklift_225.0.docx", "225"),
                 ("NEW_porter_82.0.docx", "82"),
                 ("NEW_porter_88.0.docx", "88"),
                 ("NEW_porter_94.0.docx", "94"),
                 ("NEW_porter_98.0.docx", "98"),
                 ("NEW_porter_108.0.docx", "108"),
                 ("NEW_porter_138.0.docx", "138"),
                 ("NEW_porter_168.0.docx", "168"),
                 ("NEW_porter_198.0.docx", "198"),
                 ("NEW_porter_225.0.docx", "225")
                 ]},
   	{
            'dir_name': 'material_handling',
            'name': 'MaterialHandling',
            'level_template': 'SER MH %s',
            "data": [
		("NEW_MH_40.0.docx", "40"),
		("NEW_MH_44.0.docx", "44"),
		("NEW_MH_76.0.docx", "76"),
		("NEW_MH_80.0.docx", "80"),
		("NEW_MH_82.0.docx", "82"),
		("NEW_MH_94.0.docx", "94"),
		("NEW_MH_100.0.docx", "100"),
		("NEW_MH_144.0.docx", "144"),
		("NEW_MH_150.0.docx", "150"),
		("NEW_MH_168.0.docx", "168"),
		("NEW_MH_174.0.docx", "174"),
		("NEW_MH_178.0.docx", "178"),
		("NEW_MH_ADV_ONLY_40.0.docx", "40"),
		("NEW_MH_ADV_ONLY_44.0.docx", "44"),
		("NEW_MH_ADV_ONLY_76.0.docx", "76"),
		("NEW_MH_ADV_ONLY_80.0.docx", "80"),
		("NEW_MH_ADV_ONLY_82.0.docx", "82"),
		("NEW_MH_ADV_ONLY_94.0.docx", "94"),
		("NEW_MH_ADV_ONLY_100.0.docx", "100"),
		("NEW_MH_ADV_ONLY_144.0.docx", "144"),
		("NEW_MH_ADV_ONLY_150.0.docx", "150"),
		("NEW_MH_ADV_ONLY_168.0.docx", "168"),
		("NEW_MH_ADV_ONLY_174.0.docx", "174"),
		("NEW_MH_ADV_ONLY_178.0.docx", "178"),
            ]},
   	{
            'dir_name': 'furn',
            'name': 'Furniture',
            'level_template': 'SER Furniture %s',
            "data": [
		("LED_LIGHTS_New99.docx", "New99"),
		("LED_LIGHTS_New118.docx", "New118"),
		("LED_LIGHTS_New124.docx", "New124"),
		("LED_LIGHTS_New129.8.docx", "New129.8"),
		("STD_FURN_New99.docx", "New99"),
		("STD_FURN_New118.docx", "New118"),
		("STD_FURN_New124.docx", "New124"),
		("STD_FURN_New129.8.docx", "New129.8"),
            ]}
]


def adminlog(obj, change=False, addition=False, deletion=False):
	from django.contrib.admin.models import LogEntry, CHANGE, ADDITION, DELETION
	flag = None
	if change:
		flag = CHANGE
	if addition:
		flag = ADDITION
	if deletion:
		flag = DELETION


def run():
	furniture_service_type = ServiceType.objects.filter(title='Furniture').first()
	labor_service_type = ServiceType.objects.filter(title='Labor').first()
	materialhandling_service_type = ServiceType.objects.filter(
		title='MaterialHandling').first()
	default_service_type = ServiceType.objects.filter(title="Default").first()

	for item in data:
		service_type = ServiceType.objects.filter(title=item['name'])
		directory = os.path.join(forms_dir, item['dir_name'])
		for x in item['data']:
			_derp = os.path.join(directory, x[0])
			if os.path.exists(_derp):
				level = ServiceLevel.objects.filter(
					title=x['level_template'] % x[1], type=service_type)
				if not level:
					level = ServiceLevel(
						title=item['level_template'] % x[1], type=service_type)
				fake_title = x[0].split('.docx')[0]
				servicekitform = ServiceKitForm(title=fake_title)
				servicekitform.save()
				servicekitform.level.add(level)
				servicekitform.document = FileObject(_derp)
				servicekitform.save()
				adminlog(servicekitform, addition=True)
