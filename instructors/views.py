from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_control, never_cache
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q

from administrators.views import APP_STATUS
from administrators.models import *
from administrators.forms import *
from administrators import api as adminApi

from users.models import Role
from users.forms import *
from users import api as userApi

from datetime import datetime


@method_decorator([never_cache], name='dispatch')
class Index(LoginRequiredMixin, View):
    ''' Index page of an instructor's portal '''

    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        request = userApi.has_user_access(request, Role.INSTRUCTOR)

        return render(request, 'instructors/index.html', {
            'loggedin_user': userApi.add_avatar(request.user)
        })


@method_decorator([never_cache], name='dispatch')
class EditUser(LoginRequiredMixin, View):
    ''' Edit user '''

    def setup(self, request, *args, **kwargs):
        setup = super().setup(request, *args, **kwargs)

        request = userApi.has_user_access(request, Role.INSTRUCTOR)
        confidentiality = userApi.has_user_confidentiality_created(request.user)

        # Create a confiential information if it's None
        if not confidentiality:
            confidentiality = userApi.create_confidentiality(request.user)

        self.confidentiality = confidentiality

        return setup

    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        return render(request, 'instructors/users/edit_user.html', {
            'loggedin_user': userApi.add_avatar(request.user),
            'user_form': UserInstructorForm(data=None, instance=request.user),
            'employee_number_form': EmployeeNumberEditForm(data=None, instance=self.confidentiality)
        })

    @method_decorator(require_POST)
    def post(self, request, *args, **kwargs):
        validation = userApi.validate_post(request.POST, ['first_name', 'last_name', 'email'])
        if len(validation) > 0:
            messages.error(request, 'An error occurred while updating an User Edit Form. {0}: This field is required.'.format( ', '.join(validation) ))
            return redirect('instructors:edit_user')

        user_form = UserInstructorForm(request.POST, instance=request.user)
        employee_number_form = EmployeeNumberEditForm(request.POST, instance=self.confidentiality)

        if user_form.is_valid() and employee_number_form.is_valid():
            updated_user = user_form.save()
            updated_employee_number = employee_number_form.save(commit=False)

            updated_employee_number.updated_at = datetime.now()
            updated_employee_number.employee_number = employee_number_form.cleaned_data['employee_number']
            updated_employee_number.is_new_employee = employee_number_form.cleaned_data['is_new_employee']
            updated_employee_number.save(update_fields=['employee_number', 'is_new_employee', 'updated_at'])

            errors = []
            if not updated_user: errors.append('USER')
            if not updated_employee_number: errors.append('EMPLOYEE NUMBER')

            if len(errors) > 0:
                messages.error(request, 'An error occurred while updating an User Edit Form. {0}'.format( ' '.join(errors) ))
                return redirect('instructors:edit_user')

            messages.success(request, 'Success! User Information of {0} (CWL: {1}) has been updated.'.format(request.user.get_full_name(), request.user.username))
            return redirect('instructors:index')
        else:
            errors = []

            user_errors = user_form.errors.get_json_data()
            confid_errors = employee_number_form.errors.get_json_data()

            if user_errors: errors.append( userApi.get_error_messages(user_errors) )
            if confid_errors: errors.append( userApi.get_error_messages(confid_errors) )

            messages.error(request, 'An error occurred while updating an User Form. {0}'.format( ' '.join(errors) ))

        return redirect('instructors:edit_user')


@method_decorator([never_cache], name='dispatch')
class ShowJobs(LoginRequiredMixin, View):
    ''' Display jobs by instructors '''

    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
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
            job_list = job_list.filter(session__term__code__iexact=term_q)
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


@method_decorator([never_cache], name='dispatch')
class EditJob(LoginRequiredMixin, View):
    ''' Update job details of instructors '''

    def setup(self, request, *args, **kwargs):
        setup = super().setup(request, *args, **kwargs)

        session_slug = kwargs.get('session_slug', None)
        job_slug = kwargs.get('job_slug', None)
        if not session_slug or not job_slug:
            raise Http404

        request = userApi.has_user_access(request, Role.INSTRUCTOR)
        job = adminApi.get_job_by_session_slug_job_slug(session_slug, job_slug)

        self.session_slug = session_slug
        self.job = job
        return setup

    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        return render(request, 'instructors/jobs/edit_job.html', {
            'loggedin_user': request.user,
            'job': self.job,
            'form': InstructorJobForm(data=None, instance=self.job),
            'jobs': adminApi.get_recent_ten_job_details(self.job.course, self.job.session.year),
            'next_first': request.session.get('next_first')
        })

    @method_decorator(require_POST)
    def post(self, request, *args, **kwargs):
        form = InstructorJobForm(request.POST, instance=self.job)
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


