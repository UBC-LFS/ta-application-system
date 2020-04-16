from django.urls import path
from . import views

app_name = 'administrators'

urlpatterns = [
    path('', views.index, name='index'),

    path('sessions/create/confirmation/', views.create_session_confirmation, name='create_session_confirmation'),
    path('sessions/create/', views.create_session, name='create_session'),
    path('sessions/<str:session_slug>/delete/confirmation/', views.delete_session_confirmation, name='delete_session_confirmation'),
    path('sessions/<str:session_slug>/edit/', views.edit_session, name='edit_session'),
    path('sessions/<str:session_slug>/details/', views.show_session, name='show_session'),
    path('sessions/current/', views.current_sessions, name='current_sessions'),
    path('sessions/archived/', views.archived_sessions, name='archived_sessions'),

    path('jobs/prepare/', views.prepare_jobs, name='prepare_jobs'),
    path('jobs/progress/', views.progress_jobs, name='progress_jobs'),
    path('jobs/student/', views.student_jobs, name='student_jobs'),
    path('jobs/instructor/', views.instructor_jobs, name='instructor_jobs'),
    path('instructors/search/', views.search_instructors, name='search_instructors'),
    path('instructors/<str:username>/jobs/', views.instructor_jobs_details, name='instructor_jobs_details'),
    path('students/<str:username>/jobs/', views.student_jobs_details, name='student_jobs_details'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/edit/', views.edit_job, name='edit_job'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/applications/', views.show_job_applications, name='show_job_applications'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/details/', views.show_job, name='show_job'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/instructors/add/', views.add_job_instructors, name='add_job_instructors'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/instructors/delete/', views.delete_job_instructors, name='delete_job_instructors'),

    path('applications/send_email/confirmation/', views.applications_send_email_confirmation, name='applications_send_email_confirmation'),
    path('applications/send_email/', views.applications_send_email, name='applications_send_email'),

    path('sessions/<str:session_slug>/jobs/<str:job_slug>/offer/', views.offer_job, name='offer_job'),
    path('applications/email_history/', views.email_history, name='email_history'),
    path('emails/<str:email_id>/reminder/', views.send_reminder, name='send_reminder'),
    path('applications/decline_reassign/confirmation/', views.decline_reassign_confirmation, name='decline_reassign_confirmation'),
    path('applications/decline_reassign/', views.decline_reassign, name='decline_reassign'),
    path('applications/<str:app_slug>/terminate/', views.terminate, name='terminate'),

    path('applications/dashboard/', views.applications_dashboard, name='applications_dashboard'),
    path('applications/all/', views.all_applications, name='all_applications'),
    path('applications/selected/', views.selected_applications, name='selected_applications'),
    path('applications/offered/', views.offered_applications, name='offered_applications'),
    path('applications/accepted/', views.accepted_applications, name='accepted_applications'),
    path('applications/declined/', views.declined_applications, name='declined_applications'),
    path('applications/terminated/', views.terminated_applications, name='terminated_applications'),
    path('applications/<str:app_slug>/details/', views.show_application, name='show_application'),

    path('hr/users/<str:username>/edit/', views.edit_user, name='edit_user'),
    path('hr/users/<str:username>/delete/confirmation/', views.delete_user_confirmation, name='delete_user_confirmation'),
    path('hr/users/all/', views.all_users, name='all_users'),
    path('hr/users/destroy/contents/', views.destroy_user_contents, name='destroy_user_contents'),
    path('hr/users/create/', views.create_user, name='create_user'),

    path('hr/roles/<str:slug>/edit/', views.edit_role, name='edit_role'),
    path('hr/roles/delete/', views.delete_role, name='delete_role'),
    path('hr/roles/', views.roles, name='roles'),

    path('courses/all/', views.all_courses, name='all_courses'),
    path('courses/create/', views.create_course, name='create_course'),
    path('courses/delete/', views.delete_course, name='delete_course'),
    path('courses/<str:course_slug>/edit/', views.edit_course, name='edit_course'),

    path('preparation/terms/delete/', views.delete_term, name='delete_term'),
    path('preparation/terms/<int:term_id>/edit/', views.edit_term, name='edit_term'),
    path('preparation/terms/', views.terms, name='terms'),

    path('preparation/course_codes/delete/', views.delete_course_code, name='delete_course_code'),
    path('preparation/course_codes/<int:course_code_id>/edit/', views.edit_course_code, name='edit_course_code'),
    path('preparation/course_codes/', views.course_codes, name='course_codes'),

    path('preparation/course_numbers/delete/', views.delete_course_number, name='delete_course_number'),
    path('preparation/course_numbers/<int:course_number_id>/edit/', views.edit_course_number, name='edit_course_number'),
    path('preparation/course_numbers/', views.course_numbers, name='course_numbers'),

    path('preparation/course_sections/delete/', views.delete_course_section, name='delete_course_section'),
    path('preparation/course_sections/<int:course_section_id>/edit/', views.edit_course_section, name='edit_course_section'),
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

    path('preparation/admin-emails/delete/', views.delete_admin_email, name='delete_admin_email'),
    path('preparation/admin-emails/<str:slug>/edit/', views.edit_admin_email, name='edit_admin_email'),
    path('preparation/admin-emails/', views.admin_emails, name='admin_emails'),

    path('preparation/landing-pages/delete/', views.delete_landing_page, name='delete_landing_page'),
    path('preparation/landing-pages/<int:landing_page_id>/edit/', views.edit_landing_page, name='edit_landing_page'),
    path('preparation/landing-pages/', views.landing_pages, name='landing_pages')
]
