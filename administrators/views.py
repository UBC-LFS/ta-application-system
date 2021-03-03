from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404, JsonResponse
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_control
from io import StringIO

from django.db.models import Q
from django.views.static import serve
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.contrib.auth.models import User

from administrators.models import Session, Job, Application, ApplicationStatus, Course
from administrators.forms import *
from administrators import api as adminApi

from users.models import *
from users.forms import *
from users import api as userApi

from datetime import datetime, timedelta


APP_STATUS = {
    'none': ApplicationStatus.NONE,
    'applied': ApplicationStatus.NONE,
    'selected': ApplicationStatus.SELECTED,
    'offered': ApplicationStatus.OFFERED,
    'accepted': ApplicationStatus.ACCEPTED,
    'declined': ApplicationStatus.DECLINED,
    'cancelled': ApplicationStatus.CANCELLED
}



@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def index(request):
    ''' Index page of Administrator's portal '''
    request = userApi.has_admin_access(request, Role.HR)

    apps = adminApi.get_applications()

    today_accepted_apps, today = adminApi.get_accepted_apps_by_day(apps, 'today')
    yesterday_accepted_apps, yesterday = adminApi.get_accepted_apps_by_day(apps, 'yesterday')
    week_ago_accepted_apps, week_ago = adminApi.get_accepted_apps_by_day(apps, 'week_ago')

    context = {
        'loggedin_user': userApi.add_avatar(request.user),
        'accepted_apps': apps.filter(applicationstatus__assigned=ApplicationStatus.ACCEPTED).exclude(applicationstatus__assigned=ApplicationStatus.CANCELLED).order_by('-id').distinct(),
        'today_accepted_apps': today_accepted_apps,
        'today_eform_stats': adminApi.get_eform_stats(today_accepted_apps),
        'yesterday_accepted_apps': yesterday_accepted_apps,
        'yesterday_eform_stats': adminApi.get_eform_stats(yesterday_accepted_apps),
        'week_ago_accepted_apps': week_ago_accepted_apps,
        'week_ago_eform_stats': adminApi.get_eform_stats(week_ago_accepted_apps),
        'today': today,
        'yesterday': yesterday,
        'week_ago': week_ago
    }
    if Role.ADMIN in request.user.roles or Role.SUPERADMIN in request.user.roles:
        sessions = adminApi.get_sessions()
        context['current_sessions'] = sessions.filter(is_archived=False)
        context['archived_sessions'] = sessions.filter(is_archived=True)
        context['apps'] = adminApi.get_applications()
        context['instructors'] = userApi.get_users_by_role(Role.INSTRUCTOR)
        context['students'] = userApi.get_users_by_role(Role.STUDENT)
        context['users'] = userApi.get_users()

    return render(request, 'administrators/index.html', context)


