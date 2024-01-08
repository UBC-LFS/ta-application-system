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
from django.conf import settings
from django.conf.urls import handler400, handler403, handler404, handler500
from ta_app import views

urlpatterns = [
    path('app/users/', include('users.urls')),
    path('app/administrators/', include('administrators.urls')),
    path('app/instructors/', include('instructors.urls')),
    path('app/students/', include('students.urls')),
    path('app/observers/', include('observers.urls')),
    path('app/summernote/', include('django_summernote.urls')),
    path('app/impersonate/', include('impersonate.urls')),

    path('app/', views.app_home, name='app_home'),
    path('logout/', views.site_logout, name='logout'),
    path('', views.landing_page, name='landing_page')
]

if settings.DEBUG:
    urlpatterns += [
        path('admin/', admin.site.urls)
    ]

if settings.LOCAL_LOGIN:
    urlpatterns += [
        path('accounts/', include('accounts.urls'))
    ]

handler400 = views.bad_request
handler403 = views.permission_denied
handler404 = views.page_not_found
handler500 = views.internal_server_error