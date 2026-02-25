from django.urls import path
from . import views
from . import session_views
from . import job_views
from . import app_views
from . import course_views
from . import hr_views
from . import prep_views

app_name = 'administrators'

urlpatterns = [
    path('', views.Index.as_view(), name='index')
]


# Session

urlpatterns += [
    path('sessions/create/confirmation/', session_views.CreateSessionConfirmation.as_view(), name='create_session_confirmation'),
    path('sessions/create/setup-courses/', session_views.CreateSessionSetupCourses.as_view(), name='create_session_setup_courses'),
    path('sessions/create/', session_views.CreateSession.as_view(), name='create_session'),
    path('sessions/<str:session_slug>/delete/confirmation/', session_views.delete_session_confirmation, name='delete_session_confirmation'),
    path('sessions/<str:session_slug>/edit/', session_views.EditSession.as_view(), name='edit_session'),
    path('sessions/<str:session_slug>/details/', session_views.ShowSession.as_view(), name='show_session'),
    path('sessions/<str:session_slug>/report/summary/', session_views.ShowReportSummary.as_view(), name='show_report_summary'),
    path('sessions/<str:session_slug>/report/applicants/', session_views.ShowReportApplicants.as_view(), name='show_report_applicants'),
    path('sessions/current/', session_views.CurrentSessions.as_view(), name='current_sessions'),
    path('sessions/archived/', session_views.ArchivedSessions.as_view(), name='archived_sessions'),
    path('sessions/extra-courses/add/', session_views.AddExtraCourses.as_view(), name='add_extra_courses'),
]


# Job

urlpatterns += [
    path('jobs/prepare/', job_views.PrepareJobs.as_view(), name='prepare_jobs'),
    path('jobs/progress/', job_views.ProgressJobs.as_view(), name='progress_jobs'),
    path('jobs/student/', job_views.StudentJobs.as_view(), name='student_jobs'),
    path('jobs/instructor/', job_views.InstructorJobs.as_view(), name='instructor_jobs'),
    path('instructors/search/', job_views.search_instructors, name='search_instructors'),
    path('instructors/<str:username>/jobs/', job_views.InstructorJobsDetails.as_view(), name='instructor_jobs_details'),
    path('students/<str:username>/jobs/', job_views.StudentJobsDetails.as_view(), name='student_jobs_details'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/edit/', job_views.edit_job, name='edit_job'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/applications/', job_views.show_job_applications, name='show_job_applications'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/applicants/summary/', job_views.SummaryApplicants.as_view(), name='summary_applicants'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/details/', job_views.show_job, name='show_job'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/instructors/add/', job_views.add_job_instructors, name='add_job_instructors'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/instructors/delete/', job_views.delete_job_instructors, name='delete_job_instructors'),
    path('job/worktag_setting/delete/', job_views.delete_job_worktag_setting, name='delete_job_worktag_setting'),
    path('app/worktag_setting/delete/', job_views.delete_app_worktag_setting, name='delete_app_worktag_setting'),

    path('func/jobs/report/download/pdf/', job_views.download_job_report_md, name='download_job_report_md'),
    path('func/jobs/report/download/excel/', job_views.download_job_report_excel, name='download_job_report_excel')
]


# Application

urlpatterns += [
    path('applications/send_email/confirmation/', app_views.applications_send_email_confirmation, name='applications_send_email_confirmation'),
    path('applications/send_email/', app_views.applications_send_email, name='applications_send_email'),

    path('sessions/<str:session_slug>/jobs/<str:job_slug>/offer/', app_views.offer_job, name='offer_job'),
    path('applications/email_history/', app_views.email_history, name='email_history'),
    path('emails/<str:email_id>/reminder/', app_views.send_reminder, name='send_reminder'),
    path('applications/decline_reassign/confirmation/', app_views.decline_reassign_confirmation, name='decline_reassign_confirmation'),
    path('applications/decline_reassign/', app_views.decline_reassign, name='decline_reassign'),
    path('applications/<str:app_slug>/terminate/', app_views.terminate, name='terminate'),

    path('applications/dashboard/', app_views.ApplicationsDashboard.as_view(), name='applications_dashboard'),
    path('applications/all/', app_views.AllApplications.as_view(), name='all_applications'),
    path('applications/selected/', app_views.SelectedApplications.as_view(), name='selected_applications'),
    path('applications/offered/', app_views.OfferedApplications.as_view(), name='offered_applications'),
    path('applications/accepted/report/admin/', app_views.AcceptedAppsReportAdmin.as_view(), name='accepted_apps_report_admin'),
    path('applications/accepted/workday/', app_views.AcceptedAppsReportWorkday.as_view(), name='accepted_apps_report_workday'),
    path('applications/accepted/', app_views.AcceptedApplications.as_view(), name='accepted_applications'),
    path('applications/declined/', app_views.DeclinedApplications.as_view(), name='declined_applications'),
    path('applications/terminated/', app_views.TerminatedApplications.as_view(), name='terminated_applications'),
    path('applications/accepted/report/observer/', app_views.AcceptedAppsReportObserver.as_view(), name='accepted_apps_report_observer'),
    path('applications/admin_docs/update/', app_views.update_admin_docs, name='update_admin_docs'),
    path('applications/accepted/download/workday/', app_views.download_accepted_apps_workday, name='download_accepted_apps_workday'),
    path('applications/accepted/import/', app_views.import_accepted_apps, name='import_accepted_apps'),
    path('applications/reset/', app_views.reset_application, name='reset_application'),

    path('applications/<str:app_slug>/details/', app_views.ShowApplication.as_view(), name='show_application'),

    path('func/applications/accepted/download/all/', app_views.download_all_accepted_apps, name='download_all_accepted_apps'),
    path('func/applications/accepted/report/admin/download/all/', app_views.download_all_accepted_apps_report_admin, name='download_all_accepted_apps_report_admin'),
    path('func/applications/applied/preferred_candidate/download/', app_views.download_preferred_candidates, name='download_preferred_candidates')
]


