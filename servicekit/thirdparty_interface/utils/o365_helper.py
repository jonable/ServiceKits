import requests
import urllib
import os
from allauth.socialaccount.models import SocialApp, SocialLogin, SocialAccount, SocialToken
from django.core.urlresolvers import  reverse
from django.contrib.sites.models import Site
from django.conf import settings
from django.template import Template
from django.shortcuts import render
from django.http import HttpResponse

# cant use me...
# https://graph.microsoft.com/v1.0/users/ /drive
GRAPH_API_ENDPOINT = 'https://graph.microsoft.com/v1.0/users/'

class O365DriveException(Exception): pass

def get_o365_social_app():
	return SocialApp.objects.get(provider='office365')

def o365_get_admin_consent_url(is_secure, state):
	# // Line breaks are for legibility only.

	# GET https://login.microsoftonline.com/{tenant}/adminconsent
	# ?client_id=6731de76-14a6-49ae-97bc-6eba6914391e
	# &state=12345
	# &redirect_uri=http://localhost/myapp/permissions	
	
	current_site = Site.objects.get(pk=settings.SITE_ID) 
	
	o365         = get_o365_social_app()
	client_id    = o365.client_id
	ms_domain = ""
	if is_secure:
		protocol = 'https'
	else:
		protocol = 'http'

	redirect_uri = "%s://%s%s" % (protocol, current_site.domain, reverse('o365_admin_consent_callback'))
	params = {
		"o365": o365,
		"client_id": client_id,
		"redirect_uri": redirect_uri,
		"state"	: state
	}
	return 'https://login.microsoftonline.com/%s/adminconsent?%s' % (domain, urllib.parse.urlencode(params))

def store_admin_token(token_data):
	# this may not be required
	# I can just get a new token each time I need to create a folder...
	access_token = token_data.get('access_token')
	expires_in = token_data.get('expires_in')
	o365_admin_user = SocialAccount.objects.filter(user__email=settings.O365_ADMIN_ACCOUNT).first()	
	return None

def get_users_o365_id(user):
	# returns userPrincipalName rather than the o365 UID.
	social_account = user.socialaccount_set.filter(extra_data__isnull=False).first()
	if social_account and social_account.extra_data and social_account.extra_data.get('userPrincipalName', False):
		return social_account.extra_data.get('userPrincipalName', None)
	return None

def o365_admin_get_access_token(session):
	# // Line breaks are for legibility only.

	# POST /{tenant}/oauth2/v2.0/token HTTP/1.1
	# Host: login.microsoftonline.com
	# Content-Type: application/x-www-form-urlencoded
	domain = ""
	access_token_url = 'https://login.microsoftonline.com/%s/oauth2/v2.0/token' % (domain)
	o365          = get_o365_social_app()	
	scope         = "https://graph.microsoft.com/.default"
	client_id     = o365.client_id
	client_secret = o365.secret
	grant_type    = 'client_credentials'
	data = {
		"scope": scope,
		"client_id": client_id,
		"client_secret": client_secret,
		"grant_type": grant_type,
	}
	response = session.post(access_token_url, data=data)
	if response.status_code == 200:
		access_token = response.json().get('access_token')
		session.headers.update(get_o365_auth_headers(access_token))
	return response

def get_o365_auth_headers(access_token):
	headers = {
		'Authorization' : 'Bearer {0}'.format(access_token),
		# 'Accept' : 'application/json',
		# 'Content-Type' : 'application/json'
	}
	return headers

def o365_check_if_folder_exists(session, folder_path):
	# if folder_path is none... assume we are getting root?	
	if folder_path == "/" or folder_path == "":
		request_uri = "{graph_api_endpoint}{graph_user_id}/{graph_action}".format(
			graph_api_endpoint=GRAPH_API_ENDPOINT,
			graph_user_id=' ',
			graph_action='drive/root/children'
		)
	else:
		request_uri = "{graph_api_endpoint}{graph_user_id}/{graph_action}".format(
			graph_api_endpoint=GRAPH_API_ENDPOINT,
			graph_user_id=' ',
			graph_action='drive/root:/{folder_path}:/children'.format(folder_path=folder_path)
		)
	response = session.get(request_uri)
	if response.status_code == 404:
		return False
	if response.status_code == 400:
		# bad request most likely.
		raise Exception(response.json())
	if response.status_code == 200:
		return True

