from django.shortcuts import render, redirect
from users import api as userApi

def index(request):
    ''' App index page '''
    return redirect('accounts:login')


def bad_request(request, exception, template_name='400.html'):
    ''' Exception handlder for bad request '''
    return render(request, 'ta_app/pages/400.html', { 'loggedin_user': None }, status=400)


def permission_denied(request, exception, template_name='403.html'):
    ''' Exception handlder for permission denied '''
    loggedin_user = userApi.loggedin_user(request.user)
    return render(request, 'ta_app/pages/403.html', { 'loggedin_user': loggedin_user }, status=403)


def page_not_found(request, exception, template_name='404.html'):
    ''' Exception handlder for page not found '''
    loggedin_user = userApi.loggedin_user(request.user)
    return render(request, 'ta_app/pages/404.html', { 'loggedin_user': loggedin_user }, status=404)


def internal_server_error(request, template_name='500.html'):
    ''' Exception handlder for internal server error '''
    loggedin_user = userApi.loggedin_user(request.user)
    return render(request, 'ta_app/pages/500.html', { 'loggedin_user': loggedin_user }, status=500)
