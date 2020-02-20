from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_control

from django.db.models import Q
from django.views.static import serve
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from administrators.models import Session, Job, Application, ApplicationStatus, Course
from administrators.forms import *
from administrators import api as adminApi

from django.contrib.auth.models import User
from users.forms import *
from users import api as userApi

from datetime import datetime

from django.contrib.auth.models import User


APP_MEMU = ['dashboard', 'all', 'selected', 'offered', 'accepted', 'declined', 'terminated']
SESSION_PATH = ['current', 'archived']
JOB_PATH = ['prepare', 'progress'] + APP_MEMU
APP_PATH = APP_MEMU + ['emails' ]
USER_PATH = ['instructor', 'student', 'users', 'destroy'] + APP_MEMU
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
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user) and 'HR' not in request.user.roles:
        raise PermissionDenied

    context = { 'loggedin_user': request.user }
    if 'Admin' in request.user.roles or 'Superadmin' in request.user.roles:
        sessions = adminApi.get_sessions()
        context['current_sessions'] = sessions.filter(is_archived=False)
        context['archived_sessions'] = sessions.filter(is_archived=True)
        context['apps'] = adminApi.get_applications()
        context['instructors'] = userApi.get_users_by_role(Role.INSTRUCTOR)
        context['students'] = userApi.get_users_by_role(Role.STUDENT)
        context['users'] = userApi.get_users()

    elif 'HR' in request.user.roles:
        apps = adminApi.get_applications()
        context['accepted_apps'] = apps.filter(applicationstatus__assigned=ApplicationStatus.ACCEPTED).order_by('-id').distinct()

    return render(request, 'administrators/index.html', context)