def o365_create_folder(session, parent_folder_path, new_folder_name):
	# Response Code
	# 201 == success
	# 409 == nameAlready Exists
	# 
	# https://graph.microsoft.com/v1.0/users/{user_id|user_principal_name}/drive/root:/Graphics:/children
	INTERNAL_IPS = ('',)
	if parent_folder_path == '/' or parent_folder_path == '':
		request_uri = "{graph_api_endpoint}{graph_user_id}/{graph_action}".format(
			graph_api_endpoint=GRAPH_API_ENDPOINT,
			graph_user_id=' ',
			graph_action='drive/root/children'
		)
	else:
		request_uri = "{graph_api_endpoint}{graph_user_id}/{graph_action}".format(
			graph_api_endpoint=GRAPH_API_ENDPOINT,
			graph_user_id=' ',
			graph_action='drive/root:/{parent_folder_path}:/children'.format(parent_folder_path=parent_folder_path)
		)
	response = session.post(request_uri, json={
			"name": new_folder_name,
			"folder": {}
		})

	if response.status_code not in [201, 200]:
		raise Exception('Error processing request %s: %s' % (response.status_code, response.content))

	return response

def o365_check_if_share_link_exists(session, job):
	# in the end it's not required... but helpful to know how to check permissions
	# optimistically check if a folder has a share link, if so return it... or jsut create a new?
	# https://graph.microsoft.com/v1.0/me/drive/items/root:/graphics/2017/dec/graphics-8_fake-job:/permissions
	request_uri = "{graph_api_endpoint}{graph_user_id}/{graph_action}".format(
		graph_api_endpoint=GRAPH_API_ENDPOINT,
		graph_user_id=' ',
		graph_action='drive/root:/{folder_path}:/permissions'.format(folder_path=job.get_full_folder_path())
	)
	response = session.get(request_uri)
	if response.status_code == 200:
		values = response.json().get('value')
		for value in values:
			if value.get('link') and value['link'].get('type') == 'edit' and value['link'].get('scope') == 'anonymous' and value['link'].get('webUrl'):
				return value['link'].get('webUrl')
	return False
def o365_create_folder_share_link(session, job):
	# 201 == success
	request_uri = "{graph_api_endpoint}{graph_user_id}/{graph_action}".format(
		graph_api_endpoint=GRAPH_API_ENDPOINT,
		graph_user_id=' ',
		graph_action='drive/root:/{folder_path}:/createLink'.format(folder_path=job.get_full_folder_path())
	)	
	data = {
		"type": "edit",
		"scope": "anonymous"		
	}
	response = session.post(request_uri, json=data)
	if response.status_code == 404:
		raise Exception('Folder %s not found on drive.' % job.get_full_folder_path())
	return response

def o365_mkdir_recursive(session, path):
	# shit worries me...
	sub_path = os.path.dirname(path)
	if (sub_path not in ["/", ""]) and not o365_check_if_folder_exists(session, sub_path):
		# how do we handle checking if root exists?
		# if sub_path != '/' or sub_path != '':
		# but if it is root, then it will exist and we can continue on.
		o365_mkdir_recursive(session, sub_path)
	if not o365_check_if_folder_exists(session, path):
		parent_folder_path = sub_path
		new_folder_name = os.path.basename(path)
		if not o365_create_folder(session, parent_folder_path, new_folder_name):
			raise Exception('Could not create folder %s' % path)

def _get_job_root_folder(job):
	return job.ticket.queue.slug

def o365_build_folder_path(session, job):
	# First check if job folder already exists
	
	if not job.ship_date:
		raise Exception('Job needs a ship date before a shared folder can be created.')
	jobs_root_folder = _get_job_root_folder(job)
	year        = str(job.ship_date.year)
	month       = job.ship_date.strftime('%b').lower()
	job_number  = job.get_job_number()
	job_slug    = job.slug
	folder_name = "{job_number}_{job_slug}".format(job_number=job_number, job_slug=job_slug)

	complete_folder_path = os.path.join(jobs_root_folder, year, month, folder_name)
	try:
		o365_mkdir_recursive(session, complete_folder_path)
	except Exception as e:
		raise e

	return complete_folder_path	






