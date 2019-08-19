from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    path('', views.index, name='index'),
    path('sessions/<str:session_slug>/', views.show_session, name='show_session'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/', views.show_job, name='show_job')
]
