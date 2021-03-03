from django.urls import path
from . import views

app_name = 'observers'

urlpatterns = [
    path('report/accepted-applications/', views.report_accepted_applications, name='report_accepted_applications'),
    path('', views.index, name='index')
]
