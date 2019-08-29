from django.urls import path
from . import views

app_name = 'administrators'

urlpatterns = [
    path('', views.index, name='index'),

    path('basics/', views.basics, name='basics'),

    path('sessions/', views.sessions, name='sessions'),
    path('sessions/create', views.create_session, name='create_session'),
    path('sessions/create_session_confirmation/', views.create_session_confirmation, name='create_session_confirmation'),
    path('sessions/current', views.current_sessions, name='current_sessions'),
    path('sessions/archived', views.archived_sessions, name='archived_sessions'),
    path('delete_session/', views.delete_session, name='delete_session'),
    #path('sessions/<str:session_slug>/', views.show_session, name='show_session'),
    path('sessions/<str:session_slug>/edit/', views.edit_session, name='edit_session'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/', views.show_job, name='show_job'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/edit', views.edit_job, name='edit_job'),


    path('jobs/', views.jobs, name='jobs'),
    path('jobs/prepare', views.prepare_jobs, name='prepare_jobs'),
    path('jobs/progress', views.progress_jobs, name='progress_jobs'),
    #path('sessions/<str:session_slug>/jobs/<str:job_slug>/assign_ta_hours', views.assign_ta_hours, name='assign_ta_hours'),
    #path('sessions/<str:session_slug>/jobs/<str:job_slug>/add_instructors', views.add_instructors, name='add_instructors'),



    path('applications/', views.applications, name='applications'),
    path('applications/selected/', views.selected_applications, name='selected_applications'),
    path('applications/offered/', views.offered_applications, name='offered_applications'),
    path('applications/accepted/', views.accepted_applications, name='accepted_applications'),
    path('applications/declined', views.declined_applications, name='declined_applications'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/offer_job', views.offer_job, name='offer_job'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/edit_job_application', views.edit_job_application, name='edit_job_application'),
    path('applications/<str:app_slug>', views.show_application, name='show_application'),


    path('courses/', views.courses, name='courses'),
    #path('courses/<str:course_slug>/', views.show_course, name='show_course'),
    path('courses/create', views.create_course, name="create_course"),
    path('courses/<str:course_slug>/edit/', views.edit_course, name='edit_course'),
    path('delete_course/', views.delete_course, name='delete_course'),

    path('terms/', views.terms, name='terms'),
    path('terms/<str:code>/', views.show_term, name='show_term'),
    path('terms/<str:code>/edit/', views.edit_term, name='edit_term'),
    path('delete_term/', views.delete_term, name='delete_term'),

    path('course_codes/', views.course_codes, name='course_codes'),
    path('course_codes/<str:name>/', views.show_course_code, name='show_course_code'),
    path('course_codes/<str:name>/edit', views.edit_course_code, name='edit_course_code'),
    path('course_codes/delete', views.delete_course_code, name='delete_course_code'),

    path('course_numbers/', views.course_numbers, name='course_numbers'),
    path('course_numbers/<str:name>/', views.show_course_number, name='show_course_number'),
    path('course_numbers/<str:name>/edit', views.edit_course_number, name='edit_course_number'),
    path('course_numbers/delete', views.delete_course_number, name='delete_course_number'),

    path('course_sections/', views.course_sections, name='course_sections'),
    path('course_sections/<str:name>/', views.show_course_section, name='show_course_section'),
    path('course_sections/<str:name>/edit', views.edit_course_section, name='edit_course_section'),
    path('course_sections/delete', views.delete_course_section, name='delete_course_section')

]
