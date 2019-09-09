from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_control

from users import api as usersApi

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def index(request):
    loggedin_user = usersApi.loggedin_user(request.user)
    if 'HR' not in loggedin_user.roles: raise PermissionDenied

    return render(request, 'human_resources/index.html', {
        'loggedin_user': loggedin_user
    })
