from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_control

from users import api as userApi

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def index(request):
    ''' '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'HR' not in loggedin_user.roles: raise PermissionDenied

    return render(request, 'human_resources/index.html', {
        'loggedin_user': loggedin_user
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def users_confidentiality(request):
    ''' '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'HR' not in loggedin_user.roles: raise PermissionDenied

    return render(request, 'human_resources/users_confidentiality.html', {
        'loggedin_user': loggedin_user,
        'users': userApi.get_users()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_user(request, username):
    ''' Display an user's details '''
    loggedin_user = userApi.loggedin_user(request.user)

    return render(request, 'human_resources/show_user.html', {
        'loggedin_user': loggedin_user,
        'user': userApi.get_user_by_username_with_resume(username),
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def view_confidentiality(request, username):
    ''' display an user's confidentiality '''
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user) and 'HR' not in loggedin_user.roles: raise PermissionDenied

    user = userApi.get_user_by_username(username)
    return render(request, 'human_resources/view_confidentiality.html', {
        'loggedin_user': loggedin_user,
        'user': userApi.get_user_with_confidentiality(user.id)
    })
