from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('', views.index, name='index'),
    path('profile/', views.show_profile, name='show_profile'),
    path('profile/<str:username>/edit/', views.edit_profile, name='edit_profile'),
    path('profile/<str:username>/confidentiality/submit/', views.submit_confidentiality, name='submit_confidentiality'),
    path('profile/<str:username>/upload_resume', views.upload_resume, name='upload_resume'),
    path('profile/<str:username>/resume/<str:filename>/download/', views.download_resume, name='download_resume'),
    path('profile/delete_resume/', views.delete_resume, name='delete_resume'),

    path('confidentiality/', views.show_confidentiality, name='show_confidentiality'),
    path('confidentiality/check/', views.check_confidentiality, name='check_confidentiality'),
    path('confidentiality/submit/', views.submit_confidentiality, name='submit_confidentiality'),
    path('confidentiality/<str:username>/study_permit/<str:filename>/download/', views.download_study_permit, name='download_study_permit'),
    path('confidentiality/study_permit/delete_/', views.delete_study_permit, name='delete_study_permit'),
    path('confidentiality/<str:username>/work_permit/<str:filename>/download/', views.download_work_permit, name='download_work_permit'),
    path('confidentiality/work_permit/delete/', views.delete_work_permit, name='delete_work_permit'),

    path('jobs/explore/', views.explore_jobs, name='explore_jobs'),
    path('jobs/<str:session_slug>/list/', views.list_jobs, name='list_jobs'),
    path('jobs/<str:session_slug>/jobs/<str:job_slug>/apply/', views.apply_job, name='apply_job'),
    path('jobs/applied/', views.applied_jobs, name='applied_jobs'),
    path('jobs/offered/', views.offered_jobs, name='offered_jobs'),
    path('jobs/accepted/', views.accepted_jobs, name='accepted_jobs'),
    path('jobs/declined/', views.declined_jobs, name='declined_jobs'),

    #path('students/<str:username>/', views.show_student, name='show_student'),
    #path('students/<str:username>/edit/', views.edit_student, name='edit_student'),
    #path('students/<str:username>/applied/sessions/<str:session_slug>/jobs/<str:job_slug>/', views.show_student_job, name='show_student_job'),
    #path('students/<str:username>/applied/sessions/<str:session_slug>/jobs/<str:job_slug>/accept_offer/', views.accept_offer, name='accept_offer'),
    #path('students/<str:username>/applied/sessions/<str:session_slug>/jobs/<str:job_slug>/decline_offer/', views.decline_offer, name='decline_offer'),

    #path('students/<str:username>/upload_resume', views.upload_resume, name='upload_resume'),
    #path('students/<str:username>/resume/<str:filename>/download/', views.download_resume, name='download_resume'),
    #path('delete_resume/', views.delete_resume, name='delete_resume'),




]
