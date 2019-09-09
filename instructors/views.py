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
from administrators import api as administratorsApi
from users import api as usersApi


from datetime import datetime


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def index(request):
    loggedin_user = usersApi.loggedin_user(request.user)
    if 'Instructor' not in loggedin_user.roles: raise PermissionDenied

    return render(request, 'instructors/index.html', {
        'loggedin_user': loggedin_user
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def profile(request):
    loggedin_user = usersApi.loggedin_user(request.user)
    if 'Instructor' not in loggedin_user.roles: raise PermissionDenied

    return render(request, 'instructors/profile.html', {
        'loggedin_user': loggedin_user,
        'user': usersApi.get_user(request.user.id)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def my_jobs(request):
    loggedin_user = usersApi.loggedin_user(request.user)
    if 'Instructor' not in loggedin_user.roles: raise PermissionDenied

    return render(request, 'instructors/jobs/my_jobs.html', {
        'loggedin_user': loggedin_user,
        'user': usersApi.get_user(request.user.id)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_job(request, session_slug, job_slug):
    loggedin_user = usersApi.loggedin_user(request.user)
    if 'Instructor' not in loggedin_user.roles: raise PermissionDenied

    user = usersApi.get_user(request.user.id)
    job = administratorsApi.get_session_job_by_slug(session_slug, job_slug)
    if request.method == 'POST':
        form = InstructorJobForm(request.POST, instance=job)
        if form.is_valid():
            job = form.save(commit=False)
            job.updated_at = datetime.now()
            job.save()
            if job:
                messages.success(request, 'Success! {0} - job details updated'.format(user.username))
                return redirect('instructors:my_jobs')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'instructors/jobs/edit_job.html', {
        'loggedin_user': loggedin_user,
        'user': user,
        'session': administratorsApi.get_session_by_slug(session_slug),
        'job': job,
        'form': InstructorJobForm(data=None, instance=job)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def get_applications(request, session_slug, job_slug):
    loggedin_user = usersApi.loggedin_user(request.user)
    if 'Instructor' not in loggedin_user.roles: raise PermissionDenied

    user = usersApi.get_user(request.user.id)
    job = administratorsApi.get_session_job_by_slug(session_slug, job_slug)
    instructor_preference = [ app.instructor_preference for app in job.application_set.all() ]
    if request.method == 'POST':
        form = InstructorApplicationForm(request.POST)
        if form.is_valid():
            application_id = request.POST.get('application')
            instructor_preference = request.POST.get('instructor_preference')
            updated_application = administratorsApi.update_application_instructor_preference(application_id, instructor_preference)
            if updated_application:
                messages.success(request, 'Success! Instructor Preference is selected for {0} '.format(updated_application.applicant.username))
                return HttpResponseRedirect( reverse('instructors:get_applications', args=[session_slug, job_slug]) )
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'instructors/jobs/get_applications.html', {
        'loggedin_user': loggedin_user,
        'job': administratorsApi.get_session_job_by_slug(session_slug, job_slug),
        'instructor_preference_choices': Application.INSTRUCTOR_PREFERENCE_CHOICES
    })


"""
@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_job(request, session_slug, job_slug):

    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if 'Instructor' not in loggedin_user.roles: raise PermissionDenied


    job = administratorsApi.get_session_job_by_slug(session_slug, job_slug)
    instructor_preference = [ app.instructor_preference for app in job.application_set.all() ]
    print(instructor_preference)
    if request.method == 'POST':
        form = InstructorApplicationForm(request.POST)
        if form.is_valid():
            data = request.POST
            application_id = data.get('application')
            instructor_preference = data.get('instructor_preference')
            updated = administratorsApi.update_application_instructor_preference(application_id, instructor_preference)
            if updated:
                messages.success(request, 'Success!')
                return HttpResponseRedirect( reverse('instructors:show_job', args=[session_slug, job_slug]) )
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'instructors/jobs/show_job.html', {
        'loggedin_user': loggedin_user,
        'user': usersApi.get_user(request.user.id),
        'session': administratorsApi.get_session_by_slug(session_slug),
        'job': administratorsApi.get_session_job_by_slug(session_slug, job_slug),
        'form': InstructorApplicationForm()
    })
"""
