"""ServiceKit URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/dev/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

from django.views.generic.base import RedirectView
from django.conf.urls import url, include
from django.contrib import admin
# from django.views.generic.base import RedirectView
from django.conf.urls.static import static
from django.conf import settings

from filebrowser.sites import site as filebrowser_site

# from kitcreate.views import (
#     ServiceKitWizard2, fetch_event_data, wizard_complete, 
#     create_service_kit, EventInfoListView, download_service_kit, 
#     update_all_events, select_form, demo_popup_main, 
#     demo_popup_window, DeleteEventInfoView, file_upload,
#     ServiceKitFormListView, quick_export, update_kit_status, 
#     InternalNoteUpdateView, storefrontstatus_update,StorefrontstatusListView,
#     storefrontstatus_quickinfo, send_status_message, copy_to_network_drive, 
#     view_kit_archive, update_all_places, ServicekitstatusListView, 
#     servicekitstatus_update, expire_servicekits, internal_files,
#     create_service_kit_queue, fix_broken_servicekit, view_service_kit
# )
from kitcreate import views as kitcreate_views
from kitcreate.views import wizard

# from django.conf.urls import handler404, handler500
# handler404 = 'kitcreate.views.handler404'
# handler500 = 'kitcreate.views.handler500'

from thirdparty_interface.views import allauth_logout_patch, o365_admin_consent_callback, o365_admin_consent_view

urlpatterns = [
   url(r'^admin/filebrowser/', filebrowser_site.urls),
    url(r'^admin/', admin.site.urls),
    url(r'^favicon\.ico$', RedirectView.as_view(url='/static/favicon.ico', permanent=True)),

    # this will fail in development

    # allauth + office365
    url(r'^accounts/logout/$', allauth_logout_patch), # patch fix for allauth issue with loading project templates for ovveride
    url(r'^accounts/', include('allauth.urls')),
    url(r'^o365admin/consent/$', o365_admin_consent_view, name="o365_admin_consent_view"),
    url(r'^o365admin/callback/$', o365_admin_consent_callback, name="o365_admin_consent_callback"), 

    url(r'^select/$', kitcreate_views.select_form, name="wizard_select_type"),
   
    url(r'^kits/(?P<pk>\d+)/$', wizard.EventInfoChange.as_view(), name="servicekit_wizard_change"),
    url(r'^kits/$', wizard.EventInfoCreate.as_view(), name="servicekit_wizard2_new"),

    # url(r'^kits/$', kitcreate_views.ServiceKitWizard2.as_view(), name="servicekit_wizard2_new"),


    url(r'^kits/edit/info/(?P<pk>\d+)/$', wizard.EventInfoChange.as_view(), name="edit_kit_info"),
    url(r'^kits/edit/schedule/(?P<pk>\d+)/$', wizard.EventScheduleChange.as_view(), name="edit_kit_schedule"),
    url(r'^kits/edit/pricelevel/(?P<pk>\d+)/$', wizard.PriceLevelChange.as_view(), name="edit_kit_pricelevel"),
    url(r'^kits/edit/services/(?P<pk>\d+)/$', wizard.ServicesChange.as_view(), name="edit_kit_services"),
    url(r'^kits/edit/addforms/(?P<pk>\d+)/$', wizard.AdditionalFormChange.as_view(), name="edit_kit_addforms"),

    
    url(r'^kits/fix_broken_servicekit/(?P<eventinfo_pk>\d+)/(?P<servicekit_pk>\d+)/$', kitcreate_views.fix_broken_servicekit, name="fix_broken_servicekit"),

    url(r'^kits/complete/(?P<pk>\d+)/$', kitcreate_views.wizard_complete, name="servicekit_complete"),
    
    url(r'^kits/queue/(?P<eventinfo_pk>\d+)/(?P<task_pk>\d+)/$', kitcreate_views.create_service_kit_queue, name="create_service_kit_queue"),

    url(r'^kits/create/(?P<pk>\d+)/$', kitcreate_views.create_service_kit, name="create_service_kit"),
    url(r'^kits/download/(?P<pk>\d+)/$', kitcreate_views.download_service_kit, name="download_service_kit"),
    url(r'^kits/view/(?P<pk>\d+)/$', kitcreate_views.view_service_kit, name="view_service_kit"),    
    url(r'^kits/copytoidrive/(?P<pk>\d+)/$', kitcreate_views.copy_to_network_drive, name="copy_to_network_drive"),
    url(r'^kits/archive/(?P<pk>\d+)/$', kitcreate_views.view_kit_archive, name="view_kit_archive"),
    url(r'^kits/storefrontstatus/$', kitcreate_views.StorefrontstatusListView.as_view(), name="storefrontstatus_list"),
    url(r'^kits/storefrontstatus/(?P<pk>\d+)/update/$', kitcreate_views.storefrontstatus_update, name="storefrontstatus_update"),
    url(r'^kits/storefrontdata/(?P<pk>\d+)/$', kitcreate_views.storefrontstatus_quickinfo, name="goshow_quick_notes"),


    # url(r'^kits/servicekitstatus/$', ServicekitstatusListView.as_view(), name="serviceskitstatus_listview"),
    url(r'^kits/servicekitstatus/update/(?P<pk>\d+)/$', kitcreate_views.servicekitstatus_update, name="serviceskitstatus_status_update"),


    url(r'^kits/status/update/(?P<pk>\d+)/$', kitcreate_views.update_kit_status, name="update_kit_status"),
    url(r'^kits/status/msg/(?P<pk>\d+)/$', kitcreate_views.send_status_message, name="send_status_message"),
    

    url(r'^kits/quickexport/(?P<pk>\d+)/$', kitcreate_views.quick_export, name="quick_export_form"),
    
    url(r'^kits/updatevents/$', kitcreate_views.update_all_events, name="update_all_events"),
    url(r'^kits/updateplaces/$', kitcreate_views.update_all_places, name="update_all_places"),
    url(r'^kits/expireservicekits/$', kitcreate_views.expire_servicekits, name="expire_servicekits"),
    url(r'^kits/fileupload/$', kitcreate_views.file_upload, name="file_upload_form"),
    url(r'^kits/fileupload/(?P<pk>\d+)/$', kitcreate_views.file_upload, name="file_edit_form"),
    

    url(r'^api/v1/event/(?P<pk>\d+)/$', kitcreate_views.fetch_event_data, name="api__fetch_event_data"),
    
    url(r'^popupmain/$', kitcreate_views.demo_popup_main),
    url(r'^popupwin/(?P<pk>\d+)/$', kitcreate_views.demo_popup_window),

    url(r'^kits/formslist/$', kitcreate_views.ServiceKitFormListView.as_view(), name="servicekitforms_listview"),

    url(r'^kits/delete/(?P<pk>\d+)/$', kitcreate_views.DeleteEventInfoView.as_view(), name="delete_service_kit"),
    
    url(r'kits/internal_note/update/(?P<pk>[0-9]+)/$', kitcreate_views.InternalNoteUpdateView.as_view(), name='eventinfo_internal_note_update'),
       
    url(r'^pricelists/', include('pricelists.urls', namespace="pricelists")),

    # url(r'^$',EventInfoListView.as_view(), name="kitcreate_home"),    
    url(r'^$', kitcreate_views.ServicekitstatusListView.as_view(), name="serviceskitstatus_listview"),
    url(r'^$', kitcreate_views.ServicekitstatusListView.as_view(), name="kitcreate_home"),
]


if settings.RUNNING_DEVSERVER:
    urlpatterns = urlpatterns+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)+static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    urlpatterns.append(url(r'^uploads/', kitcreate_views.internal_files, name="internal_files"))



# import logging
# logger = logging.getLogger('django')   # Django's catch-all logger
# hdlr = logging.StreamHandler()   # Logs to stderr by default
# formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
# hdlr.setFormatter(formatter)
# logger.addHandler(hdlr) 
# logger.setLevel(logging.WARNING)
# logger.warn('CHANGE MEDIA_URL SERVER IN PRODUCTION')
