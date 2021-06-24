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


from django.conf.urls import url
from django.contrib import admin
from django.conf import settings


from pricelists.views import (
    import_pricelist, export_pricelist, export_pricelist_group, 
    create_form, bulk_import_pricelists
)




urlpatterns = [
    url(r'^import/bulk/$', bulk_import_pricelists, name="import"),
    url(r'^import/(?P<pk>\d+)/$', import_pricelist, name="import"),
    url(r'^export/group/(?P<pk>\d+)/$', export_pricelist_group, name="export_group"),
    url(r'^export/(?P<pk>\d+)/$', export_pricelist, name="export"),    
    url(r'^create/$', create_form, name="create_form"),
]