# Course

urlpatterns += [
    path('courses/all/', course_views.all_courses, name='all_courses'),
    path('courses/create/', course_views.create_course, name='create_course'),
    path('courses/delete/', course_views.delete_course, name='delete_course'),
    path('courses/<str:course_slug>/edit/', course_views.edit_course, name='edit_course')
]


# HR

urlpatterns += [
    path('hr/users/<str:username>/edit/', hr_views.edit_user, name='edit_user'),
    path('hr/users/<str:username>/delete/confirmation/', hr_views.delete_user_confirmation, name='delete_user_confirmation'),
    path('hr/users/all/', hr_views.all_users, name='all_users'),
    path('hr/users/destroy/contents/', hr_views.destroy_user_contents, name='destroy_user_contents'),
    path('hr/users/create/', hr_views.create_user, name='create_user'),

    path('hr/roles/<str:slug>/edit/', hr_views.edit_role, name='edit_role'),
    path('hr/roles/delete/', hr_views.delete_role, name='delete_role'),
    path('hr/roles/', hr_views.roles, name='roles')
]


# Preparation

urlpatterns += [
    path('preparation/terms/delete/', prep_views.delete_term, name='delete_term'),
    path('preparation/terms/<int:term_id>/edit/', prep_views.edit_term, name='edit_term'),
    path('preparation/terms/', prep_views.terms, name='terms'),

    path('preparation/course_codes/delete/', prep_views.delete_course_code, name='delete_course_code'),
    path('preparation/course_codes/<int:course_code_id>/edit/', prep_views.edit_course_code, name='edit_course_code'),
    path('preparation/course_codes/', prep_views.course_codes, name='course_codes'),

    path('preparation/course_numbers/delete/', prep_views.delete_course_number, name='delete_course_number'),
    path('preparation/course_numbers/<int:course_number_id>/edit/', prep_views.edit_course_number, name='edit_course_number'),
    path('preparation/course_numbers/', prep_views.course_numbers, name='course_numbers'),

    path('preparation/course_sections/delete/', prep_views.delete_course_section, name='delete_course_section'),
    path('preparation/course_sections/<int:course_section_id>/edit/', prep_views.edit_course_section, name='edit_course_section'),
    path('preparation/course_sections/', prep_views.course_sections, name='course_sections'),

    path('preparation/statuses/delete/', prep_views.delete_status, name='delete_status'),
    path('preparation/statuses/<str:slug>/edit/', prep_views.edit_status, name='edit_status'),
    path('preparation/statuses/', prep_views.statuses, name='statuses'),

    path('preparation/faculties/delete/', prep_views.delete_faculty, name='delete_faculty'),
    path('preparation/faculties/<str:slug>/edit/', prep_views.edit_faculty, name='edit_faculty'),
    path('preparation/faculties/', prep_views.faculties, name='faculties'),

    path('preparation/programs/delete/', prep_views.delete_program, name='delete_program'),
    path('preparation/programs/<str:slug>/edit/', prep_views.edit_program, name='edit_program'),
    path('preparation/programs/', prep_views.programs, name='programs'),

    path('preparation/degrees/delete/', prep_views.delete_degree, name='delete_degree'),
    path('preparation/degrees/<str:slug>/edit/', prep_views.edit_degree, name='edit_degree'),
    path('preparation/degrees/', prep_views.degrees, name='degrees'),

    path('preparation/trainings/delete/', prep_views.delete_training, name='delete_training'),
    path('preparation/trainings/<str:slug>/edit/', prep_views.edit_training, name='edit_training'),
    path('preparation/trainings/', prep_views.trainings, name='trainings'),

    path('preparation/classifications/delete/', prep_views.delete_classification, name='delete_classification'),
    path('preparation/classifications/<str:slug>/edit/', prep_views.edit_classification, name='edit_classification'),
    path('preparation/classifications/', prep_views.classifications, name='classifications'),

    path('preparation/admin-emails/delete/', prep_views.delete_admin_email, name='delete_admin_email'),
    path('preparation/admin-emails/<str:slug>/edit/', prep_views.edit_admin_email, name='edit_admin_email'),
    path('preparation/admin-emails/', prep_views.admin_emails, name='admin_emails'),

    path('preparation/landing-pages/delete/', prep_views.delete_landing_page, name='delete_landing_page'),
    path('preparation/landing-pages/<int:landing_page_id>/edit/', prep_views.edit_landing_page, name='edit_landing_page'),
    path('preparation/landing-pages/', prep_views.landing_pages, name='landing_pages')
]