"""
Helper methods to add page numbers to a PDF.
"""
import StringIO
from PyPDF2 import PdfFileReader, PdfFileWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

import logging
logger = logging.getLogger('django')



def create_new_num_page(page_num, config=None):
	font_name         = "Helvetica"
	font_size         = 8
	page_num_template = "Page %s"
	font_rgb_color    = [0,0,0]
	if config:
		font_name = config.get('font_name') or font_name
		font_size = config.get('font_size') or font_size
		page_num_template = config.get("page_num_template") or page_num_template
		font_rgb_color = config.get("font_rgb_color") or font_rgb_color

	packet = StringIO.StringIO()
	# create a new PDF with Reportlab
	can = canvas.Canvas(packet, pagesize=letter)
	# can.setFillColorRGB(169,169,169)
	can.setFillColorRGB(font_rgb_color[0], font_rgb_color[1], font_rgb_color[2])
	can.setFont(font_name, font_size)	
	can.drawString((letter[0] - 30), 10, page_num_template % page_num)
	can.save()

	#move to the beginning of the StringIO buffer
	packet.seek(0)
	return PdfFileReader(packet)	


def add_page_numbers(pdf_input, pdf_output, config=None):
	# I think running this is corrupting the pdfs...

	existing_pdf = PdfFileReader(pdf_input)
	backup_pdf = PdfFileReader(pdf_input) # this is a lot of shit in mememory...

	output = PdfFileWriter()	
	for i in range(1, existing_pdf.getNumPages()+1):
		new_pdf = create_new_num_page(i, config=config)
		page = existing_pdf.getPage(i-1)
		page.mergePage(new_pdf.getPage(0))
		output.addPage(page)
	
	try:
		output.write(file(pdf_output, 'wb'))
	except Exception as e:
		backup_pdf.stream.seek(0)
		open(pdf_output, 'wb').write(backup_pdf.stream.read())
		logger.error("Failed to add page numbers to PDF %s : (%s)" % (pdf_input, e))
		raise Exception("Failed to add page numbers to PDF %s : (%s)" % (pdf_input, e))
	


