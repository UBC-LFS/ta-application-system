from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('index/', views.users, name='users'),
    path('index/create', views.create_user, name='create_user'),

    path('index/<str:username>/info/edit/', views.edit_user_info, name='edit_user_info'),
    path('index/<str:username>/profile/edit/', views.edit_profile, name='edit_profile'),
    path('delete_user/', views.delete_user, name='delete_user'),
    path('index/<str:username>/', views.show_user, name='show_user'),


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
