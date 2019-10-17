from django.urls import path
from . import views

app_name = 'administrators'

urlpatterns = [
    path('', views.index, name='index'),

    path('courses/all/', views.all_courses, name='all_courses'),
    path('courses/create/', views.create_course, name='create_course'),
    path('courses/delete/', views.delete_course, name='delete_course'),
    path('courses/<str:course_slug>/edit/', views.edit_course, name='edit_course'),
    path('courses/', views.courses, name='courses'),

    path('sessions/create/confirmation/', views.create_session_confirmation, name='create_session_confirmation'),
    path('sessions/create/', views.create_session, name='create_session'),
    path('sessions/delete/path/<str:path>/', views.delete_session, name='delete_session'),
    path('sessions/<str:session_slug>/edit/p/<str:path>/', views.edit_session, name='edit_session'),
    path('sessions/<str:session_slug>/p/<str:path>/', views.show_session, name='show_session'),
    path('sessions/current/', views.current_sessions, name='current_sessions'),
    path('sessions/archived/', views.archived_sessions, name='archived_sessions'),
    path('sessions/', views.sessions, name='sessions'),

    path('jobs/prepare/', views.prepare_jobs, name='prepare_jobs'),
    path('jobs/progress/', views.progress_jobs, name='progress_jobs'),
    path('jobs/student/', views.student_jobs, name='student_jobs'),
    path('jobs/instructor/', views.instructor_jobs, name='instructor_jobs'),
    path('jobs/', views.jobs, name='jobs'),
    path('instructors/<str:username>/jobs/', views.instructor_jobs_details, name='instructor_jobs_details'),
    path('students/<str:username>/jobs/', views.student_jobs_details, name='student_jobs_details'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/edit/', views.edit_job, name='edit_job'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/applications/', views.show_job_applications, name='show_job_applications'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/p/<str:path>/', views.show_job, name='show_job'),

    path('applications/offered/send_email/confirmation/', views.offered_applications_send_email_confirmation, name='offered_applications_send_email_confirmation'),
    path('applications/offered/send_email/', views.offered_applications_send_email, name='offered_applications_send_email'),

    path('sessions/<str:session_slug>/jobs/<str:job_slug>/offer/', views.offer_job, name='offer_job'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/application/edit/', views.edit_job_application, name='edit_job_application'),
    path('applications/offered/email_history/', views.email_history, name='email_history'),
    path('emails/<str:email_id>/reminder/', views.send_reminder, name='send_reminder'),
    path('applications/decline_reassign/confirmation/', views.decline_reassign_confirmation, name='decline_reassign_confirmation'),
    path('applications/decline_reassign/', views.decline_reassign, name='decline_reassign'),

    path('applications/dashboard/', views.applications_dashboard, name='applications_dashboard'),
    path('applications/all/', views.all_applications, name='all_applications'),
    path('applications/selected/', views.selected_applications, name='selected_applications'),
    path('applications/offered/', views.offered_applications, name='offered_applications'),
    path('applications/accepted/', views.accepted_applications, name='accepted_applications'),
    path('applications/declined/', views.declined_applications, name='declined_applications'),
    #path('applications/<str:username>/jobs/accepted/', views.show_user_accepted_job_summary, name='show_user_accepted_job_summary'),
    path('applications/<str:app_slug>/p/<str:path>/', views.show_application, name='show_application'),
    path('applications/', views.applications, name='applications'),


    path('hr/users/<str:username>/confidentiality/', views.view_confidentiality, name='view_confidentiality'),
    path('hr/users/create/', views.create_user, name='create_user'),
    path('hr/users/delete/', views.delete_user, name='delete_user'),
    path('hr/users/<str:username>/p/<str:path>/', views.show_user, name='show_user'),
    path('hr/users/all/', views.users, name='users'),
    path('hr/roles/delete/', views.delete_role, name='delete_role'),
    path('hr/roles/<str:slug>/edit/', views.edit_role, name='edit_role'),
    path('hr/roles/', views.roles, name='roles'),
    path('hr/', views.hr, name='hr'),

    path('preparation/terms/delete/', views.delete_term, name='delete_term'),
    path('preparation/terms/<str:code>/edit/', views.edit_term, name='edit_term'),
    path('preparation/terms/', views.terms, name='terms'),

    path('preparation/course_codes/delete/', views.delete_course_code, name='delete_course_code'),
    path('preparation/course_codes/<str:name>/edit/', views.edit_course_code, name='edit_course_code'),
    path('preparation/course_codes/', views.course_codes, name='course_codes'),

    path('preparation/course_numbers/delete/', views.delete_course_number, name='delete_course_number'),
    path('preparation/course_numbers/<str:name>/edit/', views.edit_course_number, name='edit_course_number'),
    path('preparation/course_numbers/', views.course_numbers, name='course_numbers'),

    path('preparation/course_sections/delete/', views.delete_course_section, name='delete_course_section'),
    path('preparation/course_sections/<str:name>/edit/', views.edit_course_section, name='edit_course_section'),
    path('preparation/course_sections/', views.course_sections, name='course_sections'),

    path('preparation/statuses/delete/', views.delete_status, name='delete_status'),
    path('preparation/statuses/<str:slug>/edit/', views.edit_status, name='edit_status'),
    path('preparation/statuses/', views.statuses, name='statuses'),

    path('preparation/programs/delete/', views.delete_program, name='delete_program'),
    path('preparation/programs/<str:slug>/edit/', views.edit_program, name='edit_program'),
    path('preparation/programs/', views.programs, name='programs'),

    path('preparation/degrees/delete/', views.delete_degree, name='delete_degree'),
    path('preparation/degrees/<str:slug>/edit/', views.edit_degree, name='edit_degree'),
    path('preparation/degrees/', views.degrees, name='degrees'),

    path('preparation/trainings/delete/', views.delete_training, name='delete_training'),
    path('preparation/trainings/<str:slug>/edit/', views.edit_training, name='edit_training'),
    path('preparation/trainings/', views.trainings, name='trainings'),

    path('preparation/classifications/delete/', views.delete_classification, name='delete_classification'),
    path('preparation/classifications/<str:slug>/edit/', views.edit_classification, name='edit_classification'),
    path('preparation/classifications/', views.classifications, name='classifications'),

    path('preparation/', views.preparation, name='preparation'),

    #path('sessions/<str:session_slug>/jobs/<str:job_slug>/assign_ta_hours', views.assign_ta_hours, name='assign_ta_hours'),
    #path('sessions/<str:session_slug>/jobs/<str:job_slug>/add_instructors', views.add_instructors, name='add_instructors'),

]
