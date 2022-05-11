from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_control
from django.db.models import Q, Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from urllib.parse import urlparse
from django.core.mail import EmailMultiAlternatives

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

            #app.applicant = adminApi.get_applicant_status(app.job.session.year, app.job.session.term.code, app.applicant)
            temp_apps = app.applicant.application_set.filter( Q(job__session__year=app.job.session.year) & Q(job__session__term__code=app.job.session.term.code) )
            if temp_apps.count() > 0:
                accepted_apps = []
                for temp_app in temp_apps:
                    temp_app.full_course_name = temp_app.job.course.code.name + '_' + temp_app.job.course.number.name + '_' + temp_app.job.course.section.name
                    temp_app = adminApi.add_app_info_into_application(temp_app, ['accepted', 'declined'])
                    if adminApi.check_valid_accepted_app_or_not(temp_app):
                        accepted_apps.append(temp_app)

                app.applicant.accepted_apps = accepted_apps
                app.applicant = userApi.add_resume(app.applicant)
                app.info = userApi.get_applicant_status_program(app.applicant)

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
@require_http_methods(['GET', 'POST'])
def write_note(request, app_slug):
    ''' Write a note to administraotors '''
    request = userApi.has_user_access(request, Role.INSTRUCTOR)

    app = adminApi.get_application(app_slug, 'slug')
    if request.method == 'POST':
        adminApi.can_req_parameters_access(request, 'none', ['next'], 'POST')

        form = ApplicationNoteForm(request.POST, instance=app)
        if form.is_valid():
            appl = form.save(commit=False)
            appl.updated_at = datetime.now()
            appl.save()
            if appl:
                messages.success(request, 'Success! {0} {1} - {2} {3} {4}: Note for {5}(CWL: {6}) updated.'.format(appl.job.session.year, appl.job.session.term.code, appl.job.course.code.name, appl.job.course.number.name, appl.job.course.section.name, appl.applicant.get_full_name(), appl.applicant.username))
                return HttpResponseRedirect(request.POST.get('next'))
            else:
                messages.error(request, 'An error occurred while writing a note.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return HttpResponseRedirect( reverse('instructors:write_note', args=[app_slug]) )
    else:
        adminApi.can_req_parameters_access(request, 'instructor-link', ['next'], 'GET')

    return render(request, 'instructors/jobs/write_note.html', {
        'loggedin_user': request.user,
        'app': adminApi.add_app_info_into_application(app, ['selected']),
        'form': ApplicationNoteForm(data=None, instance=app),
        'app_status': APP_STATUS,
        'next': adminApi.get_next(request)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def summary_applicants(request, session_slug, job_slug):
    ''' Display the summary of applicants in each session term '''
    request = userApi.has_user_access(request, Role.INSTRUCTOR)

    session = adminApi.get_session(session_slug, 'slug')
    job = adminApi.get_job_by_session_slug_job_slug(session_slug, job_slug)

    session_term = session.year + '_' + session.term.code
    course = job.course.code.name + '_' + job.course.number.name + '_' + job.course.section.name

    applicants = adminApi.get_applicants_in_session(session)
    total_applicants = applicants.count()

    if bool( request.GET.get('first_name') ):
        applicants = applicants.filter(first_name__icontains=request.GET.get('first_name'))
    if bool( request.GET.get('last_name') ):
        applicants = applicants.filter(last_name__icontains=request.GET.get('last_name'))
    if bool( request.GET.get('cwl') ):
        applicants = applicants.filter(username__icontains=request.GET.get('cwl'))
    if bool( request.GET.get('student_number') ):
        applicants = applicants.filter(profile__student_number__icontains=request.GET.get('student_number'))

    no_offers_applicants = []
    for applicant in applicants:
        appls = applicant.application_set.filter( Q(job__session__year=session.year) & Q(job__session__term__code=session.term.code) )

        count_offered_apps = Count('applicationstatus', filter=Q(applicationstatus__assigned=ApplicationStatus.OFFERED))
        offered_apps = appls.annotate(count_offered_apps=count_offered_apps).filter(count_offered_apps__gt=0)

        applicant.no_offers = False
        if len(offered_apps) == 0:
            no_offers_applicants.append(applicant)
            applicant.no_offers = True

    if bool( request.GET.get('no_offers') ):
        applicants = no_offers_applicants

    page = request.GET.get('page', 1)
    #paginator = Paginator(applicants, settings.PAGE_SIZE)
    paginator = Paginator(applicants, 25)

    try:
        applicants = paginator.page(page)
    except PageNotAnInteger:
        applicants = paginator.page(1)
    except EmptyPage:
        applicants = paginator.page(paginator.num_pages)

    for applicant in applicants:
        applicant = userApi.add_resume(applicant)
        applicant.info = userApi.get_applicant_status_program(applicant)

        # To check whether an alert email has been sent to an applicant
        applicant.is_sent_alertemail = False
        is_sent_alertemail = request.user.alertemail_set.filter(
            Q(year=job.session.year) & Q(term=job.session.term.code) &
            Q(job_code=job.course.code.name) & Q(job_number=job.course.number.name) & Q(job_section=job.course.section.name) &
            Q(receiver_name=applicant.get_full_name()) & Q(receiver_email=applicant.email)
        )
        if is_sent_alertemail.count() > 0:
            applicant.is_sent_alertemail = True

        has_applied = False
        apps = applicant.application_set.filter( Q(job__session__year=session.year) & Q(job__session__term__code=session.term.code) )
        applicant.apps = []
        for app in apps:
            app = adminApi.add_app_info_into_application(app, ['applied', 'accepted', 'declined', 'cancelled'])
            app_obj = {
                'course': app.job.course.code.name + ' ' + app.job.course.number.name + ' ' + app.job.course.section.name,
                'applied': app.applied,
                'accepted': None,
                'has_applied': False
            }
            if adminApi.check_valid_accepted_app_or_not(app):
                app_obj['accepted'] = app.accepted

            applicant.apps.append(app_obj)

            # To check whether an application of this user has been applied already
            if (app.job.course.code.name == job.course.code.name) and (app.job.course.number.name == job.course.number.name) and (app.job.course.section.name == job.course.section.name):
                has_applied = True
                app_obj['has_applied'] = True

            applicant.has_applied = has_applied

    return render(request, 'instructors/jobs/summary_applicants.html', {
        'loggedin_user': request.user,
        'session': session,
        'job': job,
        'total_applicants': total_applicants,
        'total_no_offers_applicants': len(no_offers_applicants),
        'applicants': applicants,
        'searched_total': len(applicants),
        'next_second': request.session.get('next_second', None),
        'new_next': adminApi.build_new_next(request)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def applicants_send_email(request):
    ''' Send an email for selected applicants '''
    request = userApi.has_user_access(request, Role.INSTRUCTOR)
    adminApi.can_req_parameters_access(request, 'none', ['next'], 'POST')

    if request.method == 'POST':
        applicants = request.POST.getlist('applicant')
        if len(applicants) > 0:
            request.session['applicants_form_data'] = {
                'applicants': applicants,
                'session_slug': request.POST.get('session_slug'),
                'job_slug': request.POST.get('job_slug')
            }
            return HttpResponseRedirect(reverse('instructors:applicants_send_email_confirmation') + '?next=' + request.POST.get('next'))
        else:
            messages.error(request, 'An error occurred. Please select applicants, then try again.')

    return HttpResponseRedirect(request.POST.get('next'))


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def applicants_send_email_confirmation(request):
    ''' Display the selected appliants '''
    request = userApi.has_user_access(request, Role.INSTRUCTOR)

    applicants = []
    receiver_list = []
    email_form = None
    sample_email = None
    job = None
    form_data = request.session.get('applicants_form_data')
    if form_data:
        job = adminApi.get_job_by_session_slug_job_slug(form_data['session_slug'], form_data['job_slug'])
        applicants = [ userApi.get_user(applicant_id) for applicant_id in form_data['applicants'] ]
        receiver_list = [ applicant.email for applicant in applicants ]

        session_term = str(job.session.year) + ' ' + str(job.session.term.code)
        course = str(job.course.code.name) + ' ' + str(job.course.number.name) + ' ' + str(job.course.section.name)

        title_template = 'Please contact {0} to explore potential TA role'
        message_template = '''<div>
        <p>Hello {5},</p>
        <p>{0} {1} would like to discuss the possibility of a TA role with you, for {4} in {3}. Please email this instructor if you are interested:</p>
        <ul>
            <li>Full Name: {0} {1}</li>
            <li>Email: {2}</li>
        </ul>
        <p><strong>Please do not reply directly to this email.</strong></p>
        <p>Best regards,</p>
        <p>LFS TA Application System</p>
        </div>'''

        if len(form_data['applicants']) == 0:
            messages.error(request, 'An error occurred. No applicants found to send an email, and try again.')
            return HttpResponseRedirect(adminApi.get_next(request))

        if request.method == 'POST':
            adminApi.can_req_parameters_access(request, 'none', ['next'], 'POST')

            receivers = []
            errors = []
            for applicant in applicants:
                receiver = '{0} <{1}>'.format(applicant.get_full_name(), applicant.email)
                title =  title_template.format(request.user.first_name, None, None, None, course, None)
                message = message_template.format(request.user.first_name, request.user.last_name, request.user.email, session_term, course, applicant.get_full_name())

                if adminApi.is_valid_email(applicant.email) == True:
                    form = AlertEmailForm({
                        'year': job.session.year,
                        'term': job.session.term.code,
                        'job_code': job.course.code.name,
                        'job_number': job.course.number.name,
                        'job_section': job.course.section.name,
                        'instructor': request.user.id,
                        'sender': settings.EMAIL_FROM,
                        'receiver_name': applicant.get_full_name(),
                        'receiver_email': applicant.email,
                        'title': title,
                        'message': message
                    })

                    if form.is_valid():
                        msg = EmailMultiAlternatives(title, message, settings.EMAIL_FROM, [receiver])
                        msg.attach_alternative(message, "text/html")
                        msg.send()

                        if form.save():
                            receivers.append(applicant.email)
                        else:
                            errors.append(str(applicant.get_full_name()) + " Form is saved")
                    else:
                        form_errors = form.errors.get_json_data()
                        errors.append( str(applicant.get_full_name()) + " " + userApi.get_error_messages(form_errors))
                else:
                    errors.append( str(applicant.email) + " email address is invalid" )

            if len(receivers) == len(applicants):
                messages.success(request, 'Success! Email has been sent to {0}'.format(', '.join(receivers)))
            else:
                if len(receivers) > 0:
                    messages.error( request, 'An error occurred. Email has been sent to {0}, but not all receivers. Please check a list of receivers.'.format(', '.join(receivers)) )
                else:
                    messages.error(request, 'An error occurred. Failed to send all emails. Please try again. ERROR: {0}'.format(errors))
                    return HttpResponseRedirect(request.get_full_path())

            # Delete session data
            del request.session['applicants_form_data']
            return HttpResponseRedirect(adminApi.get_next(request))
        else:
            adminApi.can_req_parameters_access(request, 'instructor-link', ['next'], 'GET')

            email_form = {
                'sender': settings.EMAIL_FROM,
                'receiver': receiver_list,
                'title': title_template,
                'message': message_template
            }
            sample_email = {
                'sender': settings.EMAIL_FROM,
                'receiver': receiver_list[0],
                'title': title_template.format(request.user.first_name, None, None, None, course, None),
                'message': message_template.format(request.user.first_name, request.user.last_name, request.user.email, session_term, course, applicants[0].get_full_name())
            }
    else:
        messages.error(request, 'An error occurred. No form data found. Try again.')
        return HttpResponseRedirect(adminApi.get_next(request))

    return render(request, 'instructors/jobs/applicants_send_email_confirmation.html', {
        'loggedin_user': request.user,
        'job': job,
        'applicants': applicants,
        'sender': settings.EMAIL_FROM,
        'receiver': receiver_list,
        'email_form': email_form,
        'sample_email': sample_email,
        'next': adminApi.get_next(request)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_email_history(request):
    ''' Display a list of email history '''
    request = userApi.has_user_access(request, Role.INSTRUCTOR)

    email_list = request.user.alertemail_set.all()
    if bool(request.GET.get('year')):
        email_list = email_list.filter(year__icontains=request.GET.get('year'))
    if bool(request.GET.get('term')):
        email_list = email_list.filter(term__icontains=request.GET.get('term'))
    if bool( request.GET.get('code') ):
        email_list = email_list.filter(job_code__icontains=request.GET.get('code'))
    if bool( request.GET.get('number') ):
        email_list = email_list.filter(job_number__icontains=request.GET.get('number'))
    if bool( request.GET.get('section') ):
        email_list = email_list.filter(job_section__icontains=request.GET.get('section'))
    if bool(request.GET.get('receiver_name')):
        email_list = email_list.filter(receiver_name__icontains=request.GET.get('receiver_name'))
    if bool(request.GET.get('receiver_email')):
        email_list = email_list.filter(receiver_email__icontains=request.GET.get('receiver_email'))

    page = request.GET.get('page', 1)
    paginator = Paginator(email_list, settings.PAGE_SIZE)

    try:
        emails = paginator.page(page)
    except PageNotAnInteger:
        emails = paginator.page(1)
    except EmptyPage:
        emails = paginator.page(paginator.num_pages)

    for email in emails:
        email.receiver = "{0} <{1}>".format(email.receiver_name, email.receiver_email)

    return render(request, 'instructors/jobs/show_email_history.html', {
        'loggedin_user': request.user,
        'emails': emails,
        'total': len(email_list)
    })