@method_decorator([never_cache], name='dispatch')
class ShowJob(LoginRequiredMixin, View):
    ''' Display job details '''

    def setup(self, request, *args, **kwargs):
        setup = super().setup(request, *args, **kwargs)

        session_slug = kwargs.get('session_slug', None)
        job_slug = kwargs.get('job_slug', None)
        if not session_slug or not job_slug:
            raise Http404

        request = userApi.has_user_access(request, Role.INSTRUCTOR)
        job = adminApi.get_job_by_session_slug_job_slug(session_slug, job_slug)

        self.job = job
        return setup

    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        return render(request, 'instructors/jobs/show_job.html', {
            'loggedin_user': request.user,
            'job': self.job,
            'next_first': request.session.get('next_first')
        })


@method_decorator([never_cache], name='dispatch')
class ShowApplications(LoginRequiredMixin, View):
    ''' Display applications applied by students '''

    def setup(self, request, *args, **kwargs):
        setup = super().setup(request, *args, **kwargs)
        session_slug = kwargs.get('session_slug', None)
        job_slug = kwargs.get('job_slug', None)

        if not session_slug or not job_slug:
            raise Http404

        request = userApi.has_user_access(request, Role.INSTRUCTOR)

        self.job = adminApi.get_job_by_session_slug_job_slug(session_slug, job_slug)
        self.session_slug = session_slug
        self.job_slug = job_slug

        return setup

    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        request.session['next_second'] = adminApi.build_new_next(request)
        return render(request, 'instructors/jobs/show_applications.html', {
            'loggedin_user': request.user,
            'job': self.job,
            'apps': Application.objects.filter(Q(job__session__slug=self.session_slug) & Q(job__course__slug=self.job_slug)),
            'full_job_name': self.job.course.code.name + '_' + self.job.course.number.name + '_' + self.job.course.section.name,
            'instructor_preference_choices': Application.INSTRUCTOR_PREFERENCE_CHOICES,
            'app_status': APP_STATUS,
            'summary_of_applicants_link': reverse('instructors:summary_applicants', kwargs={'session_slug': self.job.session.slug, 'job_slug': self.job.course.slug}),
            'next_first': request.session.get('next_first', None)
        })

    @method_decorator(require_POST)
    def post(self, request, *args, **kwargs):
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

        if assigned_hours > int(self.job.assigned_ta_hours):
            messages.error( request, 'An error occurred. You cannot assign {0} hours because Total Assigned TA Hours is {1}. then try again.'.format( assigned_hours, int(self.job.assigned_ta_hours) ) )
            return HttpResponseRedirect(request.get_full_path())

        if assigned_hours == 0 and instructor_preference != Application.NO_PREFERENCE:
            messages.error(request, 'An error occurred. Please assign TA hours, then try again.')
            return HttpResponseRedirect(request.get_full_path())

        instructor_app_form = InstructorApplicationForm(request.POST)
        if instructor_app_form.is_valid():
            app_status_form = ApplicationStatusForm(request.POST)
            if app_status_form.is_valid():

                # Update Application
                app = adminApi.get_application(request.POST.get('application'))
                app.instructor_preference = instructor_preference
                app.updated_at = datetime.now()
                app.save(update_fields=['instructor_preference', 'updated_at'])

                if app_status_form.save():
                    messages.success(request, 'Success! {0} (CWL: {1}) has been selected.'.format(app.applicant.get_full_name(), app.applicant.username))
                else:
                    messages.error(request, 'An error occurred while updating an application status.')
            else:
                errors = app_status_form.errors.get_json_data()
                messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))
        else:
            errors = instructor_app_form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return HttpResponseRedirect(request.get_full_path())


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

    session, job, total_applicants, no_offers_applicants, applicants, searched_total_applicants = adminApi.get_summary_applicants(request, session_slug, job_slug)

    return render(request, 'instructors/jobs/summary_applicants.html', {
        'loggedin_user': request.user,
        'session': session,
        'job': job,
        'total_applicants': total_applicants,
        'total_no_offers_applicants': len(no_offers_applicants),
        'applicants': applicants,
        'searched_total_applicants': searched_total_applicants,
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
        email_list = email_list.filter(term__iexact=request.GET.get('term'))
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