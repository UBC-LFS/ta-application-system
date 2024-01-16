from django.urls import path
from . import views

app_name = 'observers'

urlpatterns = [
    path('applications/accepted/report', views.AcceptedAppsReportObserver.as_view(), name='accepted_apps_report_observer'),
    path('', views.index, name='index')
]
