"""ta_app URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
#from django.conf.urls import include as confinclude
#from django.conf.urls import url
from django.conf.urls import handler403, handler403
from ta_app import views, saml_views

urlpatterns = [
    #url(r'^admin/', admin.site.urls),
    #url(r'^impersonate/', confinclude('impersonate.urls')),
    path('accounts/', include('accounts.urls')),
    path('administrators/', include('administrators.urls')),
    path('human_resources/', include('human_resources.urls')),
    path('instructors/', include('instructors.urls')),
    path('students/', include('students.urls')),
    path('summernote/', include('django_summernote.urls')),
    path('impersonate/', include('impersonate.urls')),
    path('saml/', saml_views.saml, name='saml'),
    path('attrs/', saml_views.attrs, name='attrs'),
    path('metadata/', saml_views.metadata, name='metadata'),
    #path('admin/', admin.site.urls),
    #path('accounts/admin/', include('django.contrib.auth.urls'))
]


handler403 = views.permission_denied
handler404 = views.page_not_found
