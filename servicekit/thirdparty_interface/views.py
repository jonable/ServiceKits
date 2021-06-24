# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

# Create your views here.


from allauth.account.views import LogoutView


class LogoutViewPatch(LogoutView):
	# Login View eXtended

	# beware ordering and collisions on paths
	template_name = "allauth/account/logout.html"

	# don't forget to create the login page, see All Auth docs
	# for use. /components is in your app templates path

allauth_logout_patch = login = LogoutViewPatch.as_view()

# when users signs up with office365 social login using alluth, they are automatically made a staff memeber
from django.conf import settings
from django.dispatch import receiver

from django.contrib.auth.models import User
from allauth.socialaccount import app_settings
from allauth.socialaccount.signals import social_account_added, pre_social_login, social_account_updated
from allauth.account.utils import perform_login
# from allauth.account.models import EmailAddress
from allauth.account.signals import user_signed_up


@receiver(user_signed_up)
def user_signed_up_(request, user, sociallogin=None, **kwargs):
	if sociallogin:
		user.is_active = True
		if user.email:
			username, domain = user.email.split('@')
			if domain in settings.O365_VALID_DOMAINS:
					user.is_staff = True
		user.save()					
		from allauth.account.models import EmailAddress
		emails = EmailAddress.objects.filter(user=user, verified=False)
		for email in emails:
			email.verified=True
			email.save()

# office 365 views.
from uuid import uuid4
from thirdparty_interface.utils.o365_helper import o365_get_admin_consent_url
from django.http import HttpResponse, HttpResponseRedirect
def o365_admin_consent_view(request):
	state = str(uuid4())
	request.session['o365_state_token'] = state
	admin_consent_url = o365_get_admin_consent_url(request.is_secure(), state)
	return HttpResponseRedirect(admin_consent_url)


def o365_admin_consent_callback(request):
	# // Line breaks are for legibility only.
	# response 
	# GET http://localhost/myapp/permissions
	# ?tenant=a8990e1f-ff32-408a-9f8e-78d3b9139b95&state=state=12345
	# &admin_consent=True	
	# should check state...
	request.GET.get('admin_consent')
	returned_state_token = request.GET.get('state')
	session_state_token = request.session.get('o365_state_token')
	if returned_state_token != session_state_token:
		raise Exception('State token mismatch - check for a valid response from office365.')
	del request.session['o365_state_token']
	return HttpResponse('<h1>%s</h1>' % request.GET.get('admin_consent'))


# from thirdparty_interface.utils.o365_helper import *
# from jobs.models import Job
# job = Job.objects.get(pk=8)
# job.get_full_folder_path()
# import requests
# session = requests.Session()
# response = o365_admin_get_access_token(session)
# response
# response.headers
# session.headers
# o365_check_if_folder_exists(job.get_full_folder_path())
# o365_check_if_folder_exists(session, job.get_full_folder_path())
# o365_build_folder_path(session,job)
# o365_build_folder_path(session,job)
# o365_build_folder_path(session,job)
# response = o365_create_folder_share_link(session, job)
# response.json()
# response.json()['link']['webUrl']
# %history
