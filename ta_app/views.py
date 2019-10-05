from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_http_methods

from users import api as userApi
from administrators import api as adminApi


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