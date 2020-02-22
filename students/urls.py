from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('', views.index, name='index'),

    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/information/<str:tab>/', views.show_profile, name='show_profile'),
    path('profile/resume/upload/', views.upload_resume, name='upload_resume'),
    path('profile/resume/delete/', views.delete_resume, name='delete_resume'),
    path('profile/<str:username>/download/resume/<str:filename>/', views.download_resume, name='download_resume'),

    path('confidential_information/check/', views.check_confidentiality, name='check_confidentiality'),
    path('confidential_information/submit/', views.submit_confidentiality, name='submit_confidentiality'),
    path('confidential_information/edit/', views.edit_confidentiality, name='edit_confidentiality'),
    path('confidential_information/delete/', views.delete_confidential_information, name='delete_confidential_information'),
    #path('confidential_information/sin/delete/', views.delete_sin, name='delete_sin'),
    #path('confidential_information/study_permit/delete/', views.delete_study_permit, name='delete_study_permit'),
    #path('confidential_information/personal_data_form/delete/', views.delete_personal_data_form, name='delete_personal_data_form'),
    path('confidential_information/', views.show_confidentiality, name='show_confidentiality'),
    path('confidential_information/<str:username>/download/personal_data_form/<str:filename>/', views.download_personal_data_form, name='download_personal_data_form'),

    path('jobs/explore/', views.explore_jobs, name='explore_jobs'),
    path('jobs/history/', views.history_jobs, name='history_jobs'),
    path('jobs/favourite/', views.favourite_jobs, name='favourite_jobs'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/apply/', views.apply_job, name='apply_job'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/select-favourite-job/', views.select_favourite_job, name='select_favourite_job'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/offered/', views.accept_decline_job, name='accept_decline_job'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/accept_offer/', views.accept_offer, name='accept_offer'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/decline_offer/', views.decline_offer, name='decline_offer'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/contract-termination/', views.cancel_job, name='cancel_job'),
    path('sessions/<str:session_slug>/jobs/available/', views.available_jobs, name='available_jobs'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/details/', views.show_job, name='show_job'),

    path('applications/<str:app_slug>/re-accept/', views.reaccept_application, name='reaccept_application'),
    path('applications/<str:app_slug>/', views.show_application, name='show_application')

    #path('confidential_information/<str:username>/download/sin/<str:filename>/', views.download_sin, name='download_sin'),
    #path('confidential_information/<str:username>/download/study_permit/<str:filename>/', views.download_study_permit, name='download_study_permit'),
]
