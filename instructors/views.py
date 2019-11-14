from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_control

from administrators.views import APP_STATUS
from administrators.models import *
from administrators.forms import *
from administrators import api as adminApi
from users import api as userApi

from datetime import datetime


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def index(request):
    ''' Index page of an instructor's portal '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Instructor' not in loggedin_user.roles: raise PermissionDenied

    return render(request, 'instructors/index.html', {
        'loggedin_user': loggedin_user
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_profile(request):
    ''' Display user's profile '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Instructor' not in loggedin_user.roles: raise PermissionDenied

    return render(request, 'instructors/users/show_profile.html', {
        'loggedin_user': loggedin_user
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_user(request, session_slug, job_slug, username):
    ''' Display an user's details '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Instructor' not in loggedin_user.roles: raise PermissionDenied

    user = userApi.get_user(username, 'username')
    user.is_student = userApi.user_has_role(user ,'Student')
    return render(request, 'instructors/users/show_user.html', {
        'loggedin_user': loggedin_user,
        'user': userApi.add_resume(user),
        'session_slug': session_slug,
        'job_slug': job_slug
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_jobs(request):
    ''' Display jobs by instructors '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Instructor' not in loggedin_user.roles: raise PermissionDenied

    return render(request, 'instructors/jobs/show_jobs.html', {
        'loggedin_user': loggedin_user
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_job(request, session_slug, job_slug):
    ''' Update job details of instructors '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Instructor' not in loggedin_user.roles: raise PermissionDenied

    job = adminApi.get_job_by_session_slug_job_slug(session_slug, job_slug)
    if request.method == 'POST':
        form = InstructorJobForm(request.POST, instance=job)
        if form.is_valid():
            job = form.save(commit=False)
            job.updated_at = datetime.now()
            job.save()
            if job:
                messages.success(request, 'Success! {0} {1} - {2} {3} {4}: job details updated'.format(job.session.year, job.session.term.code, job.course.code.name, job.course.number.name, job.course.section.name))
                return redirect('instructors:show_jobs')
            else:
                messages.error(request, 'An error occurred while updating job details.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return HttpResponseRedirect( reverse('instructors:edit_job', args=[session_slug, job_slug]) )

    return render(request, 'instructors/jobs/edit_job.html', {
        'loggedin_user': loggedin_user,
        'job': job,
        'form': InstructorJobForm(data=None, instance=job),
        'jobs': adminApi.get_recent_ten_job_details(job.course, job.session.year)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def show_job(request, session_slug, job_slug):
    ''' Display job details '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Instructor' not in loggedin_user.roles: raise PermissionDenied

    return render(request, 'instructors/jobs/show_job.html', {
        'loggedin_user': loggedin_user,
        'job': adminApi.get_job_by_session_slug_job_slug(session_slug, job_slug)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def show_applications(request, session_slug, job_slug):
    ''' Display applications applied by students '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Instructor' not in loggedin_user.roles: raise PermissionDenied

    job = adminApi.get_job_by_session_slug_job_slug(session_slug, job_slug)

    if request.method == 'POST':
        if request.POST.get('instructor_preference') == Application.NONE:
            messages.error(request, 'An error occurred. Please select your preference, then try again.')
            return HttpResponseRedirect( reverse('instructors:show_applications', args=[session_slug, job_slug]) )

        if request.POST.get('instructor_preference') == Application.NO_PREFERENCE and float(request.POST.get('assigned_hours')) > 0.0:
            messages.error(request, 'An error occurred. Please leave 0.0 for Assign TA Hours if you would to select No Preference, then try again.')
            return HttpResponseRedirect( reverse('instructors:show_applications', args=[session_slug, job_slug]) )

        if float(request.POST.get('assigned_hours')) == 0.0 and request.POST.get('instructor_preference') != Application.NO_PREFERENCE:
            messages.error(request, 'An error occurred. Please assign TA hours, then try again.')
            return HttpResponseRedirect( reverse('instructors:show_applications', args=[session_slug, job_slug]) )

        if float(request.POST.get('assigned_hours')) > float(job.assigned_ta_hours):
            messages.error( request, 'An error occurred. You cannot assign {0} hours because its maximum hours is {1}. then try it again.'.format(request.POST.get('assigned_hours'), job.assigned_ta_hours) )
            return HttpResponseRedirect( reverse('instructors:show_applications', args=[session_slug, job_slug]) )


        instructor_app_form = InstructorApplicationForm(request.POST)

        if instructor_app_form.is_valid():
            app_status_form = ApplicationStatusForm(request.POST)

            if app_status_form.is_valid():
                app_id = request.POST.get('application')
                instructor_preference = request.POST.get('instructor_preference')

                updated_app = adminApi.update_application_instructor_preference(app_id, instructor_preference)
                if updated_app:
                    updated_status = app_status_form.save()
                    if updated_status:
                        messages.success(request, 'Success! {0} is selected.'.format(updated_app.applicant.username))
                        return HttpResponseRedirect( reverse('instructors:show_applications', args=[session_slug, job_slug]) )
                    else:
                        messages.error(request, 'An error occurred while updating an application status.')
                else:
                    messages.error(request, 'An error occurred while updating an instructor_preference.')

            else:
                errors = app_status_form.errors.get_json_data()
                messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        else:
            errors = instructor_app_form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return HttpResponseRedirect( reverse('instructors:show_applications', args=[session_slug, job_slug]) )

    apps = adminApi.get_applications_with_status_by_session_slug_job_slug(session_slug, job_slug)

    return render(request, 'instructors/jobs/show_applications.html', {
        'loggedin_user': loggedin_user,
        'job': job,
        'apps': adminApi.get_applications_with_status_by_session_slug_job_slug(session_slug, job_slug),
        'instructor_preference_choices': Application.INSTRUCTOR_PREFERENCE_CHOICES,
        'app_status': APP_STATUS
    })
