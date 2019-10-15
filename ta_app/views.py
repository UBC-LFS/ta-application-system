from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_http_methods

from users import api as userApi
from administrators import api as adminApi

def get_previous_url(path, portal):
    previous_url = None
    if portal == 'Admin':
        previous_url = '/administrators'
        if path == 'prepare':
            previous_url += '/jobs/prepare/'
        elif path == 'progress':
            previous_url += '/jobs/progress/'
        elif path == 'dashboard':
            previous_url += '/applications/dashboard/'
        elif path == 'all':
            previous_url += '/applications/all/'
        elif path == 'selected':
            previous_url += '/applications/selected/'
        elif path == 'offered':
            previous_url += '/applications/offered/'
        elif path == 'accepted':
            previous_url += '/applications/accepted/'
        elif path == 'declined':
            previous_url += '/applications/declined/'
        elif path == 'email_history':
            previous_url += '/applications/offered/email_history/'

    elif portal == 'Instructor':
        previous_url = '/instructors'
        if path == 'my_jobs':
            previous_url += '/my_jobs/'
        if path == 'get_applications':
            previous_url += path

    elif portal == 'Student':
        previous_url = '/students'
        if path == 'applied':
            previous_url += '/jobs/applied/'
        elif path == 'offered':
            previous_url += '/jobs/offered/'
        elif path == 'accepted':
            previous_url += '/jobs/accepted/'
        elif path == 'declined':
            previous_url += '/jobs/declined/'

    return previous_url

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_user(request, username, path, portal):
    ''' Display user's details '''
    loggedin_user = userApi.loggedin_user(request.user)
    if portal not in loggedin_user.roles: raise PermissionDenied

    # Create a hyperlink to go back to the previous page
    previous_url = None
    if 'HTTP_REFERER' in request.META:
        previous_url = request.META['HTTP_REFERER']

    return render(request, 'ta_app/users/show_user.html', {
        'loggedin_user': loggedin_user,
        'previous_url': previous_url,
        'user': userApi.get_user_by_username_with_resume(username),
        'stats': adminApi.get_user_job_application_statistics(username),
        'path': path,
        'portal': portal
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_job(request, session_slug, job_slug, path, portal):
    ''' Display job details '''
    loggedin_user = userApi.loggedin_user(request.user)
    if portal not in loggedin_user.roles: raise PermissionDenied

    return render(request, 'ta_app/jobs/show_job.html', {
        'loggedin_user': loggedin_user,
        'previous_url': get_previous_url(path, portal),
        'job': adminApi.get_session_job_by_slug(session_slug, job_slug),
        'portal': portal
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_application(request, app_slug, path, portal):
    ''' Display application details '''
    loggedin_user = userApi.loggedin_user(request.user)
    if portal not in loggedin_user.roles: raise PermissionDenied

    return render(request, 'ta_app/applications/show_application.html', {
        'loggedin_user': userApi.loggedin_user(request.user),
        'app': adminApi.get_application_slug(app_slug),
        'previous_url': get_previous_url(path, portal),
        'path': path,
        'portal': portal
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def display_application_details(request, app_slug, role):
    ''' '''
    loggedin_user = userApi.loggedin_user(request.user)
    #if not userApi.is_admin(loggedin_user): raise PermissionDenied
    return render(request, 'administrators/util/_display_application_details.html', {
        'loggedin_user': loggedin_user,
        'previous_url': request.META['HTTP_REFERER'],
        'application': adminApi.get_application_slug(app_slug),
        'role': role
    })
