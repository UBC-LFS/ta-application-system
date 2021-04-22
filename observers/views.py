from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_control
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

from users.models import Role

from administrators.models import ApplicationStatus
from administrators import api as adminApi
from users import api as userApi


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def index(request):
    ''' Index page of Observer's portal '''
    request = userApi.has_user_access(request, Role.OBSERVER)

    return render(request, 'observers/index.html', {
        'loggedin_user': request.user
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def report_accepted_applications(request):
    ''' Display a report of applications accepted by students '''
    request = userApi.has_user_access(request, Role.OBSERVER)

    apps, total_apps = adminApi.get_report_accepted_applications(request)

    page = request.GET.get('page', 1)
    paginator = Paginator(apps, settings.PAGE_SIZE)

    try:
    	apps = paginator.page(page)
    except PageNotAnInteger:
    	apps = paginator.page(1)
    except EmptyPage:
    	apps = paginator.page(paginator.num_pages)

    filtered_app_list = []
    for app in apps:
        filtered_app_list, _, _ = adminApi.valid_accepted_app(filtered_app_list, app)

    return render(request, 'observers/report_accepted_applications.html', {
        'loggedin_user': request.user,
        'apps': apps,
        'total_apps': total_apps
    })