# Sessions


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def create_session(request):
    ''' Create a session '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        request.session['session_form_data'] = request.POST
        return redirect('administrators:create_session_confirmation')

    sessions = adminApi.get_sessions()
    return render(request, 'administrators/sessions/create_session.html', {
        'loggedin_user': request.user,
        'current_sessions': sessions.filter(is_archived=False),
        'archived_sessions': sessions.filter(is_archived=True),
        'form': SessionForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def create_session_confirmation(request):
    ''' Confirm all the inforamtion to create a session '''
    request = userApi.has_admin_access(request)

    sessions = adminApi.get_sessions()
    error_messages = []
    form = None
    data = None
    courses = None
    year = None
    term = None
    if request.method == 'POST':
        form = SessionConfirmationForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            courses = data.get('courses')

            if len(courses) == 0:
                messages.error(request, 'An error occurred. Please select courses in this session.')
                return redirect('administrators:create_session_confirmation')

            session = form.save(commit=False)

            if data['is_archived']:
                session.is_visible = False

            session.save()

            if session:
                jobs = adminApi.create_jobs(session, courses)
                if jobs:
                    del request.session['session_form_data'] # remove session form data
                    messages.success(request, 'Success! {0} {1} - {2} created'.format(session.year, session.term.code, session.title))
                    if data['is_archived']:
                        return redirect('administrators:archived_sessions')
                    else:
                        return redirect('administrators:current_sessions')
                else:
                    messages.error(request, 'An error occurred. Failed to create jobs')
            else:
                messages.error(request, 'An error occurred. Failed to create a session')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return redirect('administrators:create_session_confirmation')

    else:
        data = request.session.get('session_form_data')
        if data:
            year = data['year']
            term = adminApi.get_term(data['term'])
            courses = adminApi.get_courses_by_term(data['term'])
            if len(courses) > 0:
                data['courses'] = courses
                form = SessionConfirmationForm(data=data, initial={ 'term': term })
                errors = form.errors.get_json_data()
                if len(errors.keys()) > 0:
                    form = None
                    for key, value in errors.items(): error_messages.append(value[0]['message'])
            else:
                form = None
                error_messages.append('No courses found in a session term.')
        else:
            form = None
            error_messages.append('No data found.')

    return render(request, 'administrators/sessions/create_session_confirmation.html', {
        'loggedin_user': request.user,
        'current_sessions': sessions.filter(is_archived=False),
        'archived_sessions': sessions.filter(is_archived=True),
        'session': { 'year': year, 'term': term },
        'courses': courses,
        'form': form,
        'error_messages': error_messages
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def current_sessions(request):
    ''' Display all information of sessions and create a session '''
    request = userApi.has_admin_access(request)

    year_q = request.GET.get('year')
    term_q = request.GET.get('term')

    session_list = adminApi.get_sessions()
    if bool(year_q):
        session_list = session_list.filter(year__icontains=year_q)
    if bool(term_q):
        session_list = session_list.filter(term__code__icontains=term_q)

    session_list = session_list.filter(is_archived=False)
    session_list = adminApi.add_num_instructors(session_list)

    page = request.GET.get('page', 1)
    paginator = Paginator(session_list, settings.PAGE_SIZE)

    try:
        sessions = paginator.page(page)
    except PageNotAnInteger:
        sessions = paginator.page(1)
    except EmptyPage:
        sessions = paginator.page(paginator.num_pages)

    return render(request, 'administrators/sessions/current_sessions.html', {
        'loggedin_user': request.user,
        'sessions': sessions,
        'total_sessions': len(session_list),
        'new_next': adminApi.build_new_next(request)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def archived_sessions(request):
    ''' Display all information of sessions and create a session '''
    request = userApi.has_admin_access(request)

    year_q = request.GET.get('year')
    term_q = request.GET.get('term')

    session_list = adminApi.get_sessions()
    if bool(year_q):
        session_list = session_list.filter(year__icontains=year_q)
    if bool(term_q):
        session_list = session_list.filter(term__code__icontains=term_q)

    session_list = session_list.filter(is_archived=True)
    session_list = adminApi.add_num_instructors(session_list)

    page = request.GET.get('page', 1)
    paginator = Paginator(session_list, settings.PAGE_SIZE)

    try:
        sessions = paginator.page(page)
    except PageNotAnInteger:
        sessions = paginator.page(1)
    except EmptyPage:
        sessions = paginator.page(paginator.num_pages)

    return render(request, 'administrators/sessions/archived_sessions.html', {
        'loggedin_user': request.user,
        'sessions': sessions,
        'total_sessions': len(session_list),
        'new_next': adminApi.build_new_next(request)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_session(request, session_slug):
    ''' Display session details '''
    request = userApi.has_admin_access(request)
    adminApi.can_req_parameters_access(request, 'session', ['next', 'p'])

    return render(request, 'administrators/sessions/show_session.html', {
        'loggedin_user': request.user,
        'session': adminApi.get_session(session_slug, 'slug'),
        'next': adminApi.get_next(request)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_session(request, session_slug):
    ''' Edit a session '''
    request = userApi.has_admin_access(request)
    adminApi.can_req_parameters_access(request, 'session', ['next', 'p'])

    session = adminApi.get_session(session_slug, 'slug')
    if request.method == 'POST':

        # Check whether a next url is valid or not
        adminApi.can_req_parameters_access(request, 'none', ['next'], 'POST')

        form = SessionConfirmationForm(request.POST, instance=session)
        if form.is_valid():
            data = form.cleaned_data
            courses = data['courses']

            if len(courses) == 0:
                messages.error(request, 'An error occurred. Please select courses in this session.')
                return HttpResponseRedirect(request.get_full_path())

            updated_session = form.save(commit=False)
            updated_session.updated_at = datetime.now()

            if data['is_archived']:
                updated_session.is_visible = False

            updated_session.save()

            if updated_session:
                updated_jobs = adminApi.update_session_jobs(session, courses)
                if updated_jobs:
                    messages.success(request, 'Success! {0} {1} {2} updated'.format(session.year, session.term.code, session.title))
                    return HttpResponseRedirect(request.POST.get('next'))
                else:
                    messages.error(request, 'An error occurred while updating courses in a session.')
            else:
                messages.error(request, 'An error occurred while updating a session.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return HttpResponseRedirect(request.get_full_path())

    return render(request, 'administrators/sessions/edit_session.html', {
        'loggedin_user': request.user,
        'session': session,
        'form': SessionConfirmationForm(data=None, instance=session, initial={
            'courses': [ job.course for job in session.job_set.all() ],
            'term': session.term
        }),
        'next': adminApi.get_next(request)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def delete_session_confirmation(request, session_slug):
    ''' Confirmation to delete a Session '''
    request = userApi.has_admin_access(request)
    adminApi.can_req_parameters_access(request, 'session', ['next', 'p'])

    sessions = adminApi.get_sessions()
    if request.method == 'POST':
        adminApi.can_req_parameters_access(request, 'session', ['next'], 'POST')

        session_id = request.POST.get('session')
        deleted_session = adminApi.delete_session(session_id)
        if deleted_session:
            messages.success(request, 'Success! {0} {1} {2} deleted'.format(deleted_session.year, deleted_session.term.code, deleted_session.title))
            return HttpResponseRedirect(request.POST.get('next'))
        else:
            messages.error(request, 'An error occurred. Failed to delete {0} {1} {2}'.format(deleted_session.year, deleted_session.term.code, deleted_session.title))
        return HttpResponseRedirect(request.get_full_path())

    return render(request, 'administrators/sessions/delete_session_confirmation.html', {
        'loggedin_user': request.user,
        'current_sessions': sessions.filter(is_archived=False),
        'archived_sessions': sessions.filter(is_archived=True),
        'session': adminApi.get_session(session_slug, 'slug'),
        'next': adminApi.get_next(request)
    })


# Jobs


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_job(request, session_slug, job_slug):
    ''' Display job details '''
    request = userApi.has_admin_access(request, Role.HR)
    adminApi.can_req_parameters_access(request, 'job-app', ['next', 'p'])

    return render(request, 'administrators/jobs/show_job.html', {
        'loggedin_user': request.user,
        'job': adminApi.get_job_by_session_slug_job_slug(session_slug, job_slug),
        'next': adminApi.get_next(request)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def prepare_jobs(request):
    ''' Display preparing jobs '''
    request = userApi.has_admin_access(request)

    year_q = request.GET.get('year')
    term_q = request.GET.get('term')
    code_q = request.GET.get('code')
    number_q = request.GET.get('number')
    section_q = request.GET.get('section')
    instructor_first_name_q = request.GET.get('instructor_first_name')
    instructor_last_name_q = request.GET.get('instructor_last_name')

    job_list = adminApi.get_jobs()
    if bool(year_q):
        job_list = job_list.filter(session__year__icontains=year_q)
    if bool(term_q):
        job_list = job_list.filter(session__term__code__icontains=term_q)
    if bool(code_q):
        job_list = job_list.filter(course__code__name__icontains=code_q)
    if bool(number_q):
        job_list = job_list.filter(course__number__name__icontains=number_q)
    if bool(section_q):
        job_list = job_list.filter(course__section__name__icontains=section_q)
    if bool(instructor_first_name_q):
        job_list = job_list.filter(instructors__first_name__icontains=instructor_first_name_q)
    if bool(instructor_last_name_q):
        job_list = job_list.filter(instructors__last_name__icontains=instructor_last_name_q)

    page = request.GET.get('page', 1)
    paginator = Paginator(job_list, settings.PAGE_SIZE)

    try:
        jobs = paginator.page(page)
    except PageNotAnInteger:
        jobs = paginator.page(1)
    except EmptyPage:
        jobs = paginator.page(paginator.num_pages)

    return render(request, 'administrators/jobs/prepare_jobs.html', {
        'loggedin_user': request.user,
        'jobs': jobs,
        'total_jobs': len(job_list),
        'new_next': adminApi.build_new_next(request)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def progress_jobs(request):
    ''' See jobs in progress '''
    request = userApi.has_admin_access(request)

    year_q = request.GET.get('year')
    term_q = request.GET.get('term')
    code_q = request.GET.get('code')
    number_q = request.GET.get('number')
    section_q = request.GET.get('section')

    job_list = adminApi.get_jobs()
    if bool(year_q):
        job_list = job_list.filter(session__year__icontains=year_q)
    if bool(term_q):
        job_list = job_list.filter(session__term__code__icontains=term_q)
    if bool(code_q):
        job_list = job_list.filter(course__code__name__icontains=code_q)
    if bool(number_q):
        job_list = job_list.filter(course__number__name__icontains=number_q)
    if bool(section_q):
        job_list = job_list.filter(course__section__name__icontains=section_q)

    page = request.GET.get('page', 1)
    paginator = Paginator(job_list, settings.PAGE_SIZE)

    try:
        jobs = paginator.page(page)
    except PageNotAnInteger:
        jobs = paginator.page(1)
    except EmptyPage:
        jobs = paginator.page(paginator.num_pages)

    return render(request, 'administrators/jobs/progress_jobs.html', {
        'loggedin_user': request.user,
        'jobs': jobs,
        'total_jobs': len(job_list),
        'new_next': adminApi.build_new_next(request)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def instructor_jobs(request):
    ''' Display jobs by instructor '''
    request = userApi.has_admin_access(request)

    first_name_q = request.GET.get('first_name')
    last_name_q = request.GET.get('last_name')
    preferred_name_q = request.GET.get('preferred_name')
    cwl_q = request.GET.get('cwl')

    user_list = userApi.get_instructors()
    if bool(first_name_q):
        user_list = user_list.filter(first_name__icontains=first_name_q)
    if bool(last_name_q):
        user_list = user_list.filter(last_name__icontains=last_name_q)
    if bool(preferred_name_q):
        user_list = user_list.filter(profile__preferred_name__icontains=preferred_name_q)
    if bool(cwl_q):
        user_list = user_list.filter(username__icontains=cwl_q)

    page = request.GET.get('page', 1)
    paginator = Paginator(user_list, settings.PAGE_SIZE)

    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)

    for user in users:
        user.total_applicants = adminApi.add_total_applicants(user)

    return render(request, 'administrators/jobs/instructor_jobs.html', {
        'loggedin_user': request.user,
        'users': users,
        'total_users': len(user_list),
        'new_next': adminApi.build_new_next(request)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def student_jobs(request):
    ''' Display jobs by student '''
    request = userApi.has_admin_access(request)

    first_name_q = request.GET.get('first_name')
    last_name_q = request.GET.get('last_name')
    preferred_name_q = request.GET.get('preferred_name')
    cwl_q = request.GET.get('cwl')

    user_list = userApi.get_users()
    if bool(first_name_q):
        user_list = user_list.filter(first_name__icontains=first_name_q)
    if bool(last_name_q):
        user_list = user_list.filter(last_name__icontains=last_name_q)
    if bool(preferred_name_q):
        user_list = user_list.filter(profile__preferred_name__icontains=preferred_name_q)
    if bool(cwl_q):
        user_list = user_list.filter(username__icontains=cwl_q)

    user_list = user_list.filter(profile__roles__name=Role.STUDENT)

    page = request.GET.get('page', 1)
    paginator = Paginator(user_list, settings.PAGE_SIZE)

    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)

    return render(request, 'administrators/jobs/student_jobs.html', {
        'loggedin_user': request.user,
        'users': users,
        'total_users': len(user_list),
        'new_next': adminApi.build_new_next(request)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_job_applications(request, session_slug, job_slug):
    ''' Display a job's applications '''
    request = userApi.has_admin_access(request)

    job = adminApi.get_job_by_session_slug_job_slug(session_slug, job_slug)
    return render(request, 'administrators/jobs/show_job_applications.html', {
        'loggedin_user': request.user,
        'job': adminApi.add_job_with_applications_statistics(job),
        'app_status': APP_STATUS,
        'next': adminApi.get_next(request)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def instructor_jobs_details(request, username):
    ''' Display jobs that an instructor has '''
    request = userApi.has_admin_access(request)
    adminApi.can_req_parameters_access(request, 'job', ['next', 'p'])

    user = userApi.get_user(username, 'username')
    user.total_applicants = adminApi.add_total_applicants(user)
    return render(request, 'administrators/jobs/instructor_jobs_details.html', {
        'loggedin_user': request.user,
        'user': userApi.add_avatar(user),
        'next': adminApi.get_next(request)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def student_jobs_details(request, username):
    ''' Display jobs that an student has '''
    request = userApi.has_admin_access(request)
    adminApi.can_req_parameters_access(request, 'job-tab', ['next', 'p', 't'])

    next = adminApi.get_next(request)
    page = request.GET.get('p')

    user = userApi.get_user(username, 'username')
    apps = user.application_set.all()
    apps = adminApi.add_app_info_into_applications(apps, ['offered', 'accepted'])

    offered_apps = []
    accepted_apps = []
    for app in apps:
        if app.offered: offered_apps.append(app)
        if app.accepted: accepted_apps.append(app)

    return render(request, 'administrators/jobs/student_jobs_details.html', {
        'loggedin_user': request.user,
        'user': userApi.add_avatar(user),
        'total_assigned_hours': adminApi.get_total_assigned_hours(apps, ['offered', 'accepted']),
        'apps': apps,
        'offered_apps': offered_apps,
        'accepted_apps': accepted_apps,
        'tab_urls': {
            'all': adminApi.build_url(request.path, next, page, 'all'),
            'offered': adminApi.build_url(request.path, next, page, 'offered'),
            'accepted': adminApi.build_url(request.path, next, page, 'accepted')
        },
        'current_tab': request.GET.get('t'),
        'app_status': APP_STATUS,
        'next': next
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_job(request, session_slug, job_slug):
    ''' Edit a job '''
    request = userApi.has_admin_access(request)
    adminApi.can_req_parameters_access(request, 'job', ['next', 'p'])

    job = adminApi.get_job_by_session_slug_job_slug(session_slug, job_slug)
    if request.method == 'POST':

        # Check whether a next url is valid or not
        adminApi.can_req_parameters_access(request, 'none', ['next'], 'POST')

        form = AdminJobEditForm(request.POST, instance=job)
        if form.is_valid():
            updated_job = form.save(commit=False)
            updated_job.updated_at = datetime.now()
            updated_job.save()

            if updated_job:
                messages.success(request, 'Success! {0} {1} {2} {3} {4} updated'.format(updated_job.session.year, updated_job.session.term.code, updated_job.course.code.name, updated_job.course.number.name, updated_job.course.section.name))
                return HttpResponseRedirect(request.POST.get('next'))
            else:
                messages.error(request, 'An error occurred while updating a job.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return HttpResponseRedirect(request.get_full_path())

    return render(request, 'administrators/jobs/edit_job.html', {
        'loggedin_user': request.user,
        'job': job,
        'instructors': job.instructors.all(),
        'form': AdminJobEditForm(data=None, instance=job),
        'next': adminApi.get_next(request)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def search_instructors(request):
    ''' Search job instructors '''
    request = userApi.has_admin_access(request)

    if request.method == 'GET':
        instructors = userApi.get_instructors()
        username = request.GET.get('username')

        data = []
        if bool(username) == True:
            job = adminApi.get_job_by_session_slug_job_slug(request.GET.get('session_slug'), request.GET.get('job_slug'))
            for ins in instructors.filter( Q(username__icontains=username) & ~Q(pk__in=[ins.id for ins in job.instructors.all()]) ):
                data.append({
                    'id': ins.id,
                    'username': ins.username,
                    'first_name': ins.first_name,
                    'last_name': ins.last_name
                })
        return JsonResponse({ 'data': data, 'status': 'success' }, safe=False)
    return JsonResponse({ 'data': [], 'status': 'error' }, safe=False)


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def add_job_instructors(request, session_slug, job_slug):
    ''' Add job instructors '''
    request = userApi.has_admin_access(request)
    if request.method == 'POST':
        job = adminApi.get_job_by_session_slug_job_slug(session_slug, job_slug)

        form = InstructorUpdateForm(request.POST);
        if form.is_valid():
            instructor = form.cleaned_data['instructors']
            insturctors_ids = [ ins.id for ins in job.instructors.all() ]
            if int(request.POST.get('instructors')) in insturctors_ids:
                return JsonResponse({ 'status': 'error', 'message': 'An error occurred. Instructor {0} ({1})is already added int this job.'.format(instructor.first().username, instructor.first().get_full_name()) })

            if adminApi.add_job_instructors(job, form.cleaned_data['instructors']):
                return JsonResponse({
                    'status': 'success',
                    'user': {
                        'id': instructor.first().id,
                        'username': instructor.first().username,
                        'first_name': instructor.first().first_name,
                        'last_name': instructor.first().last_name
                    },
                    'data': {
                        'delete_url': reverse('administrators:delete_job_instructors', args=[session_slug, job_slug]),
                        'csrfmiddlewaretoken': request.POST.get('csrfmiddlewaretoken')
                    },
                    'message': 'Success! Instructor {0} added.'.format(instructor.first().username)
                })

            return JsonResponse({
                'status': 'error',
                'message': 'An error occurred while adding an instructor into a job.'
            })
        else:
            errors = form.errors.get_json_data()
            return JsonResponse({ 'status': 'error', 'message': 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ) })
    return JsonResponse({ 'status': 'error', 'message': 'Request method is not POST.' })



@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_job_instructors(request, session_slug, job_slug):
    ''' Delete job instructors '''
    request = userApi.has_admin_access(request)
    if request.method == 'POST':
        job = adminApi.get_job_by_session_slug_job_slug(session_slug, job_slug)

        if job.instructors.count() == 0:
            return JsonResponse({ 'status': 'error', 'message': 'An error occurred. Instructors are empty.' })

        form = InstructorUpdateForm(request.POST);
        if form.is_valid():
            instructor = form.cleaned_data['instructors']
            insturctors_ids = [ ins.id for ins in job.instructors.all() ]
            if int(request.POST.get('instructors')) not in insturctors_ids:
                return JsonResponse({ 'status': 'error', 'message': 'An error occurred. No instructor {0} {1} exists.'.format(instructor.first().username, instructor.first().get_full_name()) })

            if adminApi.remove_job_instructors(job, instructor):
                return JsonResponse({
                    'status': 'success',
                    'username': instructor.first().username,
                    'message': 'Success! Instructor {0} removed.'.format(instructor.first().username)
                })
            return JsonResponse({ 'status': 'error', 'message': 'An error occurred while removing an instructor into a job.' })
        else:
            errors = form.errors.get_json_data()
            return JsonResponse({ 'status': 'error', 'message': 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ) })
    return JsonResponse({ 'status': 'error', 'message': 'Request method is not POST.' })

# Applications


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_application(request, app_slug):
    ''' Display an application details '''
    request = userApi.has_admin_access(request, Role.HR)
    adminApi.can_req_parameters_access(request, 'app', ['next', 'p'])

    return render(request, 'administrators/applications/show_application.html', {
        'loggedin_user': request.user,
        'app': adminApi.get_application(app_slug, 'slug'),
        'next': adminApi.get_next(request)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def applications_dashboard(request):
    ''' Display a dashboard to take a look at updates '''
    request = userApi.has_admin_access(request)

    year_q = request.GET.get('year')
    term_q = request.GET.get('term')
    code_q = request.GET.get('code')
    number_q = request.GET.get('number')
    section_q = request.GET.get('section')
    first_name_q = request.GET.get('first_name')
    last_name_q = request.GET.get('last_name')

    status_list = adminApi.get_application_statuses()
    if bool(year_q):
        status_list = status_list.filter(application__job__session__year__icontains=year_q)
    if bool(term_q):
        status_list = status_list.filter(application__job__session__term__code__icontains=term_q)
    if bool(code_q):
        status_list = status_list.filter(application__job__course__code__name__icontains=code_q)
    if bool(number_q):
        status_list = status_list.filter(application__job__course__number__name__icontains=number_q)
    if bool(section_q):
        status_list = status_list.filter(application__job__course__section__name__icontains=section_q)
    if bool(first_name_q):
        status_list = status_list.filter(application__applicant__first_name__icontains=first_name_q)
    if bool(last_name_q):
        status_list = status_list.filter(application__applicant__last_name__icontains=last_name_q)

    page = request.GET.get('page', 1)
    paginator = Paginator(status_list, settings.PAGE_SIZE)

    try:
        statuses = paginator.page(page)
    except PageNotAnInteger:
        statuses = paginator.page(1)
    except EmptyPage:
        statuses = paginator.page(paginator.num_pages)



    return render(request, 'administrators/applications/applications_dashboard.html', {
        'loggedin_user': request.user,
        'statuses': statuses,
        'total_statuses': len(status_list),
        'app_status': APP_STATUS,
        'new_next': adminApi.build_new_next(request)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def all_applications(request):
    ''' Display all applications '''
    request = userApi.has_admin_access(request)

    year_q = request.GET.get('year')
    term_q = request.GET.get('term')
    code_q = request.GET.get('code')
    number_q = request.GET.get('number')
    section_q = request.GET.get('section')
    first_name_q = request.GET.get('first_name')
    last_name_q = request.GET.get('last_name')

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

    page = request.GET.get('page', 1)
    paginator = Paginator(app_list, settings.PAGE_SIZE)

    try:
        apps = paginator.page(page)
    except PageNotAnInteger:
        apps = paginator.page(1)
    except EmptyPage:
        apps = paginator.page(paginator.num_pages)

    return render(request, 'administrators/applications/all_applications.html', {
        'loggedin_user': request.user,
        'apps': apps,
        'total_apps': len(app_list),
        'new_next': adminApi.build_new_next(request)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def selected_applications(request):
    ''' Display applications selected by instructors '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':

        # Check whether a next url is valid or not
        adminApi.can_req_parameters_access(request, 'none', ['next'], 'POST')

        if 'classification' not in request.POST.keys() or len(request.POST.get('classification')) == 0:
            messages.error(request, 'An error occurred. Please select classification, then try again.')
            return HttpResponseRedirect(request.POST.get('next'))

        assigned_hours = request.POST.get('assigned_hours')

        if adminApi.is_valid_float(assigned_hours) == False:
            messages.error(request, 'An error occurred. Please check assigned hours. Assigned hours must be numerival value only.')
            return HttpResponseRedirect(request.POST.get('next'))

        if adminApi.is_valid_integer(assigned_hours) == False:
            messages.error(request, 'An error occurred. Please check assigned hours. Assign TA Hours must be non-negative integers.')
            return HttpResponseRedirect(request.POST.get('next'))


        assigned_hours = int( float(assigned_hours) )

        if assigned_hours < 0:
            messages.error(request, 'An error occurred. Please check assigned hours. Assigned hours must be greater than 0.')
            return HttpResponseRedirect(request.POST.get('next'))

        app = adminApi.get_application(request.POST.get('application'))
        if assigned_hours > int(app.job.assigned_ta_hours):
            messages.error(request, 'An error occurred. Please you cannot assign {0} hours Total Assigned TA Hours is {1}, then try again.'.format( assigned_hours, int(app.job.assigned_ta_hours) ))
            return HttpResponseRedirect(request.POST.get('next'))

        if adminApi.update_job_offer(request.POST):
            messages.success(request, 'Success! Updated this application (ID: {0})'.format(app.id))
        else:
            messages.error(request, 'An error occurred. Failed to update this application (ID: {0}).'.format(app.id))

        return HttpResponseRedirect(request.POST.get('next'))
    else:
        year_q = request.GET.get('year')
        term_q = request.GET.get('term')
        code_q = request.GET.get('code')
        number_q = request.GET.get('number')
        section_q = request.GET.get('section')
        first_name_q = request.GET.get('first_name')
        last_name_q = request.GET.get('last_name')
        offered_q = request.GET.get('offered')
        not_offered_q = request.GET.get('not_offered')

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
        if bool(offered_q):
            app_list = app_list.filter(applicationstatus__assigned=ApplicationStatus.OFFERED)
        if bool(not_offered_q):
            app_list = app_list.filter( ~Q(applicationstatus__assigned=ApplicationStatus.OFFERED) )
        
        app_list = app_list.filter(applicationstatus__assigned=ApplicationStatus.SELECTED).order_by('-id').distinct()
        app_list = [ app for app in app_list if app.applicationstatus_set.filter(assigned=ApplicationStatus.NONE).count() == app.applicationstatus_set.filter(assigned=ApplicationStatus.SELECTED).count() ]

        app_list = adminApi.add_app_info_into_applications(app_list, ['resume', 'selected', 'offered', 'declined'])

        page = request.GET.get('page', 1)
        paginator = Paginator(app_list, settings.PAGE_SIZE)

        try:
            apps = paginator.page(page)
        except PageNotAnInteger:
            apps = paginator.page(1)
        except EmptyPage:
            apps = paginator.page(paginator.num_pages)

        for app in apps:
            if app.job.assigned_ta_hours == app.job.accumulated_ta_hours:
                app.ta_hour_progress = 'done'
            elif app.job.assigned_ta_hours < app.job.accumulated_ta_hours:
                app.ta_hour_progress = 'over'
            else:
                if (app.job.assigned_ta_hours * 3.0/4.0) < app.job.accumulated_ta_hours:
                    app.ta_hour_progress = 'under_three_quarters'
                elif (app.job.assigned_ta_hours * 2.0/4.0) < app.job.accumulated_ta_hours:
                    app.ta_hour_progress = 'under_half'
                elif (app.job.assigned_ta_hours * 1.0/4.0) < app.job.accumulated_ta_hours:
                    app.ta_hour_progress = 'under_one_quarter'


        selected_apps_total, selected_apps_stats = adminApi.get_selected_apps_with_stats()

    return render(request, 'administrators/applications/selected_applications.html', {
        'loggedin_user': request.user,
        'apps': apps,
        'total_apps': len(app_list),
        'selected_apps': { 'total': selected_apps_total, 'stats': selected_apps_stats },
        'offered_stats': adminApi.get_offered_stats(apps),
        'classification_choices': adminApi.get_classifications(),
        'app_status': APP_STATUS,
        'new_next': adminApi.build_new_next(request)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def reset_instructor_preference(request):
    ''' Reset instructor preference '''
    request = userApi.has_admin_access(request)

    # Check whether a next url is valid or not
    adminApi.can_req_parameters_access(request, 'none', ['next'], 'POST')

    app_id = request.POST.get('application')
    app = adminApi.add_app_info_into_application(adminApi.get_application(app_id), ['offered'])

    # An offered appliation cannot be reset
    if app.offered != None:
        messages.error(request, 'An error occurred. An offered application cannot be reset.')
        return HttpResponseRedirect(request.POST.get('next'))

    instructor_preference = '0'

    instructor_app_form = InstructorApplicationForm({ 'instructor_preference': instructor_preference })
    if instructor_app_form.is_valid():
        app_status_form = ApplicationStatusForm({ 'application': app_id, 'assigned': '0', 'assigned_hours': '0', 'has_contract_read': False })
        if app_status_form:
            updated_app = adminApi.update_application_instructor_preference(app_id, instructor_preference)
            if updated_app:
                if app_status_form.save():
                    messages.success(request, 'Success! {0}: The Instructor Preference of an Application (ID: {1}, {2} {3} - {4} {5} {6}) has been reset. Please check in <a href="{7}">All Applications</a>'.format(updated_app.applicant.get_full_name(), updated_app.id, updated_app.job.session.year, updated_app.job.session.term.code, updated_app.job.course.code.name, updated_app.job.course.number.name, updated_app.job.course.section.name, reverse('administrators:all_applications')))
                else:
                    messages.error(request, 'An error occurred while updating an application status.')
            else:
                messages.error(request, 'An error occurred while updating an instructor_preference.')
        else:
            errors = app_status_form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))
    else:
        errors = instructor_app_form.errors.get_json_data()
        messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

    return HttpResponseRedirect(request.POST.get('next'))


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def offer_job(request, session_slug, job_slug):
    ''' Admin can offer a job to each job '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':

        # Check whether a next url is valid or not
        adminApi.can_req_parameters_access(request, 'none', ['next'], 'POST')

        if 'classification' not in request.POST.keys() or len(request.POST.get('classification')) == 0:
            messages.error(request, 'An error occurred. Please select classification, then try again.')
            return HttpResponseRedirect(request.POST.get('next'))

        assigned_hours = request.POST.get('assigned_hours')

        if adminApi.is_valid_float(assigned_hours) == False:
            messages.error(request, 'An error occurred. Please check assigned hours. Assigned hours must be numerival value only.')
            return HttpResponseRedirect(request.POST.get('next'))

        if adminApi.is_valid_integer(assigned_hours) == False:
            messages.error(request, 'An error occurred. Please check assigned hours. Assign TA Hours must be non-negative integers.')
            return HttpResponseRedirect(request.POST.get('next'))

        assigned_hours = int( float(assigned_hours) )

        if assigned_hours < 0:
            messages.error(request, 'An error occurred. Please check assigned hours. Assigned hours must be greater than 0.')
            return HttpResponseRedirect(request.POST.get('next'))

        job = adminApi.get_job_by_session_slug_job_slug(session_slug, job_slug)
        if assigned_hours > int(job.assigned_ta_hours):
            messages.error(request, 'An error occurred. Please you cannot assign {0} hours Total Assigned TA Hours is {1}, then try again.'.format( assigned_hours, int(job.assigned_ta_hours) ))
            return HttpResponseRedirect(request.POST.get('next'))

        admin_app_form = AdminApplicationForm(request.POST)
        app_status_form = ApplicationStatusForm(request.POST)

        if admin_app_form.is_valid() and app_status_form.is_valid():
            updated_app = adminApi.update_application_classification_note(request.POST.get('application'), admin_app_form.cleaned_data)
            status = app_status_form.save()

            errors = []
            if not updated_app: errors.append('An error occurred. Failed to update classification and note.')
            if not status: errors.append('An error occurred. Failed to update the application status.')

            if len(errors) > 0:
                messages.error(request, 'An error occurred while sending a job offer. {0}'.format( ' '.join(errors) ))
                return HttpResponseRedirect(request.POST.get('next'))

            applicant = userApi.get_user(request.POST.get('applicant'))
            messages.success(request, 'Success! You offered this user ({0} {1}) {2} hours for this job ({3} {4} - {5} {6} {7})'.format(applicant.first_name, applicant.last_name, assigned_hours, job.session.year, job.session.term.code, job.course.code.name, job.course.number.name, job.course.section.name))
        else:
            errors = []

            admin_app_errors = admin_app_form.errors.get_json_data()
            app_status_errors = app_status_form.errors.get_json_data()

            if admin_app_errors: errors.append( userApi.get_error_messages(admin_app_errors) )
            if app_status_errors: errors.append( userApi.get_error_messages(app_status_errors) )

            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

    return HttpResponseRedirect(request.POST.get('next'))


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def offered_applications(request):
    ''' Display applications offered by admins '''
    request = userApi.has_admin_access(request)

    year_q = request.GET.get('year')
    term_q = request.GET.get('term')
    code_q = request.GET.get('code')
    number_q = request.GET.get('number')
    section_q = request.GET.get('section')
    first_name_q = request.GET.get('first_name')
    last_name_q = request.GET.get('last_name')
    no_response_q = request.GET.get('no_response')

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
    if bool(no_response_q):
        app_list = adminApi.get_offered_apps_no_response(app_list)

    if bool(no_response_q) == False:
        app_list = app_list.filter(applicationstatus__assigned=ApplicationStatus.OFFERED).order_by('-id').distinct()

    app_list = adminApi.add_app_info_into_applications(app_list, ['offered', 'accepted', 'declined'])

    page = request.GET.get('page', 1)
    paginator = Paginator(app_list, settings.PAGE_SIZE)

    try:
        apps = paginator.page(page)
    except PageNotAnInteger:
        apps = paginator.page(1)
    except EmptyPage:
        apps = paginator.page(paginator.num_pages)

    return render(request, 'administrators/applications/offered_applications.html', {
        'loggedin_user': request.user,
        'apps': apps,
        'total_apps': len(app_list),
        'admin_emails': adminApi.get_admin_emails(),
        'new_next': adminApi.build_new_next(request)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def accepted_applications(request):
    ''' Display applications accepted by students '''
    request = userApi.has_admin_access(request, Role.HR)

    today = datetime.today().strftime('%Y-%m-%d')

    year_q = request.GET.get('year')
    term_q = request.GET.get('term')
    code_q = request.GET.get('code')
    number_q = request.GET.get('number')
    section_q = request.GET.get('section')
    first_name_q = request.GET.get('first_name')
    last_name_q = request.GET.get('last_name')
    eform_q = request.GET.get('eform')
    declined_reassigned_q = request.GET.get('declined_reassigned')
    accepted_in_today_q = request.GET.get('accepted_in_today')

    app_list = adminApi.get_applications()
    today_accepted_apps, today = adminApi.get_accepted_apps_by_day(app_list, 'today')

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
    if bool(eform_q):
        if eform_q.lower() == 'none':
            app_list = app_list.filter(admindocuments__eform__isnull=True)
        else:
            app_list = app_list.filter(admindocuments__eform__icontains=eform_q)
    if bool(declined_reassigned_q):
        app_list = app_list.filter(is_declined_reassigned=True)
    if bool(accepted_in_today_q):
        app_list = today_accepted_apps

    if bool(accepted_in_today_q) ==  False:
        app_list = app_list.filter( Q(applicationstatus__assigned=ApplicationStatus.ACCEPTED) & Q(is_terminated=False) ).order_by('-id').distinct()

    page = request.GET.get('page', 1)
    paginator = Paginator(app_list, settings.PAGE_SIZE)

    try:
        apps = paginator.page(page)
    except PageNotAnInteger:
        apps = paginator.page(1)
    except EmptyPage:
        apps = paginator.page(paginator.num_pages)

    apps = adminApi.add_app_info_into_applications(apps, ['accepted'])

    return render(request, 'administrators/applications/accepted_applications.html', {
        'loggedin_user': request.user,
        'apps': adminApi.add_salary(apps),
        'eform_stats': adminApi.get_eform_stats(apps),
        'total_apps': len(app_list),
        'new_next': adminApi.build_new_next(request),
        'today_accepted_apps': today_accepted_apps,
        'today_eform_stats': adminApi.get_eform_stats(today_accepted_apps),
        'today': today
    })


@require_http_methods(['POST'])
def update_admin_docs(request):
    ''' Get admin docs request '''

    if request.method == 'POST':
        admin_docs = adminApi.get_admin_docs(request.POST.get('application'))
        form = AdminDocumentsForm(request.POST, instance=admin_docs)
        if form.is_valid():
            saved_admin_docs = form.save()
            if saved_admin_docs:
                if adminApi.add_admin_docs_user(saved_admin_docs, request.user):
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Success! Admin Documents of {0} updated (Application ID: {1}).'.format( saved_admin_docs.application.applicant.get_full_name(), saved_admin_docs.application.id )
                    })
                else:
                    return JsonResponse({ 'status': 'error', 'message': 'An error occurred while saving admin docs user.' }, status=400)
            else:
                return JsonResponse({ 'status': 'error', 'message': 'An error occurred while saving admin docs.' }, status=400)
        else:
            errors = form.errors.get_json_data()
            return JsonResponse({ 'status': 'error', 'message': 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ) }, status=400)

    return JsonResponse({ 'status': 'error', 'message': 'Request method is not POST.' }, status=400)


@require_http_methods(['POST'])
def import_accepted_apps(request):
    ''' Import accepted applications '''
    if request.method == 'POST':
        file = request.FILES.get('file')
        file_split = os.path.splitext(file.name)

        # only csv is allowed to update
        if 'csv' not in file_split[1].lower():
            messages.error(request, 'An error occurred. Only CSV files are allowed to update. Please check your file.')
            return HttpResponseRedirect(request.POST.get('next'))

        data = StringIO(file.read().decode())
        result, msg = adminApi.bulk_update_admin_docs(data, request.user)
        #print('import_accepted_apps', result, msg)
        if result:
            if len(msg) > 0:
                messages.success( request, 'Success! Updated the following fields in Admin Docs through CSV. {0}'.format(msg) )
            else:
                messages.warning(request, 'Warning! No data was updated in the database. Please check your data inputs.')
        else:
            messages.error(request, msg)

    return HttpResponseRedirect(request.POST.get('next'))


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def declined_applications(request):
    ''' Display applications declined by students '''
    request = userApi.has_admin_access(request)

    year_q = request.GET.get('year')
    term_q = request.GET.get('term')
    code_q = request.GET.get('code')
    number_q = request.GET.get('number')
    section_q = request.GET.get('section')
    first_name_q = request.GET.get('first_name')
    last_name_q = request.GET.get('last_name')

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

    app_list = app_list.filter(applicationstatus__assigned=ApplicationStatus.DECLINED).order_by('-id').distinct()
    app_list = adminApi.add_app_info_into_applications(app_list, ['declined'])

    page = request.GET.get('page', 1)
    paginator = Paginator(app_list, settings.PAGE_SIZE)

    try:
        apps = paginator.page(page)
    except PageNotAnInteger:
        apps = paginator.page(1)
    except EmptyPage:
        apps = paginator.page(paginator.num_pages)

    return render(request, 'administrators/applications/declined_applications.html', {
        'loggedin_user': request.user,
        'apps': apps,
        'total_apps': len(app_list),
        'admin_emails': adminApi.get_admin_emails(),
        'new_next': adminApi.build_new_next(request)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def email_history(request):
    ''' Display all of email sent by admins to let them know job offers '''
    request = userApi.has_admin_access(request)

    receiver_q = request.GET.get('receiver')
    title_q = request.GET.get('title')
    message_q = request.GET.get('message')
    type_q = request.GET.get('type')
    no_response_q = request.GET.get('no_response')

    email_list = adminApi.get_emails()
    if bool(receiver_q):
        email_list = email_list.filter(receiver__icontains=receiver_q)
    if bool(title_q):
        email_list = email_list.filter(title__icontains=title_q)
    if bool(message_q):
        email_list = email_list.filter(message__icontains=message_q)
    if bool(type_q):
        email_list = email_list.filter(type__icontains=type_q)
    if bool(no_response_q):
        email_list = email_list.filter(application__applicationstatus__assigned=ApplicationStatus.OFFERED).filter( ~Q(application__applicationstatus__assigned=ApplicationStatus.ACCEPTED) & ~Q(application__applicationstatus__assigned=ApplicationStatus.DECLINED) ).order_by('-id').distinct()

    page = request.GET.get('page', 1)
    paginator = Paginator(email_list, settings.PAGE_SIZE)

    try:
        emails = paginator.page(page)
    except PageNotAnInteger:
        emails = paginator.page(1)
    except EmptyPage:
        emails = paginator.page(paginator.num_pages)

    for email in emails:
        email.application = adminApi.add_app_info_into_application(email.application, ['offered', 'accepted', 'declined'])

    return render(request, 'administrators/applications/email_history.html', {
        'loggedin_user': request.user,
        'emails': emails,
        'total': len(email_list),
        'new_next': adminApi.build_new_next(request)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def send_reminder(request, email_id):
    ''' Send a reminder email '''
    request = userApi.has_admin_access(request)
    adminApi.can_req_parameters_access(request, 'app', ['next', 'p'])

    email = None
    if request.method == 'POST':

        # Check whether a next url is valid or not
        adminApi.can_req_parameters_access(request, 'none', ['next'], 'POST')

        form = ReminderForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            sent_email = adminApi.send_and_create_email(data['application'], data['sender'], data['receiver'], data['title'], data['message'], data['type'])
            if sent_email:
                messages.success(request, 'Success! Email has sent to {0}'.format(data['receiver']))
                return HttpResponseRedirect(request.POST.get('next'))
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return HttpResponseRedirect(request.get_full_path())

    else:
        email = adminApi.get_email(email_id)

    return render(request, 'administrators/applications/send_reminder.html', {
        'loggedin_user': request.user,
        'email': email,
        'form': ReminderForm(data=None, instance=email, initial={
            'title': 'REMINDER: ' + email.title
        }),
        'next': adminApi.get_next(request)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def decline_reassign(request):
    ''' Decline and reassign a job offer with new assigned hours '''
    request = userApi.has_admin_access(request)
    adminApi.can_req_parameters_access(request, 'none', ['next'])
    next = adminApi.get_next(request)
    if request.method == 'POST':
        app = adminApi.get_application( request.POST.get('application') )

        old_assigned_hours = request.POST.get('old_assigned_hours')
        new_assigned_hours = request.POST.get('new_assigned_hours')

        if adminApi.is_valid_float(old_assigned_hours) == False:
            messages.error(request, 'An error occurred. Please contact administrators. Your old assigned hours must be numerival value only.')
            return HttpResponseRedirect(next)

        if adminApi.is_valid_integer(old_assigned_hours) == False:
            messages.error(request, 'An error occurred. Please check assigned hours. Assign TA Hours must be non-negative integers.')
            return HttpResponseRedirect(next)

        if adminApi.is_valid_float(new_assigned_hours) == False:
            messages.error(request, 'An error occurred. Please check assigned hours. Your new assigned hours must be numerival value only.')
            return HttpResponseRedirect(next)

        if adminApi.is_valid_integer(new_assigned_hours) == False:
            messages.error(request, 'An error occurred. Please check assigned hours. Assign TA Hours must be non-negative integers.')
            return HttpResponseRedirect(next)

        old_assigned_hours = int( float(old_assigned_hours) )
        new_assigned_hours = int( float(new_assigned_hours) )

        if new_assigned_hours < 0:
            messages.error(request, 'An error occurred. Please check assigned hours. Your new assigned hours must be greater than 0.')
            return HttpResponseRedirect(next)

        if new_assigned_hours == 0 or new_assigned_hours > int(app.job.assigned_ta_hours):
            messages.error(request, 'An error occurred. Please check assigned hours. Valid assigned hours are between 0 and {0}'.format( int(app.job.assigned_ta_hours) ))
            return HttpResponseRedirect(next)

        request.session['decline_reassign_form_data'] = request.POST
        return HttpResponseRedirect( reverse('administrators:decline_reassign_confirmation') + '?next=' + next )

    return HttpResponseRedirect(next)

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def decline_reassign_confirmation(request):
    ''' Display currnt status and new status for reassigning confirmation '''
    request = userApi.has_admin_access(request)
    adminApi.can_req_parameters_access(request, 'none', ['next'])

    app = None
    old_assigned_hours = None
    new_assigned_hours = None
    new_ta_hours = None
    if request.method == 'POST':

        # Check whether a next url is valid or not
        adminApi.can_req_parameters_access(request, 'none', ['next'], 'POST')

        if request.POST.get('is_declined_reassigned') == None:
            messages.error(request, 'An error occurred. Please click on the checkbox to decline and re-assign.')
            return HttpResponseRedirect(request.get_full_path())

        app_id = request.POST.get('application')
        old_assigned_hours = request.POST.get('old_assigned_hours')
        new_assigned_hours = request.POST.get('new_assigned_hours')
        app = adminApi.get_application(app_id)
        accepted_status = adminApi.get_accepted_status(app)

        status_form = ApplicationStatusReassignForm({
            'application': app_id,
            'assigned': ApplicationStatus.DECLINED,
            'assigned_hours': new_assigned_hours,
            'parent_id': accepted_status.id
        })

        reassign_form = ReassignApplicationForm(request.POST, instance=app)

        if status_form.is_valid() and reassign_form.is_valid():
            app_status = status_form.save()

            reaasigned_app = reassign_form.save(commit=False)
            reaasigned_app.updated_at = datetime.now()
            reaasigned_app.save()

            errors = []
            if not app_status: errors.append('An error occurred while saving a declined status.')
            if not reaasigned_app: errors.append('An error occurred. Failed to update a note in the application.')

            if len(errors) > 0:
                messages.error(request, 'An error occurred while sending a job offer. {0}'.format( ' '.join(errors) ))
                return HttpResponseRedirect(request.get_full_path())

            # admin documents updated
            if hasattr(reaasigned_app, 'admindocuments'):
                old_eform = reaasigned_app.admindocuments.eform
                reaasigned_app.admindocuments.eform = None
                reaasigned_app.admindocuments.processing_note += '<p>Auto update: eForm - <strong class="text-primary">{0}</strong> on {1}</p>'.format(old_eform, datetime.today().strftime('%Y-%m-%d'))
                reaasigned_app.admindocuments.save(update_fields=['eform', 'processing_note'])

                if reaasigned_app.admindocuments.processing_note.find(old_eform) > -1:
                    messages.success(request, 'Success! The status of Application (ID: {0}) updated'.format(app_id))
                else:
                    reaasigned_app.admindocuments.eform = old_eform
                    reaasigned_app.admindocuments.save(update_fields=['eform'])
                    messages.warning(request, 'Warning! The eForm number of Application (ID: {0}) is not updated into the processing note.'.format(app_id))
            else:
                messages.success(request, 'Success! The status of Application (ID: {0}) updated'.format(app_id))

            return HttpResponseRedirect(request.POST.get('next'))

        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return HttpResponseRedirect(request.get_full_path())

    else:
        data = request.session.get('decline_reassign_form_data')
        if data:
            app_id = data.get('application')
            old_assigned_hours = data.get('old_assigned_hours')
            new_assigned_hours = data.get('new_assigned_hours')

            app = adminApi.get_application(app_id)
            ta_hours = app.job.accumulated_ta_hours
            new_ta_hours = float(ta_hours) - float(old_assigned_hours) + float(new_assigned_hours)

    return render(request, 'administrators/applications/decline_reassign_confirmation.html', {
        'loggedin_user': request.user,
        'app': app,
        'old_assigned_hours': old_assigned_hours,
        'new_assigned_hours': new_assigned_hours,
        'new_ta_hours': new_ta_hours,
        'form': ReassignApplicationForm(data=None, instance=app),
        'next': adminApi.get_next(request)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET','POST'])
def terminate(request, app_slug):
    ''' Terminate an application, then students can can their accepted jobs '''
    request = userApi.has_admin_access(request)
    adminApi.can_req_parameters_access(request, 'none', ['next'])

    app = adminApi.get_application(app_slug, 'slug')
    if app.is_terminated: raise Http404

    if request.method == 'POST':

        # Check whether a next url is valid or not
        adminApi.can_req_parameters_access(request, 'none', ['next'], 'POST')

        if request.POST.get('is_terminated') == None:
            messages.error(request, 'An error occurred. Please click on the checkbox to terminate.')
            return HttpResponseRedirect(request.get_full_path())

        form = TerminateApplicationForm(request.POST, instance=app)
        if form.is_valid():
            terminated_app = form.save(commit=False)
            terminated_app.updated_at = datetime.now()
            terminated_app.save()
            if terminated_app:
                messages.success(request, 'Success! Application (ID: {0}) terminated.'.format(terminated_app.id))
                return HttpResponseRedirect(request.POST.get('next'))
            else:
                messages.error(request, 'An error occurred while termniating an application.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return HttpResponseRedirect(request.get_full_path())

    return render(request, 'administrators/applications/terminate.html', {
        'loggedin_user': request.user,
        'app': app,
        'form': TerminateApplicationForm(data=None, instance=app),
        'next': adminApi.get_next(request)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def terminated_applications(request):
    ''' Terminated applications '''
    request = userApi.has_admin_access(request)

    year_q = request.GET.get('year')
    term_q = request.GET.get('term')
    code_q = request.GET.get('code')
    number_q = request.GET.get('number')
    section_q = request.GET.get('section')
    first_name_q = request.GET.get('first_name')
    last_name_q = request.GET.get('last_name')

    app_list = adminApi.get_terminated_applications()
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

    page = request.GET.get('page', 1)
    paginator = Paginator(app_list, settings.PAGE_SIZE)

    try:
        apps = paginator.page(page)
    except PageNotAnInteger:
        apps = paginator.page(1)
    except EmptyPage:
        apps = paginator.page(paginator.num_pages)

    return render(request, 'administrators/applications/terminated_applications.html', {
        'loggedin_user': request.user,
        'apps': apps,
        'total_apps': len(app_list),
        'admin_emails': adminApi.get_admin_emails(),
        'new_next': adminApi.build_new_next(request)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def applications_send_email(request):
    ''' Send an email for applications '''
    request = userApi.has_admin_access(request)
    adminApi.can_req_parameters_access(request, 'app', ['next', 'p'])

    if request.method == 'POST':
        applications = request.POST.getlist('application')
        if len(applications) > 0:
            type = request.POST.get('type')
            request.session['applications_form_data'] = {
                'applications': applications,
                'type': type
            }
            return HttpResponseRedirect(reverse('administrators:applications_send_email_confirmation') + '?next=' + adminApi.get_next(request) + '&p=' + request.GET.get('p'))
        else:
            messages.error(request, 'An error occurred. Please select applications, then try again.')

    return HttpResponseRedirect(adminApi.get_next(request))


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def applications_send_email_confirmation(request):
    ''' Display a list of email for offered applications '''
    request = userApi.has_admin_access(request)
    adminApi.can_req_parameters_access(request, 'app', ['next', 'p'])

    path = request.GET.get('p')

    applications = []
    receiver_list = []
    form = None
    type = None
    admin_email = None

    form_data = request.session.get('applications_form_data')
    if form_data:
        app_ids = form_data['applications']
        applications = adminApi.get_applications_with_multiple_ids_by_path(app_ids, path)
        receiver_list = [ app.applicant.email for app in applications ]

        if request.method == 'POST':

            # Check whether a next url is valid or not
            adminApi.can_req_parameters_access(request, 'none', ['next'], 'POST')

            form = EmailForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data

                receivers = []
                count = 0
                for app in applications:
                    assigned_hours = None
                    if path == 'Offered Applications':
                        assigned_hours = app.offered.assigned_hours
                    elif path == 'Declined Applications':
                        assigned_hours = app.declined.assigned_hours
                    elif path == 'Terminated Applications':
                        assigned_hours = app.accepted.assigned_hours

                    instructors = []
                    for instructor in app.job.instructors.all():
                        instructors.append(instructor.get_full_name())

                    name = app.applicant.first_name + ' ' + app.applicant.last_name
                    message = data['message'].format(
                        name,
                        app.applicant.profile.student_number,
                        app.job.session.year + ' ' + app.job.session.term.code,
                        app.job.course.code.name + ' ' + app.job.course.number.name + ' ' + app.job.course.section.name,
                        ', '.join(instructors),
                        assigned_hours,
                        app.classification.name
                    )

                    receiver = '{0} <{1}>'.format(name, app.applicant.email)

                    email = adminApi.send_and_create_email(app, data['sender'], receiver, data['title'], message, data['type'])
                    if email:
                        receivers.append(app.applicant.email)
                        count += 1

                if count == len(applications):
                    messages.success(request, 'Success! Email has been sent to {0}'.format( data['receiver'] ))
                else:
                    if len(receivers) > 0:
                        messages.error( request, 'An error occurred. Email has been sent to {0}, but not all receivers. Please check a list of receivers.'.format(', '.join(receivers)) )
                    else:
                        messages.error(request, 'An error occurred. Failed to send emails')

                del request.session['applications_form_data']
                return HttpResponseRedirect(request.POST.get('next'))
            else:
                errors = form.errors.get_json_data()
                messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

            return HttpResponseRedirect(request.get_full_path())

        else:
            type = form_data['type']
            admin_email = adminApi.get_admin_email_by_slug(type)
            title = admin_email.title
            message = admin_email.message

            form = EmailForm(initial={
                'sender': settings.EMAIL_FROM,
                'receiver': receiver_list,
                'title': title,
                'message': message,
                'type': admin_email.type
            })

    return render(request, 'administrators/applications/applications_send_email_confirmation.html', {
        'loggedin_user': request.user,
        'applications': applications,
        'sender': settings.EMAIL_FROM,
        'receiver': receiver_list,
        'form': form,
        'admin_email': admin_email if admin_email else None,
        'path': path,
        'next': adminApi.get_next(request)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def report_accepted_applications(request):
    ''' Display a report of applications accepted by students '''
    request = userApi.has_admin_access(request)

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

    app_list = app_list.filter( Q(applicationstatus__assigned=ApplicationStatus.ACCEPTED) & Q(is_terminated=False) ).order_by('-id').distinct()
    app_list = adminApi.add_app_info_into_applications(app_list, ['accepted', 'declined'])
    app_list = [ app for app in app_list if (app.declined == None) or (app.declined != None and app.accepted.id > app.declined.id) ]

    page = request.GET.get('page', 1)
    paginator = Paginator(app_list, settings.PAGE_SIZE)

    try:
    	apps = paginator.page(page)
    except PageNotAnInteger:
    	apps = paginator.page(1)
    except EmptyPage:
    	apps = paginator.page(paginator.num_pages)

    return render(request, 'administrators/applications/report_accepted_applications.html', {
        'loggedin_user': request.user,
        'apps': apps,
        'total_apps': len(app_list)
    })


# HR


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def all_users(request):
    ''' Display all users'''
    request = userApi.has_admin_access(request)

    first_name_q = request.GET.get('first_name')
    last_name_q = request.GET.get('last_name')
    preferred_name_q = request.GET.get('preferred_name')
    cwl_q = request.GET.get('cwl')
    student_number_q = request.GET.get('student_number')
    employee_number_q = request.GET.get('employee_number')

    user_list = userApi.get_users()
    if bool(first_name_q):
        user_list = user_list.filter(first_name__icontains=first_name_q)
    if bool(last_name_q):
        user_list = user_list.filter(last_name__icontains=last_name_q)
    if bool(preferred_name_q):
        user_list = user_list.filter(profile__preferred_name__icontains=preferred_name_q)
    if bool(cwl_q):
        user_list = user_list.filter(username__icontains=cwl_q)
    if bool(student_number_q):
        user_list = user_list.filter(profile__student_number__icontains=student_number_q)
    if bool(employee_number_q):
        user_list = user_list.filter(confidentiality__employee_number__icontains=employee_number_q)


    page = request.GET.get('page', 1)
    paginator = Paginator(user_list, settings.PAGE_SIZE)

    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)

    return render(request, 'administrators/hr/all_users.html', {
        'loggedin_user': request.user,
        'users': users,
        'total_users': len(user_list),
        'new_next': adminApi.build_new_next(request)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def create_user(request):
    ''' Create a user '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        validation = userApi.validate_post(request.POST, ['first_name', 'last_name', 'email', 'username'])
        if len(validation) > 0:
            messages.error(request, 'An error occurred while saving an User Form. {0}: This field is required.'.format( ', '.join(validation) ))
            return redirect('administrators:create_user')

        user_form = UserForm(request.POST)
        user_profile_form = UserProfileForm(request.POST)

        if user_form.is_valid() and user_profile_form.is_valid():
            user = user_form.save(commit=False)
            user.set_password( userApi.password_generator() )
            user.save()

            profile = userApi.create_profile(user, user_profile_form.cleaned_data)

            errors = []
            if not user: errors.append('An error occurred while creating an user.')
            if not profile: errors.append('An error occurred while creating an user profile.')

            if len(errors) > 0:
                messages.error(request, 'An error occurred while saving an User Form. {0}'.format( ' '.join(errors) ))
                return redirect('administrators:create_user')

            confidentiality = userApi.has_user_confidentiality_created(user)

            data = {
                'user': user.id,
                'is_new_employee': False if request.POST.get('is_new_employee') == None else True,
                'employee_number': request.POST.get('employee_number')
            }
            employee_number_form = EmployeeNumberEditForm(data, instance=confidentiality)

            if employee_number_form.is_valid() == False:
                employee_number_errors = employee_number_form.errors.get_json_data()
                messages.error(request, 'An error occurred while creating an User Form. {0}'.format(employee_number_errors))

            employee_number = employee_number_form.save(commit=False)
            employee_number.created_at = datetime.now()
            employee_number.updated_at = datetime.now()
            employee_number.save()

            if not employee_number: errors.append('An error occurred while updating an employee number.')

            if len(errors) > 0:
                messages.error(request, 'An error occurred while saving an User Form. {0}'.format( ' '.join(errors) ))
                return redirect('administrators:create_user')

            messages.success(request, 'Success! {0} {1} (CWL: {2}) created'.format(user.first_name, user.last_name, user.username))
            return redirect('administrators:all_users')

        else:
            errors = []

            user_errors = user_form.errors.get_json_data()
            profile_errors = user_profile_form.errors.get_json_data()

            if user_errors: errors.append( userApi.get_error_messages(user_errors) )
            if profile_errors: errors.append( userApi.get_error_messages(profile_errors) )

            messages.error(request, 'An error occurred while creating an User Form. {0}'.format( ' '.join(errors) ))

        return redirect('administrators:create_user')

    return render(request, 'administrators/hr/create_user.html', {
        'loggedin_user': request.user,
        'users': userApi.get_users(),
        'user_form': UserForm(),
        'user_profile_form': UserProfileForm(),
        'employee_number_form': EmployeeNumberForm()
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_user(request, username):
    ''' Edit a user '''
    request = userApi.has_admin_access(request)
    adminApi.can_req_parameters_access(request, 'user', ['next', 'p'])

    user = userApi.get_user(username, 'username')
    confidentiality = userApi.has_user_confidentiality_created(user)

    # Create a confiential information if it's None
    if confidentiality == None:
        confidentiality = userApi.create_confidentiality(user)

    if request.method == 'POST':
        # Check whether a next url is valid or not
        adminApi.can_req_parameters_access(request, 'none', ['next'], 'POST')

        validation = userApi.validate_post(request.POST, ['first_name', 'last_name', 'email', 'username'])
        if len(validation) > 0:
            messages.error(request, 'An error occurred while updating an User Edit Form. {0}: This field is required.'.format( ', '.join(validation) ))
            return HttpResponseRedirect(request.get_full_path())

        #user_id = request.POST.get('user')
        #employee_number = request.POST.get('employee_number')
        profile_roles = user.profile.roles.all()

        user_form = UserForm(request.POST, instance=user)
        user_profile_edit_form = UserProfileEditForm(request.POST, instance=user.profile)
        employee_number_form = EmployeeNumberEditForm(request.POST, instance=confidentiality)

        if user_form.is_valid() and user_profile_edit_form.is_valid() and employee_number_form.is_valid():
            updated_user = user_form.save()

            updated_profile = user_profile_edit_form.save(commit=False)
            updated_profile.updated_at = datetime.now()
            updated_profile.save()

            errors = []

            updated_employee_number = employee_number_form.save(commit=False)
            updated_employee_number.updated_at = datetime.now()
            updated_employee_number.is_new_employee = employee_number_form.cleaned_data['is_new_employee']
            updated_employee_number.employee_number = employee_number_form.cleaned_data['employee_number']
            updated_employee_number.save(update_fields=['is_new_employee', 'employee_number', 'updated_at'])

            if not updated_user: errors.append('USER')
            if not updated_profile: errors.append('PROFILE')
            if not updated_employee_number: errors.append('EMPLOYEE NUMBER')

            updated = userApi.update_user_profile_roles(updated_profile, profile_roles, user_profile_edit_form.cleaned_data)
            if not updated: errors.append(request, 'An error occurred while updating profile roles.')

            if len(errors) > 0:
                messages.error(request, 'An error occurred while updating an User Edit Form. {0}'.format( ' '.join(errors) ))
                return HttpResponseRedirect(request.get_full_path())

            messages.success(request, 'Success! User information of {0} (CWL: {1}) updated'.format(user.get_full_name(), user.username))
            return HttpResponseRedirect(request.POST.get('next'))
        else:
            errors = []

            user_errors = user_form.errors.get_json_data()
            profile_errors = user_profile_edit_form.errors.get_json_data()
            confid_errors = employee_number_form.errors.get_json_data()

            if user_errors: errors.append( userApi.get_error_messages(user_errors) )
            if profile_errors: errors.append( userApi.get_error_messages(profile_errors) )
            if confid_errors: errors.append( userApi.get_error_messages(confid_errors) )

            messages.error(request, 'An error occurred while updating an User Form. {0}'.format( ' '.join(errors) ))

        return HttpResponseRedirect(request.get_full_path())

    else:
        profile = userApi.has_user_profile_created(user)
        if profile == None:
            profile = userApi.create_profile_init(user)
            user = userApi.get_user(username, 'username')
            messages.warning(request, 'This user (CWL: {0}) does not have any profile. Users must have at least one role. Please choose a role.'.format(user.username))

    return render(request, 'administrators/hr/edit_user.html', {
        'loggedin_user': request.user,
        'user': userApi.add_avatar(user),
        'roles': userApi.get_roles(),
        'user_form': UserForm(data=None, instance=user),
        'user_profile_form': UserProfileEditForm(data=None, instance=user.profile),
        'employee_number_form': EmployeeNumberEditForm(data=None, instance=confidentiality),
        'next': adminApi.get_next(request)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET','POST'])
def delete_user_confirmation(request, username):
    ''' Delete a user '''
    request = userApi.has_admin_access(request)
    adminApi.can_req_parameters_access(request, 'user', ['next', 'p'])

    user = userApi.get_user(username, 'username')
    apps = []
    if request.method == 'POST':
        user_id = request.POST.get('user')
        deleted_user = userApi.delete_user(user_id)
        if deleted_user:
            messages.success(request, 'Success! {0} {1} ({2}) deleted'.format(deleted_user.first_name, deleted_user.last_name, deleted_user.username))
        else:
            messages.error(request, 'An error occurred while deleting a user.')

        return HttpResponseRedirect(request.POST.get('next'))

    else:
        user = userApi.add_confidentiality_given_list(user, ['sin','study_permit'])
        user = userApi.add_personal_data_form(user)
        app_list = adminApi.get_applications_user(user)
        for app in app_list:
            app = adminApi.add_app_info_into_application(app, ['accepted'])
            if app.accepted == None:
                app.new_accumulated_ta_hours = app.job.accumulated_ta_hours
            else:
                app.new_accumulated_ta_hours = app.job.accumulated_ta_hours - app.accepted.assigned_hours
            apps.append(app)

    return render(request, 'administrators/hr/delete_user_confirmation.html', {
        'loggedin_user': request.user,
        'user': userApi.add_resume(user),
        'users': userApi.get_users(),
        'apps': apps,
        'next': adminApi.get_next(request)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def destroy_user_contents(request):
    ''' Destroy users who have no actions for 3 years '''
    request = userApi.has_admin_access(request)

    users = None
    target_date = None
    if request.method == 'POST':
        data = request.POST.getlist('user')
        count = 0
        for user_id in data:
            deleted = userApi.destroy_profile_resume_confidentiality(user_id)
            if deleted: count += 1

        if count == len(data):
            messages.success(request, 'Success! The contents of User IDs {0} are deleted'.format(data))
        else:
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return redirect('administrators:destroy_user_contents')
    else:
        user_list, target_date = userApi.get_users('destroy')
        users = []
        for user in user_list:
            user = userApi.add_confidentiality_given_list(user, ['sin','study_permit'])
            user = userApi.add_personal_data_form(user)
            user = userApi.add_resume(user)
            users.append(user)

    return render(request, 'administrators/hr/destroy_user_contents.html', {
        'loggedin_user': request.user,
        'users': users,
        'target_date': target_date
    })


# Courses


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def all_courses(request):
    ''' Display all courses and edit/delete a course '''
    request = userApi.has_admin_access(request)

    term_q = request.GET.get('term')
    code_q = request.GET.get('code')
    number_q = request.GET.get('number')
    section_q = request.GET.get('section')
    course_name_q = request.GET.get('course_name')

    course_list = adminApi.get_courses()
    if bool(term_q):
        course_list = course_list.filter(term__code__icontains=term_q)
    if bool(code_q):
        course_list = course_list.filter(code__name__icontains=code_q)
    if bool(number_q):
        course_list = course_list.filter(number__name__icontains=number_q)
    if bool(section_q):
        course_list = course_list.filter(section__name__icontains=section_q)
    if bool(course_name_q):
        course_list = course_list.filter(name__icontains=course_name_q)

    page = request.GET.get('page', 1)
    paginator = Paginator(course_list, settings.PAGE_SIZE)

    try:
        courses = paginator.page(page)
    except PageNotAnInteger:
        courses = paginator.page(1)
    except EmptyPage:
        courses = paginator.page(paginator.num_pages)

    return render(request, 'administrators/courses/all_courses.html', {
        'loggedin_user': request.user,
        'courses': courses,
        'total_courses': len(course_list)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def create_course(request):
    ''' Create a course '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            if course:
                messages.success(request, 'Success! {0} {1} {2} {3} created'.format(course.code.name, course.number.name, course.section.name, course.term.code))
                return redirect('administrators:all_courses')
            else:
                messages.error(request, 'An error occurred while creating a course. Please contact administrators or try it again.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return redirect('administrators:create_course')

    return render(request, 'administrators/courses/create_course.html', {
        'loggedin_user': request.user,
        'courses': adminApi.get_courses(),
        'form': CourseForm()
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_course(request, course_slug):
    ''' Edit a course '''
    request = userApi.has_admin_access(request)
    adminApi.can_req_parameters_access(request, 'none', ['next'])

    course = adminApi.get_course(course_slug, 'slug')
    if request.method == 'POST':

        # Check whether a next url is valid or not
        adminApi.can_req_parameters_access(request, 'none', ['next'], 'POST')

        form = CourseEditForm(request.POST, instance=course)
        if form.is_valid():
            updated_course = form.save()
            if updated_course:
                messages.success(request, 'Success! {0} {1} {2} {3} updated'.format(updated_course.code.name, updated_course.number.name, updated_course.section.name, updated_course.term.code))
                return HttpResponseRedirect(request.POST.get('next'))
            else:
                messages.error(request, 'An error occurred while editing a course. Please contact administrators or try it again.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return HttpResponseRedirect(request.get_full_path())

    return render(request, 'administrators/courses/edit_course.html', {
        'loggedin_user': request.user,
        'course': course,
        'form': CourseEditForm(data=None, instance=course)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_course(request):
    ''' Delete a course '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        # Check whether a next url is valid or not
        adminApi.can_req_parameters_access(request, 'none', ['next'], 'POST')

        course_id = request.POST.get('course')
        deleted_course = adminApi.delete_course(course_id)
        if deleted_course:
            messages.success(request, 'Success! {0} {1} {2} {3} deleted'.format(deleted_course.code.name, deleted_course.number.name, deleted_course.section.name, deleted_course.term.code))
        else:
            messages.error(request, 'An error occurred while deleting a course. Please contact administrators or try it again.')

        return HttpResponseRedirect(request.POST.get('next'))

    return redirect("administrators:all_courses")


# ------------- Preparation -------------

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def preparation(request):
    request = userApi.has_admin_access(request)

    return render(request, 'administrators/preparation/preparation.html', {
        'loggedin_user': request.user
    })

# Terms
@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def terms(request):
    ''' Display all terms and create a term '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        form = TermForm(request.POST)
        if form.is_valid():
            term = form.save()
            if term:
                messages.success(request, 'Success! {0} ({1}) created'.format(term.name, term.code))
                return redirect('administrators:terms')
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

    return render(request, 'administrators/preparation/terms.html', {
        'loggedin_user': request.user,
        'terms': adminApi.get_terms(),
        'form': TermForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_term(request, term_id):
    ''' Edit a term '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        term = adminApi.get_term(term_id)
        form = TermForm(request.POST, instance=term)
        if form.is_valid():
            updated_term = form.save()
            if updated_term:
                messages.success(request, 'Success! {0} ({1}) updated'.format(updated_term.name, updated_term.code))
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))
    return redirect("administrators:terms")

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_term(request):
    ''' Delete a term '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        term_id = request.POST.get('term')
        result = adminApi.delete_term(term_id)
        if result['status'] == True:
            messages.success(request, 'Success! {0} ({1}) deleted'.format(result['term'].name, result['term'].code))
        else:
            messages.error(request, 'An error occurred. {0}'.format(result['error']))
    return redirect("administrators:terms")

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def course_codes(request):
    ''' Display all course codes and create a course code '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        form = CourseCodeForm(request.POST)
        if form.is_valid():
            course_code = form.save()
            if course_code:
                messages.success(request, 'Success! {0} created'.format(course_code.name))
                return redirect('administrators:course_codes')
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

    return render(request, 'administrators/preparation/course_codes.html', {
        'loggedin_user': request.user,
        'course_codes': adminApi.get_course_codes(),
        'form': CourseCodeForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_course_code(request, course_code_id):
    ''' Edit a course code '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        course_code = adminApi.get_course_code(course_code_id)
        form = CourseCodeForm(request.POST, instance=course_code)
        if form.is_valid():
            updated_course_code = form.save()
            if updated_course_code:
                messages.success(request, 'Success! {0} updated'.format(updated_course_code.name))
            else:
                messages.error(request, 'An error occurred.')
        else:
            messages.error(request, 'An error occurred.')
    return redirect('administrators:course_codes')

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_course_code(request):
    ''' Delete a course code '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        course_code_id = request.POST.get('course_code')
        result = adminApi.delete_course_code(course_code_id)
        if result['status'] == True:
            messages.success(request, 'Success! {0} deleted'.format(result['course_code'].name))
        else:
            messages.error(request, 'An error occurred. {0}'.format(result['error']))
    return redirect('administrators:course_codes')


# Course Number


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def course_numbers(request):
    ''' display course numbers'''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        form = CourseNumberForm(request.POST)
        if form.is_valid():
            course_number = form.save()
            if course_number:
                messages.success(request, 'Success! {0} created'.format(course_number.name))
                return redirect('administrators:course_numbers')
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

    return render(request, 'administrators/preparation/course_numbers.html', {
        'loggedin_user': request.user,
        'course_numbers': adminApi.get_course_numbers(),
        'form': CourseNumberForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_course_number(request, course_number_id):
    ''' edit a course number '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        course_number = adminApi.get_course_number(course_number_id)
        form = CourseNumberForm(request.POST, instance=course_number)
        if form.is_valid():
            updated_course_number = form.save()
            if updated_course_number:
                messages.success(request, 'Success! {0} updated'.format(updated_course_number.name))
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

    return redirect('administrators:course_numbers')

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_course_number(request):
    ''' delete a course number '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        course_number_id = request.POST.get('course_number')
        result = adminApi.delete_course_number(course_number_id)
        if result['status'] == True:
            messages.success(request, 'Success! {0} deleted'.format(result['course_number'].name))
        else:
            messages.error(request, 'An error occurred. {0}'.format(result['error']))
    return redirect('administrators:course_numbers')

# Course Section

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def course_sections(request):
    ''' display course sections '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        form = CourseSectionForm(request.POST)
        if form.is_valid():
            course_section = form.save()
            if course_section:
                messages.success(request, 'Success! {0} created'.format(course_section.name))
                return redirect('administrators:course_sections')
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

    return render(request, 'administrators/preparation/course_sections.html', {
        'loggedin_user': request.user,
        'course_sections': adminApi.get_course_sections(),
        'form': CourseSectionForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_course_section(request, course_section_id):
    ''' edit a course section '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        course_section = adminApi.get_course_section(course_section_id)
        form = CourseSectionForm(request.POST, instance=course_section)
        if form.is_valid():
            updated_course_section = form.save()
            if updated_course_section:
                messages.success(request, 'Success! {0} updated'.format(updated_course_section.name))
            else:
                messages.error(request, 'An error occurred.')
        else:
            messages.error(request, 'An error occurred.')
    return redirect('administrators:course_sections')

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_course_section(request):
    ''' delete a course section '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        course_section_id = request.POST.get('course_section')
        result = adminApi.delete_course_section(course_section_id)
        if result['status'] == True:
            messages.success(request, 'Success! {0} deleted'.format(result['course_section'].name))
        else:
            messages.error(request, 'An error occurred. {0}'.format(result['error']))
    return redirect('administrators:course_sections')


# Roles

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def roles(request):
    ''' Display all roles and create a role '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        form = RoleForm(request.POST)
        if form.is_valid():
            role = form.save()
            if role:
                messages.success(request, 'Success! {0} created'.format(role.name))
                return redirect('administrators:roles')
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

    return render(request, 'administrators/preparation/roles.html', {
        'loggedin_user': request.user,
        'roles': userApi.get_roles(),
        'form': RoleForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_role(request, slug):
    ''' Edit a role '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        role = userApi.get_role_by_slug(slug)
        form = RoleForm(request.POST, instance=role)
        if form.is_valid():
            updated_role = form.save()
            if updated_role:
                messages.success(request, 'Success! {0} updated'.format(updated_role.name))
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))
    return redirect("administrators:roles")

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_role(request):
    ''' Delete a role '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        role_id = request.POST.get('role')
        deleted_role = userApi.delete_role(role_id)
        if deleted_role:
            messages.success(request, 'Success! {0} deleted'.format(deleted_role.name))
        else:
            messages.error(request, 'An error occurred.')
    return redirect("administrators:roles")


# Statuses

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def statuses(request):
    ''' Display all statuses and create a status '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        form = StatusForm(request.POST)
        if form.is_valid():
            status = form.save()
            if status:
                messages.success(request, 'Success! {0} created'.format(status.name))
                return redirect('administrators:statuses')
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

    return render(request, 'administrators/preparation/statuses.html', {
        'loggedin_user': request.user,
        'statuses': userApi.get_statuses(),
        'form': StatusForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_status(request, slug):
    ''' Edit a status '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        status = userApi.get_status_by_slug(slug)
        form = StatusForm(request.POST, instance=status)
        if form.is_valid():
            updated_status = form.save()
            if updated_status:
                messages.success(request, 'Success! {0} updated'.format(updated_status.name))
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))
    return redirect("administrators:statuses")

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_status(request):
    ''' Delete a status '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        status_id = request.POST.get('status')
        deleted_status = userApi.delete_status(status_id)
        if deleted_status:
            messages.success(request, 'Success! {0} deleted'.format(deleted_status.name))
        else:
            messages.error(request, 'An error occurred.')
    return redirect("administrators:statuses")


# Programs


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def programs(request):
    ''' Display all programs and create a program '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        form = ProgramForm(request.POST)
        if form.is_valid():
            program = form.save()
            if program:
                messages.success(request, 'Success! {0} created'.format(program.name))
                return redirect('administrators:programs')
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

    return render(request, 'administrators/preparation/programs.html', {
        'loggedin_user': request.user,
        'programs': userApi.get_programs(),
        'form': ProgramForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_program(request, slug):
    ''' Edit a program '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        program = userApi.get_program_by_slug(slug)
        form = ProgramForm(request.POST, instance=program)
        if form.is_valid():
            updated_program = form.save()
            if updated_program:
                messages.success(request, 'Success! {0} updated'.format(updated_program.name))
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))
    return redirect("administrators:programs")

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_program(request):
    ''' Delete a program '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        program_id = request.POST.get('program')
        deleted_program = userApi.delete_program(program_id)
        if deleted_program:
            messages.success(request, 'Success! {0} deleted'.format(deleted_program.name))
        else:
            messages.error(request, 'An error occurred.')
    return redirect("administrators:programs")


# Degrees

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def degrees(request):
    ''' Display all degrees and create a degree '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        form = DegreeForm(request.POST)
        if form.is_valid():
            degree = form.save()
            if degree:
                messages.success(request, 'Success! {0} created'.format(degree.name))
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return redirect('administrators:degrees')

    return render(request, 'administrators/preparation/degrees.html', {
        'loggedin_user': request.user,
        'degrees': userApi.get_degrees(),
        'form': DegreeForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_degree(request, slug):
    ''' Edit a degree '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        degree = userApi.get_degree_by_slug(slug)
        form = DegreeForm(request.POST, instance=degree)
        if form.is_valid():
            updated_degree = form.save()
            if updated_degree:
                messages.success(request, 'Success! {0} updated'.format(updated_degree.name))
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

    return redirect("administrators:degrees")

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_degree(request):
    ''' Delete a degree '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        degree_id = request.POST.get('degree')
        deleted_degree = userApi.delete_degree(degree_id)
        if deleted_degree:
            messages.success(request, 'Success! {0} deleted'.format(deleted_degree.name))
        else:
            messages.error(request, 'An error occurred.')
    return redirect("administrators:degrees")


# Trainings

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def trainings(request):
    ''' Display all trainings and create a training '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        form = TrainingForm(request.POST)
        if form.is_valid():
            training = form.save()
            if training:
                messages.success(request, 'Success! {0} created'.format(training.name))
                return redirect('administrators:trainings')
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

    return render(request, 'administrators/preparation/trainings.html', {
        'loggedin_user': request.user,
        'trainings': userApi.get_trainings(),
        'form': TrainingForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_training(request, slug):
    ''' Edit a training '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        training = userApi.get_training_by_slug(slug)
        form = TrainingForm(request.POST, instance=training)
        if form.is_valid():
            updated_training = form.save()
            if updated_training:
                messages.success(request, 'Success! {0} updated'.format(updated_training.name))
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))
    return redirect("administrators:trainings")

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_training(request):
    ''' Delete a training '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        training_id = request.POST.get('training')
        deleted_training = userApi.delete_training(training_id)
        if deleted_training:
            messages.success(request, 'Success! {0} deleted'.format(deleted_training.name))
        else:
            messages.error(request, 'An error occurred.')
    return redirect("administrators:trainings")


# classification


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def classifications(request):
    ''' Display all classifications and create a classification '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        form = ClassificationForm(request.POST)
        if form.is_valid():
            classification = form.save()
            if classification:
                messages.success(request, 'Success! {0} {1} created'.format(classification.year, classification.name))
                return redirect('administrators:classifications')
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

    return render(request, 'administrators/preparation/classifications.html', {
        'loggedin_user': request.user,
        'classifications': adminApi.get_classifications('all'),
        'form': ClassificationForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_classification(request, slug):
    ''' Edit a classification '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        classification = adminApi.get_classification_by_slug(slug)
        form = ClassificationForm(request.POST, instance=classification)
        if form.is_valid():
            updated_classification = form.save()
            if updated_classification:
                messages.success(request, 'Success! {0} {1} updated'.format(updated_classification.year, updated_classification.name))
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

    return redirect("administrators:classifications")

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_classification(request):
    ''' Delete a classification '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        classification_id = request.POST.get('classification')
        deleted_classification = adminApi.delete_classification(classification_id)
        if deleted_classification:
            messages.success(request, 'Success! {0} deleted'.format(deleted_classification.name))
        else:
            messages.error(request, 'An error occurred.')
    return redirect("administrators:classifications")


# roles

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def roles(request):
    ''' Display all roles and create a role '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        form = RoleForm(request.POST)
        if form.is_valid():
            role = form.save()
            if role:
                messages.success(request, 'Success! {0} created'.format(role.name))
                return redirect('administrators:roles')
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

    return render(request, 'administrators/hr/roles.html', {
        'loggedin_user': request.user,
        'roles': userApi.get_roles(),
        'form': RoleForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_role(request, slug):
    ''' Edit a role '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        role = userApi.get_role_by_slug(slug)
        form = RoleForm(request.POST, instance=role)
        if form.is_valid():
            updated_role = form.save()
            if updated_role:
                messages.success(request, 'Success! {0} updated'.format(updated_role.name))
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))
    return redirect("administrators:roles")

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_role(request):
    ''' Delete a role '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        role_id = request.POST.get('role')
        deleted_role = userApi.delete_role(role_id)
        if deleted_role:
            messages.success(request, 'Success! {0} deleted'.format(deleted_role.name))
        else:
            messages.error(request, 'An error occurred.')
    return redirect("administrators:roles")


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def admin_emails(request):
    ''' Display all roles and create a role '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        form = AdminEmailForm(request.POST)
        if form.is_valid():
            admin_email = form.save()
            if admin_email:
                messages.success(request, 'Success! {0} created'.format(admin_email.type))
                return redirect('administrators:admin_emails')
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

    return render(request, 'administrators/preparation/admin_emails.html', {
        'loggedin_user': request.user,
        'admin_emails': adminApi.get_admin_emails(),
        'form': AdminEmailForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_admin_email(request, slug):
    ''' Edit a admin_email '''
    request = userApi.has_admin_access(request)

    admin_email = adminApi.get_admin_email_by_slug(slug)
    if request.method == 'POST':
        form = AdminEmailForm(request.POST, instance=admin_email)
        if form.is_valid():
            updated_admin_email = form.save(commit=False)
            updated_admin_email.updated_at = datetime.now()
            updated_admin_email.save()
            if updated_admin_email:
                messages.success(request, 'Success! {0} updated'.format(updated_admin_email.type))
                return redirect("administrators:admin_emails")
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return HttpResponseRedirect( reverse('administrators:edit_admin_email', args=[slug]) )

    return render(request, 'administrators/preparation/edit_admin_email.html', {
        'loggedin_user': request.user,
        'form': AdminEmailForm(data=None, instance=admin_email)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_admin_email(request):
    ''' Delete a admin_email '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        admin_email_id = request.POST.get('admin_email')
        deleted_admin_email = adminApi.delete_admin_email(admin_email_id)
        if deleted_admin_email:
            messages.success(request, 'Success! {0} deleted'.format(deleted_admin_email.type))
        else:
            messages.error(request, 'An error occurred.')
    return redirect("administrators:admin_emails")


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def landing_pages(request):
    ''' Edit a landing page '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        form = LandingPageForm(request.POST)
        if form.is_valid():
            landing_page = form.save()
            if landing_page:
                messages.success(request, 'Success! New landing page (ID: {0}) created.'.format(landing_page.id))
                return redirect('administrators:landing_pages')
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

    return render(request, 'administrators/preparation/landing_pages.html', {
        'loggedin_user': request.user,
        'landing_pages': adminApi.get_landing_pages(),
        'form': LandingPageForm()
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_landing_page(request, landing_page_id):
    ''' Edit a admin_email '''
    request = userApi.has_admin_access(request)

    landing_page = adminApi.get_landing_page(landing_page_id)
    if request.method == 'POST':
        form = LandingPageForm(request.POST, instance=landing_page)
        if form.is_valid():
            updated_landing_page = form.save(commit=False)
            updated_landing_page.updated_at = datetime.now()
            updated_landing_page.save()
            if updated_landing_page:
                messages.success(request, 'Success! Landing Page (ID: {0}) updated'.format(updated_landing_page.id))
                return redirect("administrators:landing_pages")
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return HttpResponseRedirect( reverse('administrators:edit_landing_page', args=[landing_page_id]) )

    return render(request, 'administrators/preparation/edit_landing_page.html', {
        'loggedin_user': request.user,
        'form': LandingPageForm(data=None, instance=landing_page)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_landing_page(request):
    ''' Delete a landing page '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        landing_page_id = request.POST.get('landing_page')
        deleted_landing_page = adminApi.delete_landing_page(landing_page_id)
        if deleted_landing_page:
            messages.success(request, 'Success! Landing Page {0} deleted'.format(deleted_landing_page.title))
        else:
            messages.error(request, 'An error occurred.')
    return redirect("administrators:landing_pages")
