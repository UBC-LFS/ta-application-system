from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('', views.index, name='index'),

    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/information/', views.show_profile, name='show_profile'),
    path('profile/resume/upload/', views.upload_resume, name='upload_resume'),
    path('profile/resume/delete/', views.delete_resume, name='delete_resume'),

    path('confidential_information/check/', views.check_confidentiality, name='check_confidentiality'),
    path('confidential_information/submit/', views.submit_confidentiality, name='submit_confidentiality'),
    path('confidential_information/edit/', views.edit_confidentiality, name='edit_confidentiality'),
    path('confidential_information/delete/', views.delete_confidential_information, name='delete_confidential_information'),
    path('confidential_information/', views.show_confidentiality, name='show_confidentiality'),

    path('jobs/explore/', views.explore_jobs, name='explore_jobs'),
    path('jobs/history/', views.history_jobs, name='history_jobs'),
    path('jobs/favourite/', views.favourite_jobs, name='favourite_jobs'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/apply/', views.apply_job, name='apply_job'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/select-favourite-job/', views.select_favourite_job, name='select_favourite_job'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/offered/', views.accept_decline_job, name='accept_decline_job'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/make_decision/', views.make_decision, name='make_decision'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/contract-termination/', views.terminate_job, name='terminate_job'),
    path('sessions/<str:session_slug>/jobs/available/', views.available_jobs, name='available_jobs'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/details/', views.show_job, name='show_job'),

    path('applications/<str:app_slug>/re-accept/', views.reaccept_application, name='reaccept_application'),
    path('applications/<str:app_slug>/', views.show_application, name='show_application'),

    path('download/users/<str:username>/i/<str:item>/files/<str:filename>/', views.download_file, name='download_file')
]
