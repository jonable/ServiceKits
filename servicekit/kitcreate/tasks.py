import os
import zipfile

from datetime import datetime

from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe

from background_task import background

from kitcreate.utils.docxtopdf import forms_to_pdf
from kitcreate.models import EventInfo
from kitcreate.notifications import email_notification

from kitcreate.views import (
	create_directory, render_forms, get_merged_forms,
)
from kitcreate.utils.pdf_page_numbers import add_page_numbers

import logging
logger = logging.getLogger('django')


@background(queue="user-notices")
def demo_task(user_id):
	# lookup user by id and send them a message
	user = User.objects.get(pk=user_id)
	email_notification('Test Task Notice', "<H1>Example Email</h1>", [user.email])


@background(queue="archive-servicekit-queue")
def archive_servicekit_forms_tasks(eventinfo_pk):
	"""
	Archive an Event's forms.
	"""
	eventinfo = EventInfo.objects.get(pk=eventinfo_pk)
	# files_to_archive = []
	# Tracking down a weird error, putting catch all exceptions wherever I can...
	try:
		if not eventinfo.output_dir:
			return None
		archive_dir = os.path.join(eventinfo.output_dir, 'archive')
		if not os.path.exists(archive_dir):
			os.makedirs(archive_dir)
		archive_filename = "%s.zip" % (datetime.now().strftime("%Y%m%d-%H%M%S"))
		zf = zipfile.ZipFile(os.path.join(archive_dir, archive_filename), mode="w", allowZip64=False, compression=zipfile.ZIP_DEFLATED)
		for the_file in os.listdir(eventinfo.output_dir):
			filename = os.path.basename(the_file)
			zf.write(os.path.join(eventinfo.output_dir, the_file), arcname=filename)
			# zf.write(os.path.join(folder, the_file))
		zf.close()
		return archive_filename
	except Exception, e:
		raise Exception('Error archiving %s. Error Message: ' % (eventinfo, e))

	return True


@background(queue="create-servicekit-queue")
def create_servicekit_task(eventinfo_pk, user_pk, overwrite=False):
	"""
	Background tas
	Render EventInfo data into Service Kit .docx forms
	Calls to CloudConvert to merge forms into a PDF
	"""
	eventinfo = EventInfo.objects.get(pk=eventinfo_pk)
	# url      = reverse('servicekit_complete', args=(eventinfo_pk,))
	user     = User.objects.get(pk=user_pk)

	hostname = ''
	current_site = Site.objects.get_current()
	if current_site:
		hostname = current_site.domain

	eventinfo_url = "http://%s%s" % (hostname, reverse('servicekit_complete', kwargs={"pk":eventinfo.pk}))

	# if overwrite is true, recreate directory and it's forms.
	if overwrite:
		try:
			create_directory(eventinfo, rebuild=True)
			render_forms(eventinfo)
		except Exception, e:
			email_notification(
				"An error occured creating kit: %s" % eventinfo,
				mark_safe("""An error was encountered processing the service kit (<a href="%s"><%s/a>). Please try again in a few minutes, if the problem persists contact site admin.
					<br><b>Error Code</b><p>%s</p>""")
					% (eventinfo_url, eventinfo, e),
				[user.email]
			)
			logger.error(e)
			return False

	# get a list of all the merged forms to upload to cloud convert
	forms       = get_merged_forms(eventinfo)
	filename    = eventinfo.get_output_filename()
	output_path = os.path.join(eventinfo.output_dir, filename)
	additional_msg = ""
	if not forms:
		# messages.info(request, 'There were no forms found for this Service Kit')
		pass
	else:
		try:
			version_config_options = {}
			if eventinfo.form_version and eventinfo.form_version.config:
				version_config_options = eventinfo.form_version.config

			forms_to_pdf(forms, output_path, config=version_config_options.get("forms_to_pdf", None))
			
			#messy I know.
			page_numbers_added = False
			try:
				add_page_numbers(output_path, output_path, config=version_config_options.get("page_numbers", None))
				page_numbers_added = True
			except Exception, e:
				additional_msg += """
				Please note the PDF rendered succesfully, however the applicaiton failed to write page numbers to the PDF.
				"""
				pass
			

			download_url = "http://%s%s" % (hostname, reverse('download_service_kit', args=(eventinfo_pk,)))		
		
			email_notification(
				"%s's Service Kit is Ready" % eventinfo,
				mark_safe("""
					<p>Service Kit <a href="%s">%s</a> successfully created. 
					<a href="%s">Click here to download pdf</a>
					</p>
					<p>%s</p>
					<br>
					<small>You must be logged into view files.</small>
					"""
					% (
						eventinfo_url, 
						eventinfo, 
						download_url,
						additional_msg)),
				[user.email]
			)
		except UnboundLocalError as e:
			email_notification(
				"An error occured creating kit: %s" % eventinfo,
				mark_safe("""An error was encountered processing the service kit (<a href="%s"><%s/a>).<br><b>Error Code</b><p>The document cloud convert service is currently unavailable. Please try again in a few minutes.</p>""") 
					% (eventinfo_url, eventinfo),
				[user.email]
			)					
			logger.error('forms_to_pdf likely failed: %s: %s (%s)' % (e, eventinfo, eventinfo.pk))
			return False			
		except Exception as e:			
			email_notification(
				"An error occured creating kit: %s" % eventinfo,
				mark_safe("""An error was encountered processing the service kit (<a href="%s"><%s/a>).<br><b>Error Code</b><p>%s</p>""") 
					% (eventinfo_url, eventinfo, e),
				[user.email]
			)					
			logger.error('forms_to_pdf likely failed: %s: %s (%s)' % (e, eventinfo, eventinfo.pk))
			return False
	try:
		archive_servicekit_forms_tasks.now(eventinfo.pk)
	except Exception, e:
		# messages.error(request, 'An error was encountered archiving the forms %s' % (str(e)))
		logger.error(e)
	
	return True