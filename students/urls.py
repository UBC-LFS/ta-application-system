from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('', views.index, name='index'),
    path('profile/', views.show_profile, name='show_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/resume/upload/', views.upload_resume, name='upload_resume'),
    path('profile/resume/delete/', views.delete_resume, name='delete_resume'),
    path('profile/<str:username>/resume/<str:filename>/download/', views.download_resume, name='download_resume'),

    path('confidentiality/check/', views.check_confidentiality, name='check_confidentiality'),
    path('confidentiality/submit/', views.submit_confidentiality, name='submit_confidentiality'),
    path('confidentiality/edit/', views.edit_confidentiality, name='edit_confidentiality'),
    path('confidentiality/sin/delete/', views.delete_sin, name='delete_sin'),
    path('confidentiality/study_permit/delete/', views.delete_study_permit, name='delete_study_permit'),
    path('confidentiality/', views.show_confidentiality, name='show_confidentiality'),
    path('confidentiality/<str:username>/sin/<str:filename>/download/', views.download_sin, name='download_sin'),
    path('confidentiality/<str:username>/study_permit/<str:filename>/download/', views.download_study_permit, name='download_study_permit'),

    path('jobs/explore/', views.explore_jobs, name='explore_jobs'),
    path('jobs/history/', views.history_jobs, name='history_jobs'),
    path('jobs/favourite/', views.favourite_jobs, name='favourite_jobs'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/apply/', views.apply_job, name='apply_job'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/select-favourite-job/', views.select_favourite_job, name='select_favourite_job'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/offered/', views.accept_decline_job, name='accept_decline_job'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/accept_offer/', views.accept_offer, name='accept_offer'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/decline_offer/', views.decline_offer, name='decline_offer'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/cancel/', views.cancel_job, name='cancel_job'),
    path('sessions/<str:session_slug>/jobs/available/', views.available_jobs, name='available_jobs'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/details/', views.show_job, name='show_job'),

    path('applications/<str:app_slug>/', views.show_application, name='show_application')

    #path('profile/<str:username>/confidentiality/submit/', views.submit_confidentiality, name='submit_confidentiality')
]
