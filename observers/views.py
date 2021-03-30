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

    year_q = request.GET.get('year')
    term_q = request.GET.get('term')
    code_q = request.GET.get('code')
    number_q = request.GET.get('number')
    section_q = request.GET.get('section')
    first_name_q = request.GET.get('first_name')
    last_name_q = request.GET.get('last_name')
    student_number_q = request.GET.get('student_number')

    app_list = adminApi.get_applications()
    if bool(year_q):
        app_list = app_list.filter(job__session__year__icontains=year_q)
    if bool(term_q):
        app_list = app_list.filter(job__session__term__code__icontains=term_q)
    if bool(code_q):
        app_list = app_list.filter(job__course__code__name__icontains=code_q)
    if bool(number_q):
        app_list = app_list.filter(job__course__number__name__icontains=number_q)
    if bool(section_q):
        app_list = app_list.filter(job__course__section__name__icontains=section_q)
    if bool(first_name_q):
        app_list = app_list.filter(applicant__first_name__icontains=first_name_q)
    if bool(last_name_q):
        app_list = app_list.filter(applicant__last_name__icontains=last_name_q)
    if bool(student_number_q):
        app_list = app_list.filter(applicant__profile__student_number__icontains=student_number_q)

    #app_list = app_list.filter( Q(applicationstatus__assigned=ApplicationStatus.ACCEPTED) & Q(is_terminated=False) ).order_by('-id').distinct()
    #app_list = adminApi.add_app_info_into_applications(app_list, ['accepted', 'declined'])
    #app_list = [ app for app in app_list if (app.declined == None) or (app.declined != None and app.accepted.id > app.declined.id) ]
    app_list = app_list.filter(applicationstatus__assigned=ApplicationStatus.ACCEPTED).order_by('-id').distinct()
    app_list = adminApi.add_app_info_into_applications(app_list, ['accepted', 'declined', 'cancelled'])

    filtered_app_list = []
    for app in app_list:
        filtered_app_list, _, _ = adminApi.valid_accepted_app(filtered_app_list, app)
        """if app.is_terminated == False or app.cancelled == None:
            if app.is_declined_reassigned:
                latest_status = adminApi.get_latest_status_in_app(app)
                if (latest_status == 'declined' and app.declined.parent_id != None) or (latest_status == 'accepted'):
                    filtered_app_list.append(app)
            else:
                filtered_app_list.append(app)"""

    page = request.GET.get('page', 1)
    paginator = Paginator(filtered_app_list, settings.PAGE_SIZE)

    try:
    	apps = paginator.page(page)
    except PageNotAnInteger:
    	apps = paginator.page(1)
    except EmptyPage:
    	apps = paginator.page(paginator.num_pages)

    apps = adminApi.add_app_info_into_applications(apps, ['accepted'])

    return render(request, 'observers/report_accepted_applications.html', {
        'loggedin_user': request.user,
        'apps': apps,
        'total_apps': len(filtered_app_list)
    })
