Exhibitor Service Kit Document Creation and Management System.

This application was develop to create, manage, and distribute exhibitor services kits for events serviced by SER exposition services.

What is an Exhibitor Service Kit (aka Service Manual):
An exhibitor service kit is a document containing a large assortment of information specific to an event. 
	- A manual might include:
		- Event Schedules (like event setup and breakdown, order deadlines, ect.)
		- Proceedures and policies for move-in and move-out
		- Directions to the facility
		- Floorplans of the event
		- Contact Info for customer service or event management
		- Exhibiting resources (like guides for first time exhibitors, how to order materials, local info, ect)
		- Marketing materials and order forms for rentals or show services
	
	

How it worked:
- Create or Select from an existing event
- Select services available to the event (labor, rentals, material handing/logistics)
- Select price levels and taxe rate
- Add event specific documents (Third party order forms, additional marketing materials, exhibiting resources)
- Render the forms into a single PDF for download or print


Features.
- Document life cycle tracking from draft to published
- Notifications to staff about revisions while editing
- Document history and reversion
- Templates maintained as Word Documents
- Maintain pricelist for each services offered
- Create a sharable/download link to the PDF



Install for ServiceKit Django Applicaiton for development.

Requirements:
	- Python 2.7 (https://www.python.org/download/releases/2.7/)
	- Virtualenv (https://virtualenv.pypa.io/en/stable/)

Set up:
- Unzip the ServiceKit archive.

- Change directories into the unzipped directory.
	:cd ./ServiceKit

- Create a new virtual enviroment.
	:virtualenv project_name

- From the virtual enviroment run.
	:pip install -r requirements.txt

- To run the development server
	:python manage.py runserver 0.0.0.0:8111

- To run the interactive shell
	:python manage.py shell

