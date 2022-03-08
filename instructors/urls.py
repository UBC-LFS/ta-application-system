from django.urls import path
from . import views

app_name = 'instructors'

urlpatterns = [
    path('', views.index, name='index'),
    path('users/edit/', views.edit_user, name='edit_user'),
    path('jobs/', views.show_jobs, name='show_jobs'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/edit/', views.edit_job, name='edit_job'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/applications/', views.show_applications, name='show_applications'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/details/', views.show_job, name='show_job'),
    path('sessions/<str:session_slug>/applicants/summary-applicants/', views.summary_applicants, name='summary_applicants'),
    path('applications/<str:app_slug>/write-note/', views.write_note, name='write_note')
]
