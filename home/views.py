from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_control

from department.models import ApplicationStatus
from department.forms import ApplicationForm, ApplicationStatusForm
from users import api as usersApi
from department import api as departmentApi

from django.forms.models import model_to_dict

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def index(request):
    """ Display active sessions """

    if not usersApi.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = usersApi.loggedin_user(request.user)
    active_sessions = departmentApi.get_active_sessions()
    return render(request, 'home/index.html', {
        'loggedin_user': loggedin_user,
        'active_sessions': active_sessions
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_session(request, session_slug):
    """ Display session details """

    if not usersApi.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = usersApi.loggedin_user(request.user)
    session = departmentApi.get_session_by_slug(session_slug)
    jobs = departmentApi.get_jobs_with_student_applied(session_slug, request.user)
    return render(request, 'home/show_session.html', {
        'loggedin_user': loggedin_user,
        'session': session,
        'jobs': jobs
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def show_job(request, session_slug, job_slug):
    """ Display job details of a session """

    if not usersApi.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = usersApi.loggedin_user(request.user)
    session = departmentApi.get_session_by_slug(session_slug)
    job = departmentApi.get_session_job_by_slug(session_slug, job_slug)
    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            application = form.save()

            if application:
                status_form = ApplicationStatusForm({ 'assigned': ApplicationStatus.NONE, 'assigned_hours': 0.00 })
                #status_data = status_form.cleaned_data
                status = status_form.save()

                if status:
                    application.status.add(status)
                    #job.applications.add(application)
                    messages.success(request, 'Success! {0} {1} {2} {3} {4} applied'.format(job.session.year, job.session.term.code, job.course.code.name, job.course.number.name, job.course.section.name))
                    return HttpResponseRedirect( reverse('home:show_session', args=[session_slug]) )
                else:
                    messages.error(request, 'Error!')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! form is invalid')

    return render(request, 'home/show_job.html', {
        'loggedin_user': loggedin_user,
        'session': session,
        'job': job,
        'has_applied_job': departmentApi.has_applied_job(session_slug, job_slug, request.user),
        'form': ApplicationForm(initial={
            'applicant': request.user.id,
            'job': job.id
        })
    })




"""
def index(request):


    courses = departmentApi.get_course_list_with_student_applied(request.user)
    for course in courses:
        print( course, course.has_applied )

    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        print(request.POST)
        print('is valid ', form.is_valid())
        print(form.errors.get_json_data())
        if form.is_valid():
            application = form.save()
            if application:
                course_id = request.POST.get('course')
                course = departmentApi.get_course(course_id)
                print("course ", course)
                course.applications.add( application )
                messages.success(request, 'Success!')
                return redirect('home:index')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error!')

    return render(request, 'home/index.html', {
        'loggedin_user': usersApi.loggedin_user(request.user),
        'courses': courses,
        'form': ApplicationForm(initial={
            'applicant': request.user.id
        })
    })
"""
