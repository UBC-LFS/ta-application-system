from django.shortcuts import render
from users import api as userApi

def permission_denied(request, exception, template_name='403.html'):
    ''' Exception handlder for permission denied '''
    loggedin_user = userApi.loggedin_user(request.user)
    return render(request, 'ta_app/pages/403.html', { 'loggedin_user': loggedin_user }, status=403)

def page_not_found(request, exception, template_name='404.html'):
    ''' Exception handlder for page not found '''
    loggedin_user = userApi.loggedin_user(request.user)
    return render(request, 'ta_app/pages/404.html', { 'loggedin_user': loggedin_user }, status=404)
