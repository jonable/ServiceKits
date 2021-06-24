import os
from shutil import copyfile
from filebrowser.sites import site

os.path.join(site.storage.location, site.directory)
forms_dir = os.path.join(base_dir, 'documents', 'forms')
templates_dir = os.path.join(base_dir, 'documents', 'templates')

TEMPLATE_DIR = os.path.join(templates_dir, 'default')
OUTPUT_DIR = os.path.join(forms_dir, 'default')

def run():	
	if not os.path.exists(OUTPUT_DIR):
		os.makedirs(OUTPUT_DIR)	
	for filename in [x for x in list(os.walk(TEMPLATE_DIR))[-1][-1] if '.docx' in x]:
		print "Copying file", filename
		copyfile(os.path.join(TEMPLATE_DIR, filename), os.path.join(OUTPUT_DIR, filename))

