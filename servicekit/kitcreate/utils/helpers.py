import os
from kitcreate.views import (
	render_forms, get_merged_forms, create_directory, 
	add_page_numbers, forms_to_pdf
)

def render_a_service_kit(eventinfo):
	# for testing purposes
	# create a directory for forms to live in
	create_directory(eventinfo, rebuild=True)
	# merege the forms (word files) with the data in eventinfo object
	render_forms(eventinfo)
	# get a list of all the forms for the service kit
	forms = get_merged_forms(eventinfo)
	# service kit pdf name
	filename    = eventinfo.get_output_filename()
	# path to save the service kit pdf
	output_path = os.path.join(eventinfo.output_dir, filename)
	# merge all the forms into the service kit
	forms_to_pdf(forms, output_path)	
	# add page numbers to the forms
	add_page_numbers(output_path, output_path)

	return output_path