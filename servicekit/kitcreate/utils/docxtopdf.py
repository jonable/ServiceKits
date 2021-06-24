"""
Helper methods to upload and merge forms (docx, doc, pdf) into one PDF:
Uses https://cloudconvert.com/ API.
"""

import os
import cloudconvert

CLOUDCONVERT_API_KEY = ''
def init(combine=False, inputformat="*", outputformat="pdf"):
	api = cloudconvert.Api(CLOUDCONVERT_API_KEY)
	# passing "*" for inputformat allows multipule types of forms to merged into one pdf
	# this is undocumented but it worked... so go with it?
	default_parms = {
		"inputformat": inputformat,
		"outputformat": outputformat,		
	}
	if combine:
		default_parms["mode"] = "combine"
		
	process = api.createProcess(default_parms)
	return process

def continue_process(process_url):
	api = cloudconvert.Api(CLOUDCONVERT_API_KEY)
	return cloudconvert.Process(api, process_url)

def forms_to_pdf(forms, output_path, config=None):
	"""
	Uses CloudConver to merge docx into one PDF 
	Currently using their free plan, 25 files a day 
	@Exception if file path does not exists or the output directory does not exists
	:forms [<String>] an ordered list of absolute [file/paths/to/form.docx] to combine
	:output_path <string>
	:return <string> returns output_path when succesful
	"""
	if not forms:
		return None
	if not os.path.exists(os.path.dirname(output_path)):
		raise Exception('The following output directory does not exist: %s' % os.path.dirname(output_path))		
	for form in forms:
		if not os.path.exists(form):
			raise Exception('The following file does not exist: %s' % form)	
	url = None
	process = init(combine=True)	
	
	# everything below should be run in the background
	# return process.url
	process.start(
		{"files": [{"input": "upload"} for x in forms], 
		"mode": "combine", 
		"save":True
	})

	url = process.data['upload']['url']
	for form in forms:
		try:
			process.api.rawCall(
				 'POST',
				 url,
				 content={
				 	'input': 'upload', 
				 	'outputformat': 'pdf', 
				 	'mode': 'combine', 
				 	'file':open(form, 'rb')
				 },
				 is_authenticated=False,
				 stream=False
			)			
		except Exception, e:
			raise Exception('Error with form: %s. Output path: %s. Message supplied %s' % (form, output_path, e))
	process.refresh()
	if process.data['output'].has_key('url'):
		process.download(localfile=output_path)
	
	return output_path

def form_to_pdf2(form, output_path):
	"""
	Uses CloudConver to convert a docx into a PDF 
	Currently using their free plan, 25 files a day 
	@Exception if file path does not exists or the output directory does not exists
	:form <string> /path/to/form
	:output_path <string>
	:return <string> returns output_path when succesful
	"""	
	if not os.path.exists(form):
		raise Exception('The following file does not exist: %s' % form)	
	if not os.path.exists(os.path.dirname(output_path)):
		raise Exception('The following output directory does not exist: %s' % os.path.dirname(output_path))	
	try:
		process = init()
		process.start({
			"input": "upload",
			"file": open(form, 'rb'),
			"outputformat": "pdf",
			"wait": True,
			'mode': 'convert',
			# 'download': True,		
			# 'email': True
		})	
		if process.data['output'].has_key('url'):
			process.download(localfile=output_path)		
	except Exception, e:
		raise Exception('Error with form: %s. Output path: %s. Message supplied %s' % (form, output_path, e))
	return output_path	

