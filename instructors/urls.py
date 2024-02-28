from django.urls import path
from . import views

app_name = 'instructors'

urlpatterns = [
    path('', views.Index.as_view(), name='index'),
    path('users/edit/', views.EditUser.as_view(), name='edit_user'),
    path('jobs/', views.ShowJobs.as_view(), name='show_jobs'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/edit/', views.EditJob.as_view(), name='edit_job'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/applications/', views.ShowApplications.as_view(), name='show_applications'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/details/', views.ShowJob.as_view(), name='show_job'),
    path('sessions/<str:session_slug>/jobs/<str:job_slug>/applicants/summary-applicants/', views.summary_applicants, name='summary_applicants'),
    path('applications/<str:app_slug>/write-note/', views.write_note, name='write_note'),
    path('applicants/send_email/confirmation', views.applicants_send_email_confirmation, name='applicants_send_email_confirmation'),
    path('applicants/send_email/', views.applicants_send_email, name='applicants_send_email'),
    path('emails/history/', views.show_email_history, name='show_email_history')
]
