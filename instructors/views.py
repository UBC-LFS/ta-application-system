from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_control

from administrators.models import *
from administrators.forms import *
from administrators import api as adminApi
from users import api as userApi


from datetime import datetime


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def index(request):
    ''' '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Instructor' not in loggedin_user.roles: raise PermissionDenied

    return render(request, 'instructors/index.html', {
        'loggedin_user': loggedin_user
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def profile(request):
    ''' Display user's profile '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Instructor' not in loggedin_user.roles: raise PermissionDenied

    return render(request, 'instructors/profile.html', {
        'loggedin_user': loggedin_user,
        'user': loggedin_user
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def my_jobs(request):
    ''' Display jobs by instructors '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Instructor' not in loggedin_user.roles: raise PermissionDenied

    return render(request, 'instructors/jobs/my_jobs.html', {
        'loggedin_user': loggedin_user,
        'user': loggedin_user
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_job(request, session_slug, job_slug):
    ''' Update job details of instructors '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Instructor' not in loggedin_user.roles: raise PermissionDenied

    job = adminApi.get_session_job_by_slug(session_slug, job_slug)
    if request.method == 'POST':
        form = InstructorJobForm(request.POST, instance=job)
        if form.is_valid():
            job = form.save(commit=False)
            job.updated_at = datetime.now()
            job.save()
            if job:
                messages.success(request, 'Success! {0} {1} - {2} {3} {4}: job details updated'.format(job.session.year, job.session.term.code, job.course.code.name, job.course.number.name, job.course.section.name))
                return redirect('instructors:my_jobs')
            else:
                messages.error(request, 'An error occurred while updating job details.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))


    return render(request, 'instructors/jobs/edit_job.html', {
        'loggedin_user': loggedin_user,
        'job': job,
        'form': InstructorJobForm(data=None, instance=job),
        'jobs': adminApi.get_recent_ten_job_details(job.course, job.session.year)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def get_applications(request, session_slug, job_slug):
    ''' Display applications applied by students '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Instructor' not in loggedin_user.roles: raise PermissionDenied

    if request.method == 'POST':
        form = InstructorApplicationForm(request.POST)
        if form.is_valid():
            application_id = request.POST.get('application')
            instructor_preference = request.POST.get('instructor_preference')
            updated_application = adminApi.update_application_instructor_preference(application_id, instructor_preference)
            if updated_application:
                messages.success(request, 'Success! Instructor Preference is selected for {0} '.format(updated_application.applicant.username))
                return HttpResponseRedirect( reverse('instructors:get_applications', args=[session_slug, job_slug]) )
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

    return render(request, 'instructors/jobs/get_applications.html', {
        'loggedin_user': loggedin_user,
        'job': adminApi.get_session_job_by_slug(session_slug, job_slug),
        'instructor_preference_choices': Application.INSTRUCTOR_PREFERENCE_CHOICES
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
        'job': adminApi.get_session_job_by_slug(session_slug, job_slug)
    })
