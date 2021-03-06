"""
Django settings for ServiceKit project.

Generated by 'django-admin startproject' using Django 1.10rc1.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""

import os
import sys

RUNNING_DEVSERVER = (len(sys.argv) > 1 and sys.argv[1] == 'runserver')	

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/dev/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ''

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost']


# Application definition

INSTALLED_APPS = [
	# 'grappelli',
	'filebrowser',
	'django.contrib.admin',
	'django.contrib.auth',
	'django.contrib.contenttypes',
	'django.contrib.sessions',
	'django.contrib.messages',
	'django.contrib.staticfiles',
	'django.contrib.sites',
	'django.contrib.humanize',
	'allauth',
	'allauth.account',
	'allauth.socialaccount',
	'allauth_office365',
	'easy_select2',
	'formtools',
	'background_task',
	'thirdparty_interface',
	'pricelists',
	'kitcreate',
	'sortedm2m',	
	# 'adminsortable',
]

MIDDLEWARE_CLASSES = [
	'django.middleware.security.SecurityMiddleware',
	'django.contrib.sessions.middleware.SessionMiddleware',
	'django.middleware.common.CommonMiddleware',
	'django.middleware.csrf.CsrfViewMiddleware',
	'django.contrib.auth.middleware.AuthenticationMiddleware',
	'django.contrib.messages.middleware.MessageMiddleware',
	'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'servicekit.urls'

TEMPLATES = [
	{
		'BACKEND': 'django.template.backends.django.DjangoTemplates',
		'DIRS': [
			os.path.join(BASE_DIR, 'templates'),
			os.path.join(BASE_DIR, 'templates', 'allauth')
		],
		'APP_DIRS': True,
		'OPTIONS': {
			'context_processors': [
				'django.template.context_processors.debug',
				'django.template.context_processors.request',
				'django.contrib.auth.context_processors.auth',
				'django.contrib.messages.context_processors.messages',

			],
		},
	},
]

WSGI_APPLICATION = 'servicekit.wsgi.application'


# Database
# https://docs.djangoproject.com/en/dev/ref/settings/#databases

DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.sqlite3',
		'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
	}
}


# Password validation
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
	{
		'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
	},
	{
		'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
	},
	{
		'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
	},
	{
		'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
	},
]


# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_INPUT_FORMATS = [
	'%I:%M %p',
	'%H:%M'
]

TIME_ZONE = 'America/New_York'

USE_I18N = True

USE_L10N = True

# USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/

# STATIC_ROOT = os.path.abspath(os.path.join(BASE_DIR, 'static'))
STATIC_URL = '/static/'
STATICFILES_DIRS  = [
    os.path.join(BASE_DIR, 'static'),   
]

SITE_ID = 3

# FileBrowser works with FileStorage thing from django
# site. something sets a lot of this? idk
# MEDIA_ROOT = os.path.join(BASE_DIR, 'uploads')
# MEDIA_URL = '/admin/filebrowser/detail/uploads/'
# this will cause issues....
MEDIA_URL = '/'
FILEBROWSER_DIRECTORY = 'uploads/'
DIRECTORY = 'uploads/'
MEDIA_ROOT = './ServiceKit/servicekit'
# App specific settings
# 
# FileBrowser
# FILEBROWSER_OVERWRITE_EXISTING = True

# KitForms
KITFORMS_DOCFORMS_DIR = 'documents/forms/'
KITFORMS_DEFAULT_SERVICEKIT_ORDER = 'default_form_order'

ADMINS = [
	("", ""),
]

EPMIDDLEWARE_API_ENDPOINT              = ''
EPMIDDLEWARE_API_UPDATEEVENTS_ENDPOINT = ''
EPMIDDLEWARE_API_UPDATEPLACES_ENDPOINT = ''
DISCOUNT_DATE_DAYS                     = 7
ADVANCE_SHIP_DATE_DAYS                 = 30
CARRIER_PICKUP_HOURS                   = 2.0
EXPIRED_DAYS_THRESHOLD                 = 45

# FORM_VERSION = "v2"
FORM_VERSION = "v1"
# NETSHARE_PDF_REPO =  os.path.join(os.path.expanduser('~'),'.gvfs/data on sbsrv/Web PDF\'s')
NETSHARE_PDF_REPO =  os.path.join(os.path.expanduser('~'), 'Desktop')

DEFAULT_IGNORED_MERGEFIELDS = [
	'advance_ship_date',
	'direct_ship_date',
	'discount_date',
	'event_header_date',
	'event_name',
	'facility',
	'facility_address1',
	'facility_address2',
	'facility_city',
	'facility_state',
	'facility_title',
	'facility_zip',
	'terminal_address1',
	'terminal_address2',
	'terminal_city',
	'terminal_state',
	'terminal_title',
	'terminal_zip',
	'thirty_days_prior'
]


SERVER_EMAIL = ' '
DEFAULT_FROM_EMAIL = SERVER_EMAIL
# EMAIL_BACKEND = 'common.emailbackend.SEREmailBackend'

EMAIL_HOST_USER = ' '
EMAIL_HOST_PASSWORD = ' ' 
EMAIL_HOST = ' '
EMAIL_PORT = 587
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = True

SOCIALACCOUNT_ADAPTER = 'allauth_office365.adapter.SocialAccountAdapter'
SOCIALACCOUNT_PROVIDERS = {
	'office365': {
	  'SCOPE': ['User.read',],
	  'USERNAME_FIELD': 'mail',
	  'TENANT': 'serexpo.onmicrosoft.com'
	}
}

O365_VALID_DOMAINS = ['', '']



