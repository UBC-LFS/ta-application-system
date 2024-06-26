from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('', views.Index.as_view(), name='index'),

    path('profile/edit/', views.EditProfile.as_view(), name='edit_profile'),
    path('profile/reminder/confirm/', views.confirm_profile_reminder, name='confirm_profile_reminder'),
    path('profile/information/ta/update/', views.update_profile_ta, name='update_profile_ta'),
    path('profile/information/', views.ShowProfile.as_view(), name='show_profile'),
    path('profile/resume/upload/', views.upload_resume, name='upload_resume'),
    path('profile/resume/delete/', views.delete_resume, name='delete_resume'),

    path('confidential_information/check/', views.check_confidentiality, name='check_confidentiality'),
    path('confidential_information/submit/', views.submit_confidentiality, name='submit_confidentiality'),
    path('confidential_information/edit/', views.EditConfidentiality.as_view(), name='edit_confidentiality'),
    path('confidential_information/delete/', views.delete_confidential_information, name='delete_confidential_information'),
    path('confidential_information/', views.show_confidentiality, name='show_confidentiality'),

    path('jobs/explore/', views.ExploreJobs.as_view(), name='explore_jobs'),
    path('jobs/history/', views.history_jobs, name='history_jobs'),
    path('jobs/favourite/', views.favourite_jobs, name='favourite_jobs'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/apply/', views.ApplyJob.as_view(), name='apply_job'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/select-favourite-job/', views.select_favourite_job, name='select_favourite_job'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/offered/', views.accept_decline_job, name='accept_decline_job'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/make_decision/', views.make_decision, name='make_decision'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/contract-termination/', views.terminate_job, name='terminate_job'),
    path('sessions/<str:session_slug>/jobs/available/', views.AvailableJobs.as_view(), name='available_jobs'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/details/', views.show_job, name='show_job'),

    path('applications/<str:app_slug>/re-accept/', views.reaccept_application, name='reaccept_application'),
    path('applications/<str:app_slug>/', views.show_application, name='show_application'),

    path('download/users/<str:username>/i/<str:item>/files/<str:filename>/', views.download_file, name='download_file')
]
