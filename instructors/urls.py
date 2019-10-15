from django.urls import path
from . import views

app_name = 'instructors'

urlpatterns = [
    path('', views.index, name='index'),
    path('profile/', views.profile, name='profile'),
    path('my_jobs/', views.my_jobs, name='my_jobs'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/edit/', views.edit_job, name='edit_job'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/applications/', views.get_applications, name='get_applications'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/', views.show_job, name='show_job')
]
