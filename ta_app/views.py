from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_control
from django.http import HttpResponseRedirect
from django.core.exceptions import SuspiciousOperation
from django.contrib.auth import logout

from administrators import api as adminApi
from users import api as userApi


def landing_page(request):
    return render(request, 'ta_app/landing_page.html', {
        'landing_page': adminApi.get_visible_landing_page()
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def app_home(request):
    ''' App Home '''

    roles = userApi.get_user_roles(request.user)
    if not roles:
        raise SuspiciousOperation

    request.session['loggedin_user'] = {
        'id': request.user.id,
        'username': request.user.username,
        'roles': roles
    }
    redirect_to = adminApi.redirect_to_index_page(roles)
    return HttpResponseRedirect(redirect_to)


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def site_logout(request):
    logout(request)
    return HttpResponseRedirect('/Shibboleth.sso/Logout')


def bad_request(request, exception, template_name='400.html'):
    ''' Exception handlder for bad request '''
    return render(request, 'ta_app/errors/400.html', { 'loggedin_user': None }, status=400)

def permission_denied(request, exception, template_name='403.html'):
    ''' Exception handlder for permission denied '''
    loggedin_user = userApi.loggedin_user(request.user)
    return render(request, 'ta_app/errors/403.html', { 'loggedin_user': loggedin_user }, status=403)

def page_not_found(request, exception, template_name='404.html'):
    ''' Exception handlder for page not found '''
    loggedin_user = userApi.loggedin_user(request.user)
    return render(request, 'ta_app/errors/404.html', { 'loggedin_user': loggedin_user }, status=404)

def internal_server_error(request, template_name='500.html'):
    ''' Exception handlder for internal server error '''
    loggedin_user = userApi.loggedin_user(request.user)
    return render(request, 'ta_app/errors/500.html', { 'loggedin_user': loggedin_user }, status=500)