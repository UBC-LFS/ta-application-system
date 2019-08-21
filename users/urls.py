from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('', views.index, name='index'),

    path('index/<str:username>/info/edit/', views.edit_user_info, name='edit_user_info'),
    path('index/<str:username>/profile/edit/', views.edit_profile, name='edit_profile'),
    path('delete_user/', views.delete_user, name='delete_user'),
    path('index/<str:username>/', views.show_user, name='show_user'),

    path('students/<str:username>/', views.show_student, name='show_student'),
    path('students/<str:username>/edit/', views.edit_student, name='edit_student'),
    path('students/<str:username>/applied/sessions/<str:session_slug>/jobs/<str:job_slug>/', views.show_student_job, name='show_student_job'),
    path('students/<str:username>/applied/sessions/<str:session_slug>/jobs/<str:job_slug>/accept_offer/', views.accept_offer, name='accept_offer'),
    path('students/<str:username>/applied/sessions/<str:session_slug>/jobs/<str:job_slug>/decline_offer/', views.decline_offer, name='decline_offer'),

    path('students/<str:username>/upload_resume', views.upload_resume, name='upload_resume'),
    path('students/<str:username>/resume/<str:filename>/download/', views.download_resume, name='download_resume'),
    path('delete_resume/', views.delete_resume, name='delete_resume'),

    path('students/<str:username>/submit_confidentiality/', views.submit_confidentiality, name='submit_confidentiality'),
    path('students/<str:username>/study_permit/<str:filename>/download/', views.download_study_permit, name='download_study_permit'),
    path('delete_study_permit/', views.delete_study_permit, name='delete_study_permit'),
    path('students/<str:username>/work_permit/<str:filename>/download/', views.download_work_permit, name='download_work_permit'),
    path('delete_work_permit/', views.delete_work_permit, name='delete_work_permit'),

    path('instructors/<str:username>/', views.show_instructor, name='show_instructor'),
    path('instructors/<str:username>/edit/', views.edit_instructor, name='edit_instructor'),
    path('instructors/<str:username>/sessions/<str:session_slug>/jobs/<str:job_slug>/', views.show_instructor_jobs, name='show_instructor_jobs'),
    path('instructors/<str:username>/sessions/<str:session_slug>/jobs/<str:job_slug>/edit/', views.edit_instructor_jobs, name='edit_instructor_jobs'),

    path('hr/', views.hr, name='hr'),


    path('trainings/', views.trainings, name='trainings'),
    path('trainings/<str:slug>/', views.show_training, name='show_training'),
    path('trainings/<str:slug>/edit/', views.edit_training, name='edit_training'),
    path('delete_training/', views.delete_training, name='delete_training'),

    path('programs/', views.programs, name='programs'),
    path('programs/<str:slug>/', views.show_program, name='show_program'),
    path('programs/<str:slug>/edit/', views.edit_program, name='edit_program'),
    path('delete_program/', views.delete_program, name='delete_program'),

    path('degrees/', views.degrees, name='degrees'),
    path('degrees/<str:slug>/', views.show_degree, name='show_degree'),
    path('degrees/<str:slug>/edit/', views.edit_degree, name='edit_degree'),
    path('delete_degree/', views.delete_degree, name='delete_degree'),

    path('roles/', views.roles, name='roles'),
    path('roles/<str:slug>/', views.show_role, name='show_role'),
    path('roles/<str:slug>/edit/', views.edit_role, name='edit_role'),
    path('delete_role/', views.delete_role, name='delete_role'),

    path('statuses/', views.statuses, name='statuses'),
    path('statuses/<str:slug>/', views.show_status, name='show_status'),
    path('statuses/<str:slug>/edit/', views.edit_status, name='edit_status'),
    path('delete_status/', views.delete_status, name='delete_status'),
]
