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
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from urllib.parse import urlparse

from administrators.views import APP_STATUS
from administrators.models import *
from administrators.forms import *
from administrators import api as adminApi

from users.models import Role
from users.forms import *
from users import api as userApi

from datetime import datetime


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def index(request):
    ''' Index page of an instructor's portal '''
    request = userApi.has_user_access(request, Role.INSTRUCTOR)

    return render(request, 'instructors/index.html', {
        'loggedin_user': userApi.add_avatar(request.user)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_user(request):
    ''' Index page of an instructor's portal '''
    request = userApi.has_user_access(request, Role.INSTRUCTOR)

    confidentiality = userApi.has_user_confidentiality_created(request.user)

    # Create a confiential information if it's None
    if confidentiality == None:
        confidentiality = userApi.create_confidentiality(request.user)

    if request.method == 'POST':
        validation = userApi.validate_post(request.POST, ['first_name', 'last_name', 'email'])
        if len(validation) > 0:
            messages.error(request, 'An error occurred while updating an User Edit Form. {0}: This field is required.'.format( ', '.join(validation) ))
            return redirect('instructors:edit_user')

        user_form = UserInstructorForm(request.POST, instance=request.user)
        employee_number_form = EmployeeNumberEditForm(request.POST, instance=confidentiality)

        if user_form.is_valid() and employee_number_form.is_valid():
            updated_user = user_form.save()
            updated_employee_number = employee_number_form.save(commit=False)

            updated_employee_number.updated_at = datetime.now()
            updated_employee_number.employee_number = employee_number_form.cleaned_data['employee_number']
            updated_employee_number.save(update_fields=['employee_number', 'updated_at'])

            errors = []
            if not updated_user: errors.append('USER')
            if not updated_employee_number: errors.append('EMPLOYEE NUMBER')

            if len(errors) > 0:
                messages.error(request, 'An error occurred while updating an User Edit Form. {0}'.format( ' '.join(errors) ))
                return redirect('instructors:edit_user')

            messages.success(request, 'Success! User information of {0} (CWL: {1}) updated'.format(request.user.get_full_name(), request.user.username))
            return redirect('instructors:index')

        else:
            errors = []

            user_errors = user_form.errors.get_json_data()
            confid_errors = employee_number_form.errors.get_json_data()

            if user_errors: errors.append( userApi.get_error_messages(user_errors) )
            if confid_errors: errors.append( userApi.get_error_messages(confid_errors) )

            messages.error(request, 'An error occurred while updating an User Form. {0}'.format( ' '.join(errors) ))

        return redirect('instructors:edit_user')

    return render(request, 'instructors/users/edit_user.html', {
        'loggedin_user': userApi.add_avatar(request.user),
        'user_form': UserInstructorForm(data=None, instance=request.user),
        'employee_number_form': EmployeeNumberEditForm(data=None, instance=confidentiality)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_jobs(request):
    ''' Display jobs by instructors '''
    request = userApi.has_user_access(request, Role.INSTRUCTOR)

    request.session['next_first'] = adminApi.build_new_next(request)

    year_q = request.GET.get('year')
    term_q = request.GET.get('term')
    code_q = request.GET.get('code')
    number_q = request.GET.get('number')
    section_q = request.GET.get('section')

    job_list = request.user.job_set.all()
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


    return render(request, 'instructors/jobs/show_jobs.html', {
        'loggedin_user': request.user,
        'jobs': jobs,
        'total_jobs': len(job_list)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_job(request, session_slug, job_slug):
    ''' Update job details of instructors '''
    request = userApi.has_user_access(request, Role.INSTRUCTOR)

    job = adminApi.get_job_by_session_slug_job_slug(session_slug, job_slug)
    if request.method == 'POST':
        form = InstructorJobForm(request.POST, instance=job)
        if form.is_valid():
            job = form.save(commit=False)
            job.updated_at = datetime.now()
            job.save()
            if job:
                messages.success(request, 'Success! {0} {1} - {2} {3} {4}: job details updated'.format(job.session.year, job.session.term.code, job.course.code.name, job.course.number.name, job.course.section.name))
                return HttpResponseRedirect(request.POST.get('next_first'))
            else:
                messages.error(request, 'An error occurred while updating job details.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return HttpResponseRedirect(request.get_full_path())


    return render(request, 'instructors/jobs/edit_job.html', {
        'loggedin_user': request.user,
        'job': job,
        'form': InstructorJobForm(data=None, instance=job),
        'jobs': adminApi.get_recent_ten_job_details(job.course, job.session.year),
        'next_first': request.session.get('next_first')
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_job(request, session_slug, job_slug):
    ''' Display job details '''
    request = userApi.has_user_access(request, Role.INSTRUCTOR)

    return render(request, 'instructors/jobs/show_job.html', {
        'loggedin_user': request.user,
        'job': adminApi.get_job_by_session_slug_job_slug(session_slug, job_slug),
        'next_first': request.session.get('next_first')
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def show_applications(request, session_slug, job_slug):
    ''' Display applications applied by students '''
    request = userApi.has_user_access(request, Role.INSTRUCTOR)

    request.session['next_second'] = adminApi.build_new_next(request)

    job = adminApi.get_job_by_session_slug_job_slug(session_slug, job_slug)
    apps = Application.objects.filter( Q(job__session__slug=session_slug) & Q(job__course__slug=job_slug) )

    if request.method == 'POST':
        instructor_preference = request.POST.get('instructor_preference')
        assigned_hours = request.POST.get('assigned_hours')

        if adminApi.is_valid_float(assigned_hours) == False:
            messages.error(request, 'An error occurred. Please check assigned hours. Assign TA Hours must be numerival value only.')
            return HttpResponseRedirect(request.get_full_path())

        if adminApi.is_valid_integer(assigned_hours) == False:
            messages.error(request, 'An error occurred. Please check assigned hours. Assign TA Hours must be non-negative integers.')
            return HttpResponseRedirect(request.get_full_path())

        assigned_hours = int( float(assigned_hours) )

        if assigned_hours < 0:
            messages.error(request, 'An error occurred. Please check assigned hours. Assign TA Hours must be greater than 0.')
            return HttpResponseRedirect(request.get_full_path())

        if instructor_preference == Application.NONE:
            messages.error(request, 'An error occurred. Please select your preference, then try again.')
            return HttpResponseRedirect(request.get_full_path())

        if instructor_preference == Application.NO_PREFERENCE and assigned_hours > 0:
            messages.error(request, 'An error occurred. Please leave 0 for Assign TA Hours if you would like to select No Preference, then try again.')
            return HttpResponseRedirect(request.get_full_path())

        if assigned_hours > int(job.assigned_ta_hours):
            messages.error( request, 'An error occurred. You cannot assign {0} hours because Total Assigned TA Hours is {1}. then try again.'.format( assigned_hours, int(job.assigned_ta_hours) ) )
            return HttpResponseRedirect(request.get_full_path())

        if assigned_hours == 0 and instructor_preference != Application.NO_PREFERENCE:
            messages.error(request, 'An error occurred. Please assign TA hours, then try again.')
            return HttpResponseRedirect(request.get_full_path())


        instructor_app_form = InstructorApplicationForm(request.POST)
        if instructor_app_form.is_valid():
            app_status_form = ApplicationStatusForm(request.POST)

            if app_status_form.is_valid():
                app_id = request.POST.get('application')
                updated_app = adminApi.update_application_instructor_preference(app_id, instructor_preference)
                if updated_app:
                    if app_status_form.save():
                        messages.success(request, 'Success! {0} (CWL: {1}) is selected.'.format(updated_app.applicant.get_full_name(), updated_app.applicant.username))
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

        return HttpResponseRedirect(request.get_full_path())

    else:
        for app in apps:
            app.selected = None
            selected = app.applicationstatus_set.filter(assigned=ApplicationStatus.SELECTED)
            if selected.exists():
                app.selected = selected.last()

            app.applicant = adminApi.get_applicant_status(app.job.session.year, app.job.session.term.code, app.applicant)

    return render(request, 'instructors/jobs/show_applications.html', {
        'loggedin_user': request.user,
        'job': job,
        'apps': apps,
        'full_job_name': job.course.code.name + '_' + job.course.number.name + '_' + job.course.section.name,
        'instructor_preference_choices': Application.INSTRUCTOR_PREFERENCE_CHOICES,
        'app_status': APP_STATUS,
        'next_first': request.session.get('next_first', None)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def status_summary_applicants(request, session_slug):
    ''' Display the status of applicants in each session term '''
    request = userApi.has_user_access(request, Role.INSTRUCTOR)

    session = adminApi.get_session(session_slug, 'slug')

    applicants = User.objects.filter( Q(profile__roles__name='Student') & Q(application__job__session__year=session.year) & Q(application__job__session__term__code=session.term.code) ).order_by('last_name', 'first_name').distinct()
    total_applicants = applicants.count()

    if bool( request.GET.get('first_name') ):
        applicants = applicants.filter(first_name__icontains=request.GET.get('first_name'))
    if bool( request.GET.get('last_name') ):
        applicants = applicants.filter(last_name__icontains=request.GET.get('last_name'))
    if bool( request.GET.get('cwl') ):
        applicants = applicants.filter(username__icontains=request.GET.get('cwl'))
    if bool( request.GET.get('student_number') ):
        applicants = applicants.filter(profile__student_number__icontains=request.GET.get('student_number'))

    page = request.GET.get('page', 1)
    paginator = Paginator(applicants, settings.PAGE_SIZE)

    try:
        applicants = paginator.page(page)
    except PageNotAnInteger:
        applicants = paginator.page(1)
    except EmptyPage:
        applicants = paginator.page(paginator.num_pages)

    for applicant in applicants:
        apps = applicant.application_set.filter( Q(job__session__year=session.year) & Q(job__session__term__code=session.term.code) )

        applicant.apps = []
        for app in apps:
            app = adminApi.add_app_info_into_application(app, ['applied', 'accepted', 'declined', 'cancelled'])
            app_obj = {
                'course': app.job.course.code.name + ' ' + app.job.course.number.name + ' ' + app.job.course.section.name,
                'applied': app.applied,
                'accepted': None
            }
            if adminApi.check_valid_accepted_app_or_not(app):
                app_obj['accepted'] = app.accepted

            applicant.apps.append(app_obj)

    return render(request, 'instructors/jobs/status_summary_applicants.html', {
        'loggedin_user': request.user,
        'session': session,
        'total_applicants': total_applicants,
        'applicants': applicants,
        'next_second': request.session.get('next_second', None)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def write_note(request, app_slug):
    ''' Write a note to administraotors '''
    request = userApi.has_user_access(request, Role.INSTRUCTOR)

    app = adminApi.get_application(app_slug, 'slug')
    if request.method == 'POST':
        form = ApplicationNoteForm(request.POST, instance=app)
        if form.is_valid():
            appl = form.save(commit=False)
            appl.updated_at = datetime.now()
            appl.save()
            if appl:
                messages.success(request, 'Success! {0} {1} - {2} {3} {4}: Note for {5}(CWL: {6}) updated.'.format(appl.job.session.year, appl.job.session.term.code, appl.job.course.code.name, appl.job.course.number.name, appl.job.course.section.name, appl.applicant.get_full_name(), appl.applicant.username))
                return HttpResponseRedirect(request.POST.get('next_second'))
            else:
                messages.error(request, 'An error occurred while writing a note.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return HttpResponseRedirect( reverse('instructors:write_note', args=[app_slug]) )
    else:
        #adminApi.can_req_parameters_access(request, 'instructor-note', [])
        pass

    return render(request, 'instructors/jobs/write_note.html', {
        'loggedin_user': request.user,
        'app': adminApi.add_app_info_into_application(app, ['selected']),
        'form': ApplicationNoteForm(data=None, instance=app),
        'app_status': APP_STATUS,
        'next_second': request.session.get('next_second', None)
    })