# ------------- Sessions -------------


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def create_session(request):
    ''' Create a session '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

    year_q = request.GET.get('year')
    term_q = request.GET.get('term')

    session_list = adminApi.get_sessions()
    if bool(year_q):
        session_list = session_list.filter(year__iexact=year_q)
    if bool(term_q):
        session_list = session_list.filter(term__code__iexact=term_q)

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
        'form': SessionForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def archived_sessions(request):
    ''' Display all information of sessions and create a session '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

    year_q = request.GET.get('year')
    term_q = request.GET.get('term')

    session_list = adminApi.get_sessions()
    if bool(year_q):
        session_list = session_list.filter(year__iexact=year_q)
    if bool(term_q):
        session_list = session_list.filter(term__code__iexact=term_q)

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
        'form': SessionForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_session(request, session_slug, path):
    ''' Display session details '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied
    if path not in SESSION_PATH: raise Http404

    return render(request, 'administrators/sessions/show_session.html', {
        'loggedin_user': request.user,
        'session': adminApi.get_session(session_slug, 'slug'),
        'path': path
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_session(request, session_slug, path):
    ''' Edit a session '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied
    if path not in SESSION_PATH: raise Http404

    session = adminApi.get_session(session_slug, 'slug')
    if request.method == 'POST':
        form = SessionConfirmationForm(request.POST, instance=session)
        if form.is_valid():
            data = form.cleaned_data
            courses = data['courses']

            if len(courses) == 0:
                messages.error(request, 'An error occurred. Please select courses in this session.')
                return HttpResponseRedirect( reverse('administrators:edit_session', args=[session_slug, path]) )

            updated_session = form.save(commit=False)
            updated_session.updated_at = datetime.now()

            if data['is_archived']:
                updated_session.is_visible = False

            updated_session.save()

            if updated_session:
                updated_jobs = adminApi.update_session_jobs(session, courses)
                if updated_jobs:
                    messages.success(request, 'Success! {0} {1} {2} updated'.format(session.year, session.term.code, session.title))
                    if data['is_archived']:
                        return redirect('administrators:archived_sessions')
                    else:
                        return redirect('administrators:current_sessions')
                else:
                    messages.error(request, 'An error occurred while updating courses in a session.')
            else:
                messages.error(request, 'An error occurred while updating a session.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return HttpResponseRedirect( reverse('administrators:edit_session', args=[session_slug, path]) )

    return render(request, 'administrators/sessions/edit_session.html', {
        'loggedin_user': request.user,
        'session': session,
        'form': SessionConfirmationForm(data=None, instance=session, initial={
            'courses': [ job.course for job in session.job_set.all() ],
            'term': session.term
        }),
        'path': path
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_session(request, path):
    ''' Delete a Session '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

    if request.method == 'POST':
        session_id = request.POST.get('session')
        deleted_session = adminApi.delete_session(session_id)
        if deleted_session:
            messages.success(request, 'Success! {0} {1} {2} deleted'.format(deleted_session.year, deleted_session.term.code, deleted_session.title))
        else:
            messages.error(request, 'An error occurred. Failed to delete {0} {1} {2}'.format(deleted_session.year, deleted_session.term.code, deleted_session.title))

    return redirect('administrators:{0}_sessions'.format(path))


# ------------- Jobs -------------



@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def show_job(request, session_slug, job_slug, path):
    ''' Display job details '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user) and 'HR' not in request.user.roles:
        raise PermissionDenied
    if path not in JOB_PATH: raise Http404

    return render(request, 'administrators/jobs/show_job.html', {
        'loggedin_user': request.user,
        'job': adminApi.get_job_by_session_slug_job_slug(session_slug, job_slug),
        'path': path
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def prepare_jobs(request):
    ''' Display preparing jobs '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

    year_q = request.GET.get('year')
    term_q = request.GET.get('term')
    code_q = request.GET.get('code')
    number_q = request.GET.get('number')
    section_q = request.GET.get('section')
    instructor_first_name_q = request.GET.get('instructor_first_name')
    instructor_last_name_q = request.GET.get('instructor_last_name')

    job_list = adminApi.get_jobs()
    if bool(year_q):
        job_list = job_list.filter(session__year__iexact=year_q)
    if bool(term_q):
        job_list = job_list.filter(session__term__code__iexact=term_q)
    if bool(code_q):
        job_list = job_list.filter(course__code__name__iexact=code_q)
    if bool(number_q):
        job_list = job_list.filter(course__number__name__iexact=number_q)
    if bool(section_q):
        job_list = job_list.filter(course__section__name__iexact=section_q)
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
        'total_jobs': len(job_list)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def progress_jobs(request):
    ''' See jobs in progress '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

    year_q = request.GET.get('year')
    term_q = request.GET.get('term')
    code_q = request.GET.get('code')
    number_q = request.GET.get('number')
    section_q = request.GET.get('section')

    job_list = adminApi.get_jobs()
    if bool(year_q):
        job_list = job_list.filter(session__year__iexact=year_q)
    if bool(term_q):
        job_list = job_list.filter(session__term__code__iexact=term_q)
    if bool(code_q):
        job_list = job_list.filter(course__code__name__iexact=code_q)
    if bool(number_q):
        job_list = job_list.filter(course__number__name__iexact=number_q)
    if bool(section_q):
        job_list = job_list.filter(course__section__name__iexact=section_q)

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
        'total_jobs': len(job_list)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def instructor_jobs(request):
    ''' Display jobs by instructor '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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

    user_list = user_list.filter(profile__roles__name=Role.INSTRUCTOR)

    page = request.GET.get('page', 1)
    paginator = Paginator(user_list, settings.PAGE_SIZE)

    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)

    return render(request, 'administrators/jobs/instructor_jobs.html', {
        'loggedin_user': request.user,
        'users': users,
        'total_users': len(user_list)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def student_jobs(request):
    ''' Display jobs by student '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
        'total_users': len(user_list)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_job_applications(request, session_slug, job_slug):
    ''' Display a job's applications '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

    job = adminApi.get_job_by_session_slug_job_slug(session_slug, job_slug)
    return render(request, 'administrators/jobs/show_job_applications.html', {
        'loggedin_user': request.user,
        'job': adminApi.add_job_with_applications_statistics(job),
        'app_status': APP_STATUS
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def instructor_jobs_details(request, username):
    ''' Display jobs that an instructor has '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

    user = userApi.get_user(username, 'username')
    return render(request, 'administrators/jobs/instructor_jobs_details.html', {
        'loggedin_user': request.user,
        'user': adminApi.add_total_applicants(user)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def student_jobs_details(request, username, tab):
    ''' Display jobs that an student has '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

    user = userApi.get_user(username, 'username')
    apps = user.application_set.all()
    return render(request, 'administrators/jobs/student_jobs_details.html', {
        'loggedin_user': request.user,
        'user': user,
        'apps': adminApi.add_app_info_into_applications(apps, ['offered', 'accepted']),
        'total_assigned_hours': adminApi.get_total_assigned_hours(apps, ['offered', 'accepted']),
        'current_tab': tab,
        'app_status': APP_STATUS
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_job(request, session_slug, job_slug):
    ''' Edit a job '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

    job = adminApi.get_job_by_session_slug_job_slug(session_slug, job_slug)
    job_instructors = job.instructors.all()
    if request.method == 'POST':
        form = AdminJobForm(request.POST, instance=job)
        if form.is_valid():
            data = form.cleaned_data
            new_instructors = data.get('instructors')

            updated_job = form.save(commit=False)
            updated_job.updated_at = datetime.now()
            updated_job.save()
            if updated_job:
                updated = adminApi.update_job_instructors(updated_job, job_instructors, new_instructors)
                if updated:
                    messages.success(request, 'Success! {0} {1} {2} {3} {4} updated'.format(updated_job.session.year, updated_job.session.term.code, updated_job.course.code.name, updated_job.course.number.name, updated_job.course.section.name))
                    return redirect('administrators:prepare_jobs')
                else:
                    messages.error(request, 'An error occurred while updateing instructors of a job.')
            else:
                messages.error(request, 'An error occurred while updating a job.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return HttpResponseRedirect(reverse('administrators:edit_job', args=[session_slug, job_slug]))

    return render(request, 'administrators/jobs/edit_job.html', {
        'loggedin_user': request.user,
        'job': job,
        'form': AdminJobForm(data=None, instance=job, initial={
            'instructors': job_instructors
        })
    })




# Applications


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_application(request, app_slug, path):
    ''' Display an application details '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user) and 'HR' not in request.user.roles:
        raise PermissionDenied

    if path not in APP_PATH: raise Http404

    return render(request, 'administrators/applications/show_application.html', {
        'loggedin_user': request.user,
        'app': adminApi.get_application(app_slug, 'slug'),
        'path': path
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def applications_dashboard(request):
    ''' Display a dashboard to take a look at updates '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

    year_q = request.GET.get('year')
    term_q = request.GET.get('term')
    code_q = request.GET.get('code')
    number_q = request.GET.get('number')
    section_q = request.GET.get('section')
    first_name_q = request.GET.get('first_name')
    last_name_q = request.GET.get('last_name')

    status_list = adminApi.get_application_statuses()
    if bool(year_q):
        status_list = status_list.filter(application__job__session__year__iexact=year_q)
    if bool(term_q):
        status_list = status_list.filter(application__job__session__term__code__iexact=term_q)
    if bool(code_q):
        status_list = status_list.filter(application__job__course__code__name__iexact=code_q)
    if bool(number_q):
        status_list = status_list.filter(application__job__course__number__name__iexact=number_q)
    if bool(section_q):
        status_list = status_list.filter(application__job__course__section__name__iexact=section_q)
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
        'app_status': APP_STATUS
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def all_applications(request):
    ''' Display all applications '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

    year_q = request.GET.get('year')
    term_q = request.GET.get('term')
    code_q = request.GET.get('code')
    number_q = request.GET.get('number')
    section_q = request.GET.get('section')
    first_name_q = request.GET.get('first_name')
    last_name_q = request.GET.get('last_name')

    app_list = adminApi.get_applications()
    if bool(year_q):
        app_list = app_list.filter(job__session__year__iexact=year_q)
    if bool(term_q):
        app_list = app_list.filter(job__session__term__code__iexact=term_q)
    if bool(code_q):
        app_list = app_list.filter(job__course__code__name__iexact=code_q)
    if bool(number_q):
        app_list = app_list.filter(job__course__number__name__iexact=number_q)
    if bool(section_q):
        app_list = app_list.filter(job__course__section__name__iexact=section_q)
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
        'total_apps': len(app_list)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def selected_applications(request):
    ''' Display applications selected by instructors '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

    year_q = request.GET.get('year')
    term_q = request.GET.get('term')
    code_q = request.GET.get('code')
    number_q = request.GET.get('number')
    section_q = request.GET.get('section')
    first_name_q = request.GET.get('first_name')
    last_name_q = request.GET.get('last_name')

    app_list = adminApi.get_applications()
    if bool(year_q):
        app_list = app_list.filter(job__session__year__iexact=year_q)
    if bool(term_q):
        app_list = app_list.filter(job__session__term__code__iexact=term_q)
    if bool(code_q):
        app_list = app_list.filter(job__course__code__name__iexact=code_q)
    if bool(number_q):
        app_list = app_list.filter(job__course__number__name__iexact=number_q)
    if bool(section_q):
        app_list = app_list.filter(job__course__section__name__iexact=section_q)
    if bool(first_name_q):
        app_list = app_list.filter(applicant__first_name__icontains=first_name_q)
    if bool(last_name_q):
        app_list = app_list.filter(applicant__last_name__icontains=last_name_q)

    app_list = app_list.filter(applicationstatus__assigned=ApplicationStatus.SELECTED).order_by('-id').distinct()
    app_list = adminApi.add_app_info_into_applications(app_list, ['resume', 'selected', 'offered'])

    page = request.GET.get('page', 1)
    paginator = Paginator(app_list, settings.PAGE_SIZE)

    try:
        apps = paginator.page(page)
    except PageNotAnInteger:
        apps = paginator.page(1)
    except EmptyPage:
        apps = paginator.page(paginator.num_pages)

    return render(request, 'administrators/applications/selected_applications.html', {
        'loggedin_user': request.user,
        'apps': apps,
        'total_apps': len(app_list),
        'admin_application_form': AdminApplicationForm(),
        'status_form': ApplicationStatusForm(initial={ 'assigned': ApplicationStatus.OFFERED }),
        'classification_choices': adminApi.get_classifications(),
        'app_status': APP_STATUS,
        'special_programs': {
            'mfre': '',
            'mlws': '',
            'mfs': ''
        }
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def offer_job(request, session_slug, job_slug):
    ''' Admin can offer a job to each job '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

    if request.method == 'POST':
        if 'classification' not in request.POST.keys() or len(request.POST.get('classification')) == 0:
            messages.error(request, 'An error occurred. Please select classification, then try again.')
            return redirect('administrators:selected_applications')

        assigned_hours = request.POST.get('assigned_hours')

        if adminApi.is_valid_float(assigned_hours) == False:
            messages.error(request, 'An error occurred. Please check assigned hours. Assigned hours must be numerival value only.')
            return redirect('administrators:selected_applications')

        assigned_hours = float(assigned_hours)

        if assigned_hours < 0.0:
            messages.error(request, 'An error occurred. Please check assigned hours. Assigned hours must be greater than 0.')
            return redirect('administrators:selected_applications')

        job = adminApi.get_job_by_session_slug_job_slug(session_slug, job_slug)
        if assigned_hours > float(job.assigned_ta_hours):
            messages.error(request, 'An error occurred. Please you cannot assign {0} hours Total Assigned TA Hours is {1}, then try again.'.format(assigned_hours, job.assigned_ta_hours))
            return redirect('administrators:selected_applications')

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
                return HttpResponseRedirect( reverse('administrators:edit_user', args=[username]) )

            applicant = userApi.get_user(request.POST.get('applicant'))
            messages.success(request, 'Success! You offered this user ({0} {1}) {2} hours for this job ({3} {4} - {5} {6} {7})'.format(applicant.first_name, applicant.last_name, assigned_hours, job.session.year, job.session.term.code, job.course.code.name, job.course.number.name, job.course.section.name))
        else:
            errors = []

            admin_app_errors = admin_app_form.errors.get_json_data()
            app_status_errors = app_status_form.errors.get_json_data()

            if admin_app_errors: errors.append( userApi.get_error_messages(admin_app_errors) )
            if app_status_errors: errors.append( userApi.get_error_messages(app_status_errors) )

            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

    return redirect('administrators:selected_applications')


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def offered_applications(request):
    ''' Display applications offered by admins '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

    year_q = request.GET.get('year')
    term_q = request.GET.get('term')
    code_q = request.GET.get('code')
    number_q = request.GET.get('number')
    section_q = request.GET.get('section')
    first_name_q = request.GET.get('first_name')
    last_name_q = request.GET.get('last_name')

    app_list = adminApi.get_applications()
    if bool(year_q):
        app_list = app_list.filter(job__session__year__iexact=year_q)
    if bool(term_q):
        app_list = app_list.filter(job__session__term__code__iexact=term_q)
    if bool(code_q):
        app_list = app_list.filter(job__course__code__name__iexact=code_q)
    if bool(number_q):
        app_list = app_list.filter(job__course__number__name__iexact=number_q)
    if bool(section_q):
        app_list = app_list.filter(job__course__section__name__iexact=section_q)
    if bool(first_name_q):
        app_list = app_list.filter(applicant__first_name__icontains=first_name_q)
    if bool(last_name_q):
        app_list = app_list.filter(applicant__last_name__icontains=last_name_q)

    app_list = app_list.filter(applicationstatus__assigned=ApplicationStatus.OFFERED).order_by('-id').distinct()
    app_list = adminApi.add_app_info_into_applications(app_list, ['offered'])

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
        'admin_emails': adminApi.get_admin_emails()
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def accepted_applications(request):
    ''' Display applications accepted by students '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user) and 'HR' not in request.user.roles:
        raise PermissionDenied

    if request.method == 'POST':
        admin_docs = adminApi.get_admin_docs(request.POST.get('application'))
        form = AdminDocumentsForm(request.POST, instance=admin_docs)
        if form.is_valid():
            saved_admin_docs = form.save()
            if saved_admin_docs:
                messages.success(request, 'Success! Admin Documents of {0} updated (Application ID: {1})'.format( saved_admin_docs.application.applicant.get_full_name(), saved_admin_docs.application.id ))
            else:
                messages.error(request, 'An error occurred while saving admin docs.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return redirect('administrators:accepted_applications')

    else:
        year_q = request.GET.get('year')
        term_q = request.GET.get('term')
        code_q = request.GET.get('code')
        number_q = request.GET.get('number')
        section_q = request.GET.get('section')
        first_name_q = request.GET.get('first_name')
        last_name_q = request.GET.get('last_name')

        app_list = adminApi.get_applications()
        if bool(year_q):
            app_list = app_list.filter(job__session__year__iexact=year_q)
        if bool(term_q):
            app_list = app_list.filter(job__session__term__code__iexact=term_q)
        if bool(code_q):
            app_list = app_list.filter(job__course__code__name__iexact=code_q)
        if bool(number_q):
            app_list = app_list.filter(job__course__number__name__iexact=number_q)
        if bool(section_q):
            app_list = app_list.filter(job__course__section__name__iexact=section_q)
        if bool(first_name_q):
            app_list = app_list.filter(applicant__first_name__icontains=first_name_q)
        if bool(last_name_q):
            app_list = app_list.filter(applicant__last_name__icontains=last_name_q)

        app_list = app_list.filter(applicationstatus__assigned=ApplicationStatus.ACCEPTED).order_by('-id').distinct()

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
        'total_apps': len(app_list)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def declined_applications(request):
    ''' Display applications declined by students '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

    year_q = request.GET.get('year')
    term_q = request.GET.get('term')
    code_q = request.GET.get('code')
    number_q = request.GET.get('number')
    section_q = request.GET.get('section')
    first_name_q = request.GET.get('first_name')
    last_name_q = request.GET.get('last_name')

    app_list = adminApi.get_applications()
    if bool(year_q):
        app_list = app_list.filter(job__session__year__iexact=year_q)
    if bool(term_q):
        app_list = app_list.filter(job__session__term__code__iexact=term_q)
    if bool(code_q):
        app_list = app_list.filter(job__course__code__name__iexact=code_q)
    if bool(number_q):
        app_list = app_list.filter(job__course__number__name__iexact=number_q)
    if bool(section_q):
        app_list = app_list.filter(job__course__section__name__iexact=section_q)
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
        'admin_emails': adminApi.get_admin_emails()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def email_history(request):
    ''' Display all of email sent by admins to let them know job offers '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

    return render(request, 'administrators/applications/email_history.html', {
        'loggedin_user': request.user,
        'emails': adminApi.get_emails()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def send_reminder(request, email_id):
    ''' Send a reminder email '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

    email = None
    if request.method == 'POST':
        form = ReminderForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            sent_email = adminApi.send_and_create_email(data['application'], data['sender'], data['receiver'], data['title'], data['message'], data['type'])
            if sent_email:
                messages.success(request, 'Success! Email has sent to {0}'.format(data['receiver']))
                return redirect('administrators:email_history')
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))
    else:
        email = adminApi.get_email(email_id)

    return render(request, 'administrators/applications/send_reminder.html', {
        'loggedin_user': request.user,
        'email': email,
        'form': ReminderForm(data=None, instance=email, initial={
            'title': 'REMINDER: ' + email.title
        })
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def decline_reassign(request):
    ''' Decline and reassign a job offer with new assigned hours '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

    if request.method == 'POST':
        app = adminApi.get_application( request.POST.get('application') )

        if app.is_declined_reassigned: raise Http404

        old_assigned_hours = request.POST.get('old_assigned_hours')
        new_assigned_hours = request.POST.get('new_assigned_hours')

        if adminApi.is_valid_float(old_assigned_hours) == False:
            messages.error(request, 'An error occurred. Please contact administrators. Your old assigned hours must be numerival value only.')
            return redirect('administrators:accepted_applications')

        if adminApi.is_valid_float(new_assigned_hours) == False:
            messages.error(request, 'An error occurred. Please check assigned hours. Your new assigned hours must be numerival value only.')
            return redirect('administrators:accepted_applications')

        old_assigned_hours = float(old_assigned_hours)
        new_assigned_hours = float(new_assigned_hours)

        if new_assigned_hours < 0.0:
            messages.error(request, 'An error occurred. Please check assigned hours. Your new assigned hours must be greater than 0.')
            return redirect('administrators:accepted_applications')

        if old_assigned_hours == new_assigned_hours:
            messages.error(request, 'An error occurred. Please check assigned hours. Your new assigned hours are same as current assigned hours.')
            return redirect('administrators:accepted_applications')

        if new_assigned_hours == 0.0 or new_assigned_hours > float(app.job.assigned_ta_hours):
            messages.error(request, 'An error occurred. Please check assigned hours. Valid assigned hours are between 0.0 and {0}'.format(app.job.assigned_ta_hours))
            return redirect('administrators:accepted_applications')

        request.session['decline_reassign_form_data'] = request.POST
        return redirect('administrators:decline_reassign_confirmation')

    return redirect('administrators:accepted_applications')

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def decline_reassign_confirmation(request):
    ''' Display currnt status and new status for reassigning confirmation '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

    app = None
    old_assigned_hours = None
    new_assigned_hours = None
    new_ta_hours = None
    if request.method == 'POST':
        if request.POST.get('is_declined_reassigned') == None:
            messages.error(request, 'An error occurred. Please click the checkbox to decline and re-assign.')
            return redirect('administrators:decline_reassign_confirmation')

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
                return redirect('administrators:decline_reassign_confirmation')

            messages.success(request, 'Success! The status of Application (ID: {0}) updated'.format(app_id))
            return redirect('administrators:accepted_applications')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return redirect('administrators:decline_reassign_confirmation')

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
        'form': ReassignApplicationForm(data=None, instance=app)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET','POST'])
def terminate(request, app_slug):
    ''' Terminate an application, then students can can their accepted jobs '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

    app = adminApi.get_application(app_slug, 'slug')
    if app.is_terminated: raise Http404

    if request.method == 'POST':
        if request.POST.get('is_terminated') == None:
            messages.error(request, 'An error occurred. Please click the checkbox to terminate.')
            return HttpResponseRedirect( reverse('administrators:terminate', args=[app_slug]) )

        form = TerminateApplicationForm(request.POST, instance=app)
        if form.is_valid():
            terminated_app = form.save(commit=False)
            terminated_app.updated_at = datetime.now()
            terminated_app.save()
            if terminated_app:
                messages.success(request, 'Success! Application (ID: {0}) terminated.'.format(terminated_app.id))
                return redirect('administrators:accepted_applications')
            else:
                messages.error(request, 'An error occurred while termniating an application.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return HttpResponseRedirect( reverse('administrators:terminate_application', args=[app_slug]) )

    return render(request, 'administrators/applications/terminate.html', {
        'loggedin_user': request.user,
        'app': app,
        'form': TerminateApplicationForm(data=None, instance=app)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def terminated_applications(request):
    ''' Terminated applications '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

    year_q = request.GET.get('year')
    term_q = request.GET.get('term')
    code_q = request.GET.get('code')
    number_q = request.GET.get('number')
    section_q = request.GET.get('section')
    first_name_q = request.GET.get('first_name')
    last_name_q = request.GET.get('last_name')

    app_list = adminApi.get_terminated_applications()
    if bool(year_q):
        app_list = app_list.filter(job__session__year__iexact=year_q)
    if bool(term_q):
        app_list = app_list.filter(job__session__term__code__iexact=term_q)
    if bool(code_q):
        app_list = app_list.filter(job__course__code__name__iexact=code_q)
    if bool(number_q):
        app_list = app_list.filter(job__course__number__name__iexact=number_q)
    if bool(section_q):
        app_list = app_list.filter(job__course__section__name__iexact=section_q)
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
        'admin_emails': adminApi.get_admin_emails()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def applications_send_email(request, path):
    ''' Send an email for applications '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

    if request.method == 'POST':
        applications = request.POST.getlist('application')
        if len(applications) > 0:
            type = request.POST.get('type')
            request.session['applications_form_data'] = { 'applications': applications, 'type': type }
            return HttpResponseRedirect( reverse('administrators:applications_send_email_confirmation', args=[path]) )
        else:
            messages.error(request, 'An error occurred. Please select applications, then try again.')

    return redirect('administrators:{0}_applications'.format(path))


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def applications_send_email_confirmation(request, path):
    ''' Display a list of email for offered applications '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
            form = EmailForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data

                count = 0
                for app in applications:
                    assigned_hours = None
                    if path == 'offered':
                        assigned_hours = app.offered.assigned_hours
                    elif path == 'declined':
                        assigned_hours = app.declined.assigned_hours
                    elif path == 'terminated':
                        assigned_hours = app.accepted.assigned_hours

                    name = app.applicant.first_name + ' ' + app.applicant.last_name
                    message = data['message'].format(
                        name,
                        app.job.session.year + ' ' + app.job.session.term.code,
                        app.job.course.code.name + ' ' + app.job.course.number.name + ' ' + app.job.course.section.name,
                        assigned_hours,
                        app.classification.name
                    )

                    # TODO: replace a receiver
                    receiver = '{0} <{1}>'.format(name, app.applicant.email)

                    email = adminApi.send_and_create_email(app, data['sender'], receiver, data['title'], message, data['type'])
                    if email: count += 1

                if count == len(applications):
                    messages.success(request, 'Success! Email has sent to {0}'.format( data['receiver'] ))
                else:
                    messages.error(request, 'An error occurred.')

                del request.session['applications_form_data']
                return redirect('administrators:{0}_applications'.format(path))
            else:
                errors = form.errors.get_json_data()
                messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

            return redirect('administrators:applications_send_email_confirmation')

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
        'path': path
    })



# HR


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def all_users(request):
    ''' Display all users'''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
        'total_users': len(user_list)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_user(request, username, path, tab):
    ''' Display an user's details '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user) and 'HR' not in request.user.roles:
        raise PermissionDenied
    if path not in USER_PATH: raise Http404

    user = userApi.get_user(username, 'username')
    user = userApi.add_resume(user)

    if tab == 'confidential':
        user = userApi.add_confidentiality_given_list(user, ['sin','study_permit'])
        user = userApi.add_personal_data_form(user)

    user.is_student = userApi.user_has_role(user ,'Student')
    return render(request, 'administrators/hr/show_user.html', {
        'loggedin_user': request.user,
        'user': user,
        'path': path,
        'current_tab': tab
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def create_user(request):
    ''' Create a user '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

    if request.method == 'POST':
        user_form = UserForm(request.POST)
        user_profile_form = UserProfileForm(request.POST)

        if user_form.is_valid() and user_profile_form.is_valid():
            user = user_form.save(commit=False)
            user.set_password(settings.USER_PASSWORD)
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
                'employee_number': request.POST.get('employee_number')
            }
            employee_number_form = EmployeeNumberEditForm(data, instance=confidentiality)

            if employee_number_form.is_valid() == False:
                employee_number_errors = employee_number_form.errors.get_json_data()
                messages.error(request, 'An error occurred while creating an User Form. {0}'.format(employee_number_errors))

            employee_number = employee_number_form.save()

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
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

    user = userApi.get_user(username, 'username')
    confidentiality = userApi.has_user_confidentiality_created(user)

    if request.method == 'POST':
        user_id = request.POST.get('user')
        employee_number = request.POST.get('employee_number')
        profile_roles = user.profile.roles.all()

        user_form = UserForm(request.POST, instance=user)
        user_profile_edit_form = UserProfileEditForm(request.POST, instance=user.profile)
        employee_number_form = EmployeeNumberEditForm(request.POST, instance=confidentiality)

        if user_form.is_valid() and user_profile_edit_form.is_valid() and employee_number_form.is_valid():
            updated_user = user_form.save()

            updated_profile = user_profile_edit_form.save(commit=False)
            updated_profile.updated_at = datetime.now()
            updated_profile.save()

            updated_employee_number = employee_number_form.save(commit=False)
            updated_employee_number.updated_at = datetime.now()
            updated_employee_number.employee_number = employee_number_form.cleaned_data['employee_number']
            updated_employee_number.save(update_fields=['employee_number'])

            errors = []

            if not updated_user: errors.append('An error occurred while updating an user form.')
            if not updated_profile: errors.append('An error occurred while updating a profile.')
            if not updated_employee_number: errors.append('An error occurred while updating an employee number.')

            updated = userApi.update_user_profile_roles(updated_profile, profile_roles, user_profile_edit_form.cleaned_data)
            if not updated: errors.append(request, 'An error occurred while updating profile roles.')

            if len(errors) > 0:
                messages.error(request, 'An error occurred while saving an User Form. {0}'.format( ' '.join(errors) ))
                return HttpResponseRedirect( reverse('administrators:edit_user', args=[username]) )

            messages.success(request, 'Success! User information of {0} (CWL: {1}) updated'.format(user.get_full_name(), user.username))
            return redirect('administrators:all_users')
        else:
            errors = []

            user_errors = user_form.errors.get_json_data()
            profile_errors = user_profile_edit_form.errors.get_json_data()
            confid_errors = employee_number_form.errors.get_json_data()

            if user_errors: errors.append( userApi.get_error_messages(user_errors) )
            if profile_errors: errors.append( userApi.get_error_messages(profile_errors) )
            if confid_errors: errors.append( userApi.get_error_messages(confid_errors) )

            messages.error(request, 'An error occurred while updating an User Form. {0}'.format( ' '.join(errors) ))

        return HttpResponseRedirect( reverse('administrators:edit_user', args=[username]) )


    return render(request, 'administrators/hr/edit_user.html', {
        'loggedin_user': request.user,
        'user': user,
        'roles': userApi.get_roles(),
        'user_form': UserForm(data=None, instance=user),
        'user_profile_form': UserProfileEditForm(data=None, instance=user.profile),
        'employee_number_form': EmployeeNumberEditForm(data=None, instance=confidentiality)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_user(request):
    ''' Delete a user '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

    if request.method == 'POST':
        user_id = request.POST.get('user')
        deleted_user = userApi.delete_user(user_id)
        if deleted_user:
            messages.success(request, 'Success! {0} {1} ({2}) deleted'.format(deleted_user.first_name, deleted_user.last_name, deleted_user.username))
        else:
            messages.error(request, 'An error occurred while deleting a user.')

    return redirect('administrators:all_users')

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def destroy_user_contents(request):
    ''' Destroy users who have no actions for 3 years '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
        users, target_date = userApi.get_users('destroy')

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
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

    term_q = request.GET.get('term')
    code_q = request.GET.get('code')
    number_q = request.GET.get('number')
    section_q = request.GET.get('section')
    course_name_q = request.GET.get('course_name')

    course_list = adminApi.get_courses()
    if bool(term_q):
        course_list = course_list.filter(term__code__iexact=term_q)
    if bool(code_q):
        course_list = course_list.filter(code__name__iexact=code_q)
    if bool(number_q):
        course_list = course_list.filter(number__name__iexact=number_q)
    if bool(section_q):
        course_list = course_list.filter(section__name__iexact=section_q)
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
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

    course = adminApi.get_course(course_slug, 'slug')
    if request.method == 'POST':
        form = CourseEditForm(request.POST, instance=course)
        if form.is_valid():
            updated_course = form.save()
            if updated_course:
                messages.success(request, 'Success! {0} {1} {2} {3} updated'.format(updated_course.code.name, updated_course.number.name, updated_course.section.name, updated_course.term.code))
                return redirect('administrators:all_courses')
            else:
                messages.error(request, 'An error occurred while editing a course. Please contact administrators or try it again.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return HttpResponseRedirect( reverse('administrators:edit_course', args=[course_slug]) )

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
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

    if request.method == 'POST':
        course_id = request.POST.get('course')
        deleted_course = adminApi.delete_course(course_id)
        if deleted_course:
            messages.success(request, 'Success! {0} {1} {2} {3} deleted'.format(deleted_course.code.name, deleted_course.number.name, deleted_course.section.name, deleted_course.term.code))
        else:
            messages.error(request, 'An error occurred while deleting a course. Please contact administrators or try it again.')

    return redirect("administrators:all_courses")




# ------------- Preparation -------------

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def preparation(request):
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

    return render(request, 'administrators/preparation/preparation.html', {
        'loggedin_user': request.user
    })

# Terms
@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def terms(request):
    ''' Display all terms and create a term '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
    ''' '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
    ''' '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
    ''' '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
    ''' '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
    ''' '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
    ''' '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
    ''' '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

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
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

    admin_emails = adminApi.get_admin_emails()
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
        'admin_emails': admin_emails,
        'form': AdminEmailForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_admin_email(request, slug):
    ''' Edit a admin_email '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

    admin_email = adminApi.get_admin_email_by_slug(slug)

    if request.method == 'POST':
        form = AdminEmailForm(request.POST, instance=admin_email)
        if form.is_valid():
            updated_admin_email = form.save()
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
        'admin_emails': admin_emails,
        'form': AdminEmailForm(data=None, instance=admin_email)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_admin_email(request):
    ''' Delete a admin_email '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not userApi.is_admin(request.user): raise PermissionDenied

    if request.method == 'POST':
        admin_email_id = request.POST.get('admin_email')
        deleted_admin_email = adminApi.delete_admin_email(admin_email_id)
        if deleted_admin_email:
            messages.success(request, 'Success! {0} deleted'.format(deleted_admin_email.type))
        else:
            messages.error(request, 'An error occurred.')
    return redirect("administrators:admin_emails")
