import os
from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_control, never_cache
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods, require_GET, require_POST

from ta_app import utils
from administrators.forms import *
from administrators import api as adminApi

from users.models import Role, Alert
from users.forms import *
from users import api as userApi

from datetime import datetime

IMPORTANT_MESSAGE = '<strong>Important:</strong> Please complete all items in your <strong>Additional Information</strong> tab. If you have not already done so, also upload your <strong>Resume</strong>. <br />When these tabs are complete, you will be able to <strong>Explore Jobs</strong> when the TA Application is open.<br />No official TA offer can be sent to you unless these two sections are completed.  Thanks.'


@method_decorator([never_cache], name='dispatch')
class Index(LoginRequiredMixin, View):
    ''' Index page of Stusent's portal '''

    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        request = userApi.has_user_access(request, Role.STUDENT)

        # To check whether a student has competed an additional information and resume
        can_apply = userApi.can_apply(request.user)
        if not can_apply:
            return HttpResponseRedirect( reverse('students:show_profile') + '?next=' + reverse('students:index') + '&p=Home&t=basic' )

        # To check whether a student has read an alert message
        can_alert = False
        if utils.THIS_MONTH == 3 or utils.THIS_MONTH == 4:
            alert = Alert.objects.filter( Q(student_id=request.user.id) & Q(has_read=True) & Q(created_at__year=utils.THIS_YEAR) )
            if alert.count() == 0:
                can_alert = True

        apps = request.user.application_set.all()

        accepted_apps, total_assigned_hours = adminApi.get_accepted_apps_in_user(request.user)

        return render(request, 'students/index.html', {
            'loggedin_user': userApi.add_avatar(request.user),
            'apps': apps,
            'recent_apps': apps.filter( Q(created_at__year__gte=datetime.now().year) ).order_by('-created_at'),
            'favourites': adminApi.get_favourites(request.user),
            'can_alert': can_alert,
            'expiry_status': userApi.get_confidential_info_expiry_status(request.user),
            'this_year': utils.THIS_YEAR,
            'accepted_apps': accepted_apps,
            'total_assigned_hours': total_assigned_hours
        })

    @method_decorator(require_POST)
    def post(self, request, *args, **kwargs):
        ''' Read an alert message '''
        request = userApi.has_user_access(request, Role.STUDENT)

        form = AlertForm(request.POST)
        if form.is_valid():
            if form.save():
                messages.success(request, 'Success! You have read an alert message.')
            else:
                messages.error(request, 'An error occurred while saving your data. Please try again.')

        return redirect("students:index")


@method_decorator([never_cache], name='dispatch')
class ShowProfile(LoginRequiredMixin, View):
    ''' Display user profile '''

    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        request = userApi.has_user_access(request, Role.STUDENT)
        adminApi.can_req_parameters_access(request, 'student', ['next', 'p', 't'])

        loggedin_user = userApi.add_resume(request.user)

        can_apply = userApi.can_apply(request.user)
        if can_apply == False:
            messages.warning(request, IMPORTANT_MESSAGE)

        return render(request, 'students/profile/show_profile.html', {
            'loggedin_user': userApi.add_avatar(loggedin_user),
            'form': ResumeForm(initial={ 'user': loggedin_user }),
            'current_tab': request.GET.get('t'),
            'can_apply': can_apply,
            'undergrad_status_id': userApi.get_undergraduate_status_id()
        })


@method_decorator([never_cache], name='dispatch')
class EditProfile(LoginRequiredMixin, View):
    ''' Edit user's profile '''

    def setup(self, request, *args, **kwargs):
        setup = super().setup(request, *args, **kwargs)
        request = userApi.has_user_access(request, Role.STUDENT)

        tab = request.GET.get('t', None)
        if not tab or tab not in ['general', 'graduate', 'undergraduate', 'summary']:
            raise Http404
        
        self.tab = tab
        self.user = request.user

        profile = userApi.has_user_profile_created(request.user)
        if not profile:
            raise SuspiciousOperation
        
        undergrad_status_id = userApi.get_undergraduate_status_id()

        path = None
        if getattr(profile, 'status'):
            if profile.status.id == undergrad_status_id:
                path = 'undergraduate'
            else:
                path = 'graduate'

        if not path and tab in ['graduate', 'undergraduate']:
            raise Http404
        
        self.path = path
        self.profile = profile
        self.undergrad_status_id = undergrad_status_id
        
        return setup
    
    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        accepted_apps, total_assigned_hours = adminApi.get_accepted_apps_in_user(self.user)

        context = { 
            'loggedin_user': userApi.add_avatar(self.user),
            'accepted_apps': accepted_apps,
            'total_assigned_hours': total_assigned_hours,
            'path': self.path,
            'current_tab': self.tab,
            'submit_url': reverse('students:edit_profile') + '?t=general' if self.tab == 'general' else reverse('students:update_profile_ta'),
            'confirm_profile_reminder': userApi.confirm_profile_reminder(self.user, session=request.GET.get('session', None))
        }
        
        if self.tab == 'general':
            context['form'] = StudentProfileGeneralForm(instance=self.profile)
        elif self.path == 'graduate' and self.tab == 'graduate':
            context['form'] = StudentProfileGraduateForm(instance=self.profile)
        elif self.path == 'undergraduate' and self.tab == 'undergraduate':
            context['form'] = StudentProfileUndergraduateForm(instance=self.profile)

        return render(request, 'students/profile/edit_profile.html', context=context)

    @method_decorator(require_POST)
    def post(self, request, *args, **kwargs):
        ''' Save profile general changes '''

        PROGRAM_OTHERS = userApi.get_program_others_id()
        if not PROGRAM_OTHERS:
            raise SuspiciousOperation

        profile_degrees = self.profile.degrees.all()
        profile_trainings = self.profile.trainings.all()
        
        form = StudentProfileGeneralForm(request.POST, instance=self.profile)
        if form.is_valid():
            data = form.cleaned_data

            errors = []

            program_others = adminApi.trim(adminApi.strip_html_tags(data['program_others']))
            if data['program'].id == PROGRAM_OTHERS and not program_others:
                errors.append('<strong>Other Program</strong>: Please indicate the name of your program if you select "Other" in <strong>Current Program</strong>.')

            if len(data['degrees']) == 0:
                errors.append('<strong>Most Recent Completed Degrees</strong>: This field is required.')

            if len(data['trainings']) == 0 or len(data['trainings']) != len(userApi.get_active_trainings()):
                errors.append('<strong>Trainings</strong>: You must check all fields to proceed.')

            degree_details = adminApi.trim(adminApi.strip_html_tags(data['degree_details']))
            training_details = adminApi.trim(adminApi.strip_html_tags(data['training_details']))
            lfs_ta_training_details = adminApi.trim(adminApi.strip_html_tags(data['lfs_ta_training_details']))
            if not degree_details:
                errors.append('<strong>Degree Details</strong>: This field is required.')
            if not training_details:
                errors.append('<strong>Training Details</strong>: This field is required.')
            if not lfs_ta_training_details:
                errors.append('<strong>LFS TA Training Details</strong>: This field is required.')
            
            if len(errors) > 0:
                messages.error(request, 'An error occurred. Form is invalid. {0}'.format(' '.join(errors)))
                return HttpResponseRedirect(reverse('students:edit_profile') + '?t=general')
            
            if form.save():
            
                # Update degrees and trainings
                userApi.update_student_profile_degrees_trainings(self.profile, profile_degrees, profile_trainings, data)
                messages.success(request, 'Success! {0} - General information has been updated.'.format(request.user.get_full_name()))
                status = data['status']
                if status.id == self.undergrad_status_id:
                    return HttpResponseRedirect(reverse('students:edit_profile') + '?t=undergraduate')
                else:
                    return HttpResponseRedirect(reverse('students:edit_profile') + '?t=graduate')
            else:
                messages.error(request, "An error occurred while updating student's profile.")
        else:
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.display_error_messages(form.errors.get_json_data()) ))

        return HttpResponseRedirect(reverse('students:edit_profile') + '?t=general')


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def update_profile_ta(request):
    ''' Update profile ta information '''

    path = request.POST.get('path', None)
    if not path:
        raise SuspiciousOperation
    
    form = None
    if path == 'graduate':
        form = StudentProfileGraduateForm(request.POST, instance=request.user.profile)
    elif path == 'undergraduate':
        form = StudentProfileUndergraduateForm(request.POST, instance=request.user.profile)
    
    if not form:
        raise SuspiciousOperation
    
    if form.is_valid():
        data = form.cleaned_data

        errors = []
        ta_experience_details = adminApi.trim(adminApi.strip_html_tags(data['ta_experience_details']))
        qualifications = adminApi.trim(adminApi.strip_html_tags(data['qualifications']))
        if not ta_experience_details:
            errors.append('<strong>Previous TA Experience Details</strong>: This field is required.')
        if not qualifications:
            errors.append('<strong>Explanation of Qualifications</strong>: This field is required.')
        
        if len(errors) > 0:
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format(' '.join(errors)))
            return HttpResponseRedirect(reverse('students:edit_profile') + '?t=' + path)

        if form.save():
            messages.success(request, 'Success! {0} - TA information has been updated.'.format(request.user.get_full_name()))
            return HttpResponseRedirect( reverse('students:show_profile') + '?next=' + reverse('students:edit_profile') + '&p=Edit Profile&t=additional' )
        else:
            messages.error(request, "An error occurred while updating student's profile.")
    else:
        messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.display_error_messages(form.errors.get_json_data()) ))

    return HttpResponseRedirect(reverse('students:edit_profile') + '?t=' + path)


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def confirm_profile_reminder(request):
    ''' Confirm profile reminder '''
    user_id = request.POST.get('user', None)
    session_slug = request.POST.get('session', None)
    if not user_id or not session_slug:
        raise SuspiciousOperation
    
    created = ProfileReminder.objects.create(user_id=user_id, session=session_slug)
    if created:
        messages.success(request, 'Success! Apply Now!')
        return HttpResponseRedirect(reverse('students:available_jobs', args=[session_slug]))

    next = request.POST.get('next', reverse('students:edit_profile') + '?t=general')
    return HttpResponseRedirect(next)


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def upload_resume(request):
    ''' Upload user's resume '''
    request = userApi.has_user_access(request, Role.STUDENT)
    adminApi.can_req_parameters_access(request, 'student', ['next', 'p'])

    loggedin_user = userApi.add_resume(request.user)
    if request.method == 'POST':
        NEXT = reverse('students:show_profile') + '?next=' + request.GET.get('next') + '&p=' + request.GET.get('p') + '&t=resume'
        if len(request.FILES) == 0:
            messages.error(request, 'An error occurred. Please select your resume, then try again.')
            return HttpResponseRedirect(NEXT)

        if loggedin_user.resume_filename:
            messages.error(request, 'An error occurred. Please remove your previous resume, then try again.')
            return HttpResponseRedirect(NEXT)

        form = ResumeForm(request.POST, request.FILES)
        if form.is_valid():
            resume = form.save(commit=False)
            resume.uploaded = request.FILES.get('uploaded')
            resume.save()
            if resume:
                messages.success(request, 'Success! {0} - Resume uploaded'.format( loggedin_user.get_full_name()) )
            else:
                messages.error(request, 'An error occurred while saving a resume.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

    return HttpResponseRedirect(NEXT)


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_resume(request):
    ''' Delete user's resume '''
    request = userApi.has_user_access(request, Role.STUDENT)
    adminApi.can_req_parameters_access(request, 'student', ['next', 'p'])

    if request.method == 'POST':
        res = userApi.delete_user_resume(request.POST.get('user'))
        if res['status'] == 'success':
            messages.success(request, 'Success! Resume deleted')
        elif res['status'] == 'warning':
            messages.warning(request, "Warning! The folder of this resume hasn't been deleted")
        else:
            messages.error(request, 'An error occurred. {0}'.format(res['message']))
    else:
        messages.error(request, 'An error occurred. Request is not POST.')

    return HttpResponseRedirect( reverse('students:show_profile') + '?next=' + request.GET.get('next') + '&p=' + request.GET.get('p') + '&t=resume' )


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_confidentiality(request):
    ''' Display user's confidentiality '''
    request = userApi.has_user_access(request, Role.STUDENT)

    template = 'choose'
    if userApi.has_user_confidentiality_created(request.user) and request.user.confidentiality and request.user.confidentiality.nationality != None:
        template = 'detail'

    user = userApi.add_confidentiality_given_list(request.user, ['sin', 'study_permit'])
    return render(request, 'students/profile/show_confidentiality.html', {
        'loggedin_user': userApi.add_avatar(user),
        'template': template
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def check_confidentiality(request):
    ''' Check whether an international student or not '''
    request = userApi.has_user_access(request, Role.STUDENT)

    if request.method == 'POST':
        form = None
        if userApi.has_user_confidentiality_created(request.user):
            form = ConfidentialityCheckForm(request.POST, instance=request.user.confidentiality)
        else:
            form = ConfidentialityCheckForm(request.POST)

        if form.is_valid():
            confi = form.save(commit=False)
            confi.created_at = datetime.now()
            confi.updated_at = datetime.now()
            confi.save()
            if confi:
                messages.info(request, 'Please submit your information.')
            else:
                messages.error(request, 'An error occurred while saving confidentiality.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

    return redirect('students:submit_confidentiality')

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def submit_confidentiality(request):
    ''' Submit user's confidentiality '''
    request = userApi.has_user_access(request, Role.STUDENT)

    loggedin_user = request.user
    form = None
    confidentiality = userApi.has_user_confidentiality_created(loggedin_user)
    if request.method == 'POST':
        if confidentiality is not None:
            if loggedin_user.confidentiality.nationality == '0':
                form = ConfidentialityDomesticForm(request.POST, request.FILES, instance=loggedin_user.confidentiality)
            else:
                form = ConfidentialityInternationalForm(request.POST, request.FILES, instance=loggedin_user.confidentiality)

            is_new_employee = request.POST.get('is_new_employee')
            employee_number = request.POST.get('employee_number')

            if confidentiality.is_new_employee == True:
                if bool(is_new_employee) == False:
                    # New employees (no employee number) must check is_new_employee
                    if bool(employee_number) == False:
                        messages.error(request, 'An error occurred. New employees must check this <strong>I am a new employee</strong> field.')
                        return redirect('students:show_confidentiality')
                else:
                    # Not a new employee
                    if bool(employee_number) == True:
                        messages.error(request, 'An error occurred. Please uncheck this <strong>I am a new employee</strong> field if you are not a new employee.')
                        return redirect('students:show_confidentiality')
            else:
                # Only new employees (no employee number) can check is_new_employee
                if bool(employee_number) == True and bool(is_new_employee) == True:
                    messages.error(request, 'An error occurred. Your Employee Number is {0}. Only new employees can check this <strong>I am a new employee</strong> field.'.format(confidentiality.employee_number))
                    return redirect('students:show_confidentiality')

        if form.is_valid():
            updated_confidentiality = form.save(commit=False)
            updated_confidentiality.created_at = datetime.now()
            updated_confidentiality.updated_at = datetime.now()

            updated_confidentiality.sin = request.FILES.get('sin')
            updated_confidentiality.study_permit = request.FILES.get('study_permit')

            updated_confidentiality.save()
            if updated_confidentiality:
                messages.success(request, 'Success! {0} - Confidential information submitted'.format(loggedin_user.get_full_name()))
                return redirect('students:show_confidentiality')
            else:
                messages.error(request, 'An error occurred while saving confidentiality.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return redirect('students:submit_confidentiality')

    else:
        if confidentiality:
            if loggedin_user.confidentiality.nationality == '0':
                form = ConfidentialityDomesticForm(data=None, instance=loggedin_user.confidentiality, initial={ 'user': loggedin_user })
            else:
                form = ConfidentialityInternationalForm(data=None, instance=loggedin_user.confidentiality, initial={ 'user': loggedin_user })

    return render(request, 'students/profile/submit_confidentiality.html', {
        'loggedin_user': userApi.add_avatar(loggedin_user),
        'form': form,
        'confidentiality': confidentiality
    })


@method_decorator([never_cache], name='dispatch')
class EditConfidentiality(LoginRequiredMixin, View):
    
    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        request = userApi.has_user_access(request, Role.STUDENT)

        form = None
        sin_file = None
        study_permit_file = None
        can_delete = False

        confidentiality = userApi.has_user_confidentiality_created(request.user)
        if confidentiality:
            if bool(confidentiality.employee_number):
                can_delete = True
            if bool(confidentiality.sin):
                sin_file = os.path.basename(confidentiality.sin.name)
                can_delete = True

            if bool(confidentiality.study_permit):
                study_permit_file = os.path.basename(confidentiality.study_permit.name)
                can_delete = True

            if bool(confidentiality.date_of_birth):
                can_delete = True

            if confidentiality.nationality == '0':
                form = ConfidentialityDomesticForm(data=None, instance=confidentiality, initial={ 'user': request.user })
            else:
                form = ConfidentialityInternationalForm(data=None, instance=confidentiality, initial={ 'user': request.user })
                if bool(confidentiality.sin_expiry_date):
                    can_delete = True
                if bool(confidentiality.study_permit_expiry_date):
                    can_delete = True
        
        if not form:
            raise SuspiciousOperation

        return render(request, 'students/profile/edit_confidentiality.html', {
            'loggedin_user': userApi.add_avatar(request.user),
            'sin_file': sin_file,
            'study_permit_file': study_permit_file,
            'form': form,
            'can_delete': can_delete,
            'confidentiality': confidentiality
        })

    @method_decorator(require_POST)
    def post(self, request, *args, **kwargs):
        is_new_employee = request.POST.get('is_new_employee')
        employee_number = request.POST.get('employee_number')
        
        confidentiality = userApi.has_user_confidentiality_created(request.user)
        if confidentiality.is_new_employee == True:
            if bool(is_new_employee) == False:
                # New employees (no employee number) must check is_new_employee
                if bool(employee_number) == False:
                    messages.error(request, 'An error occurred. New employees must check this <strong>I am a new employee</strong> field.')
                    return redirect('students:edit_confidentiality')
            else:
                # Not a new employee
                if bool(employee_number) == True:
                    messages.error(request, 'An error occurred. Please uncheck this <strong>I am a new employee</strong> field if you are not a new employee.')
                    return redirect('students:edit_confidentiality')
        else:
            # Only new employees (no employee number) can check is_new_employee
            if bool(is_new_employee) == True:
                messages.error(request, 'An error occurred. Your Employee Number is {0}. Only new employees can check this <strong>I am a new employee</strong> field.'.format(confidentiality.employee_number))
                return redirect('students:edit_confidentiality')

        # Check SIN and Study Permit
        sin_study_permit_errors = []
        if request.FILES.get('sin') and bool(confidentiality.sin):
            sin_study_permit_errors.append('SIN')
        if request.FILES.get('study_permit') and bool(confidentiality.study_permit):
            sin_study_permit_errors.append('Study Permit')

        if len(sin_study_permit_errors) > 0:
            msg = ' and '.join(sin_study_permit_errors)
            messages.error(request, 'An error occurred. Please delete your old {0} first, and then try again.'.format(msg))
            return redirect('students:edit_confidentiality')

        form = ConfidentialityForm(request.POST, request.FILES, instance=confidentiality)
        if form.is_valid():
            data = form.cleaned_data
            user = data['user']

            updated_confidentiality = form.save(commit=False)
            updated_confidentiality.updated_at = datetime.now()

            update_fields = ['updated_at']
            if data['nationality'] is not None:
                updated_confidentiality.nationality = data['nationality']
                update_fields.append('nationality')

            if data['is_new_employee'] is not None:
                updated_confidentiality.is_new_employee = data['is_new_employee']
                update_fields.append('is_new_employee')

            if data['employee_number'] is not None:
                updated_confidentiality.employee_number = data['employee_number']
                update_fields.append('employee_number')

            if request.FILES.get('sin') is not None:
                updated_confidentiality.sin = request.FILES.get('sin')
                update_fields.append('sin')

            if data['sin_expiry_date'] is not None:
                updated_confidentiality.sin_expiry_date = data['sin_expiry_date']
                update_fields.append('sin_expiry_date')

            if request.FILES.get('study_permit') is not None:
                updated_confidentiality.study_permit = request.FILES.get('study_permit')
                update_fields.append('study_permit')

            if data['study_permit_expiry_date'] is not None:
                updated_confidentiality.study_permit_expiry_date = data['study_permit_expiry_date']
                update_fields.append('study_permit_expiry_date')

            if data['date_of_birth'] is not None:
                updated_confidentiality.date_of_birth = data['date_of_birth']
                update_fields.append('date_of_birth')

            updated_confidentiality.save(update_fields=update_fields)

            if updated_confidentiality:
                messages.success(request, 'Success! Confidential information of {0} updated'.format(request.user.get_full_name()))
                return redirect('students:show_confidentiality')
            else:
                messages.error(request, 'An error occurred while updating confidential information.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return redirect('students:edit_confidentiality')

 
@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_confidential_information(request):
    ''' Delete a confidential information '''
    request = userApi.has_user_access(request, Role.STUDENT)

    if request.method == 'POST':
        data = []
        if request.POST.get('date_of_birth') != None: data.append('date_of_birth')
        if request.POST.get('employee_number') != None: data.append('employee_number')
        if request.POST.get('sin') != None: data.append('sin')
        if request.POST.get('sin_expiry_date') != None: data.append('sin_expiry_date')
        if request.POST.get('study_permit') != None: data.append('study_permit')
        if request.POST.get('study_permit_expiry_date') != None: data.append('study_permit_expiry_date')

        if len(data) == 0:
            messages.error(request, 'An error occurred while deleting. Please select any information that you want to delete.')
            return redirect('students:edit_confidentiality')

        result = userApi.delete_confidential_information(request.POST)
        if result == True:
            messages.success(request, 'Success! Confidential Information of {0} deleted'.format(request.POST.get('user')))
        else:
            messages.error(request, 'An error occurred while deleting. Failed to delete {0}'.format(result))

    return redirect('students:edit_confidentiality')


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def download_file(request, username, item, filename):
    ''' Download user' uploaded files '''
    if userApi.is_valid_user(request.user) == False:
        raise PermissionDenied

    file_path = os.path.join(settings.MEDIA_ROOT, 'users', username, item, filename)
    filename_splited = os.path.splitext(filename)

    content_type = None
    if '.doc' in filename_splited:
        content_type = 'application/msword'
    elif '.docx' in filename_splited:
        content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    elif '.pdf' in filename_splited:
        content_type = 'application/pdf'
    elif '.jpg' in filename_splited or '.jpeg' in filename_splited:
        content_type = 'image/jpeg'
    elif '.png' in filename_splited:
        content_type = 'image/png'

    if os.path.exists(file_path) or content_type is not None:
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type=content_type)
            response['Content-Disposition'] = 'inline; filename=' + filename
            return response
    raise Http404


# Jobs

@method_decorator([never_cache], name='dispatch')
class ExploreJobs(LoginRequiredMixin, View):
    ''' Index page of Stusent's portal '''

    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        ''' Display all lists of session terms '''
        request = userApi.has_user_access(request, Role.STUDENT)

        can_apply = userApi.can_apply(request.user)
        if not can_apply:
            messages.warning(request, IMPORTANT_MESSAGE)

        sessions = Session.objects.filter(is_visible=True, is_archived=False)
        for session in sessions:
            session.is_locked = True
            found = ProfileReminder.objects.filter(user=request.user, session=session.slug).exists()
            if found:
                session.is_locked = False

        return render(request, 'students/jobs/explore_jobs.html', {
            'loggedin_user': userApi.add_avatar(request.user),
            'visible_current_sessions': sessions,
            'favourites': adminApi.get_favourites(request.user),
            'can_apply': can_apply,
            'expiry_status': userApi.get_confidential_info_expiry_status(request.user),
            'this_year': utils.THIS_YEAR
        })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def favourite_jobs(request):
    ''' Display all lists of session terms '''
    request = userApi.has_user_access(request, Role.STUDENT)

    if request.method == 'POST':
        form = FavouriteForm(request.POST)
        if form.is_valid():
            job = form.cleaned_data['job']
            deleted = adminApi.delete_favourite_job(request.user, job)
            if deleted:
                messages.success(request, 'Success! {0} {1} - {2} {3} {4} deleted'.format(job.session.year, job.session.term.code, job.course.code.name, job.course.number.name, job.course.section.name))
            else:
                messages.error(request, 'An error occurred while deleting your favourite job. Please try again.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return HttpResponseRedirect(request.get_full_path())
    else:
        year_q = request.GET.get('year')
        term_q = request.GET.get('term')
        code_q = request.GET.get('code')
        number_q = request.GET.get('number')
        section_q = request.GET.get('section')
        instructor_first_name_q = request.GET.get('instructor_first_name')
        instructor_last_name_q = request.GET.get('instructor_last_name')
        exclude_applied_jobs_q = request.GET.get('exclude_applied_jobs')
        exclude_inactive_jobs_q = request.GET.get('exclude_inactive_jobs')

        favourite_list = adminApi.get_favourites(request.user)
        all_favourites = favourite_list
        if bool(year_q):
            favourite_list = favourite_list.filter(job__session__year__icontains=year_q)
        if bool(term_q):
            favourite_list = favourite_list.filter(job__session__term__code__iexact=term_q)
        if bool(code_q):
            favourite_list = favourite_list.filter(job__course__code__name__icontains=code_q)
        if bool(number_q):
            favourite_list = favourite_list.filter(job__course__number__name__icontains=number_q)
        if bool(section_q):
            favourite_list = favourite_list.filter(job__course__section__name__icontains=section_q)
        if bool(instructor_first_name_q):
            favourite_list = favourite_list.filter(job__instructors__first_name__icontains=instructor_first_name_q)
        if bool(instructor_last_name_q):
            favourite_list = favourite_list.filter(job__instructors__last_name__icontains=instructor_last_name_q)
        if exclude_applied_jobs_q == '1':
            favourite_list = favourite_list.exclude(job__application__applicant__id=request.user.id)
        if exclude_inactive_jobs_q == '1':
            favourite_list = favourite_list.exclude(job__is_active=False)

        page = request.GET.get('page', 1)
        paginator = Paginator(favourite_list, settings.PAGE_SIZE)

        try:
            favourites = paginator.page(page)
        except PageNotAnInteger:
            favourites = paginator.page(1)
        except EmptyPage:
            favourites = paginator.page(paginator.num_pages)

    return render(request, 'students/jobs/favourite_jobs.html', {
        'loggedin_user': userApi.add_avatar(request.user),
        'all_favourites': all_favourites,
        'favourites': adminApi.add_applied_jobs_to_favourites(request.user, favourites),
        'total_favourites': len(favourite_list),
        'can_apply': userApi.can_apply(request.user),
        'new_next': adminApi.build_new_next(request)
    })


@method_decorator([never_cache], name='dispatch')
class AvailableJobs(LoginRequiredMixin, View):

    def setup(self, request, *args, **kwargs):
        setup = super().setup(request, *args, **kwargs)

        session_slug = kwargs.get('session_slug', None)
        if not session_slug:
            raise Http404

        confirm_profile_reminder = userApi.confirm_profile_reminder(request.user, session_slug)
        if not confirm_profile_reminder:
            raise PermissionDenied

        request = userApi.has_user_access(request, Role.STUDENT)

        can_apply = userApi.can_apply(request.user)
        if can_apply == False:
            raise PermissionDenied
        
        adminApi.available_session(session_slug) # raise PermissionDenied
        
        self.session_slug = session_slug
        self.can_apply = can_apply

        return setup
    
    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        ''' Display jobs available to apply '''

        code_q = request.GET.get('code')
        number_q = request.GET.get('number')
        section_q = request.GET.get('section')
        instructor_first_name_q = request.GET.get('instructor_first_name')
        instructor_last_name_q = request.GET.get('instructor_last_name')
        exclude_applied_jobs_q = request.GET.get('exclude_applied_jobs')
        exclude_inactive_jobs_q = request.GET.get('exclude_inactive_jobs')

        job_list = adminApi.get_jobs().filter(session__slug=self.session_slug)
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
        if exclude_applied_jobs_q == '1':
            job_list = job_list.exclude(application__applicant__id=request.user.id)
        if exclude_inactive_jobs_q == '1':
            job_list = job_list.exclude(is_active=False)

        page = request.GET.get('page', 1)
        paginator = Paginator(job_list, settings.PAGE_SIZE)

        try:
            jobs = paginator.page(page)
        except PageNotAnInteger:
            jobs = paginator.page(1)
        except EmptyPage:
            jobs = paginator.page(paginator.num_pages)

        return render(request, 'students/jobs/available_jobs.html', {
            'loggedin_user': userApi.add_avatar(request.user),
            'session_slug': self.session_slug,
            'jobs': adminApi.add_applied_favourite_jobs(request.user, jobs),
            'total_jobs': len(job_list),
            'can_apply': self.can_apply,
            'new_next': adminApi.build_new_next(request)
        })


@method_decorator([never_cache], name='dispatch')
class ApplyJob(LoginRequiredMixin, View):

    def setup(self, request, *args, **kwargs):
        setup = super().setup(request, *args, **kwargs)

        session_slug = kwargs.get('session_slug', None)
        job_slug = kwargs.get('job_slug', None)
        if not session_slug or not job_slug:
            raise Http404

        confirm_profile_reminder = userApi.confirm_profile_reminder(request.user, session_slug)
        if not confirm_profile_reminder:
            raise PermissionDenied
        
        request = userApi.has_user_access(request, Role.STUDENT)
        adminApi.can_req_parameters_access(request, 'none', ['next'])

        next = adminApi.get_next(request)

        # There are two paths to apply a job
        # If the path doesn't contian favourite, then check session in the path
        if 'favourite' not in next:
            adminApi.validate_next(next, ['session'])

        session = adminApi.get_session(session_slug, 'slug')
        job = adminApi.get_job_by_session_slug_job_slug(session_slug, job_slug)

        can_apply = userApi.can_apply(request.user)
        UNDERGRADUATE_STUDENT = userApi.get_undergraduate_status_id()

        if not session.is_visible or session.is_archived or not job.is_active or not can_apply or not UNDERGRADUATE_STUDENT:
            raise PermissionDenied

        self.session_slug = session_slug
        self.job_slug = job_slug
        self.UNDERGRADUATE_STUDENT = UNDERGRADUATE_STUDENT
        self.job = job
        self.next = next

        return setup

    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        ''' Students can apply for each job '''

        return render(request, 'students/jobs/apply_job.html', {
            'loggedin_user': request.user,
            'job': adminApi.add_favourite_job(request.user, self.job),
            'has_applied_job': self.job.application_set.filter(applicant__id=request.user.id).exists(),
            'form': ApplicationForm(initial={ 'applicant': request.user.id, 'job': self.job.id }),
            'next': self.next
        })

    @method_decorator(require_POST)
    def post(self, request, *args, **kwargs):

        # Check whether a next url is valid or not
        adminApi.can_req_parameters_access(request, 'none', ['next'], 'POST')

        if request.user.profile.status and request.user.profile.status.id != self.UNDERGRADUATE_STUDENT and not request.POST.get('supervisor_approval'):
            messages.error(request, 'An error occurred. You must check "Yes" in the box under <strong>Supervisor Approval</strong> if you are a <strong>graduate student</strong>. Undergraduate students should leave this box blank.')
            return HttpResponseRedirect(request.get_full_path())

        if request.POST.get('how_qualified') == '0' or request.POST.get('how_interested') == '0':
            messages.error(request, 'An error occurred. Please select both <strong>How qualifed are you?</strong> and <strong>How interested are you?</strong>.')
            return HttpResponseRedirect(request.get_full_path())

        if not request.POST.get('availability'):
            messages.error(request, 'An error occurred. You must check "I understand" in the box under <strong>Availability Requirements</strong>. Please read through it.')
            return HttpResponseRedirect(request.get_full_path())

        form = ApplicationForm(request.POST)
        if form.is_valid():
            app = form.save()
            if app:
                app_status = adminApi.create_application_status(app)
                if app_status:
                    messages.success(request, 'Success! {0} {1} - {2} {3} {4} applied'.format(self.job.session.year, self.job.session.term.code, self.job.course.code.name, self.job.course.number.name, self.job.course.section.name))
                    return HttpResponseRedirect(request.POST.get('next'))
                else:
                    messages.error(request, 'An error occurred while creating a status of an application.')
            else:
                messages.error(request, 'An error occurred while saving an application.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return HttpResponseRedirect(request.get_full_path())


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def select_favourite_job(request, session_slug, job_slug):
    ''' Select favourite jobs '''
    request = userApi.has_user_access(request, Role.STUDENT)

    if request.method == 'POST':

        # Check whether a next url is valid or not
        adminApi.can_req_parameters_access(request, 'none', ['next'], 'POST')

        form = FavouriteForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            job = data['job']

            if data['is_selected']:
                fav = form.save()
                if fav:
                    messages.success(request, 'Success! {0} {1} - {2} {3} {4} added'.format(job.session.year, job.session.term.code, job.course.code.name, job.course.number.name, job.course.section.name))
                else:
                    messages.error(request, 'An error occurred while adding your favourite job. Please try again.')
            else:
                deleted = adminApi.delete_favourite_job(request.user, job)
                if deleted:
                    messages.success(request, 'Success! {0} {1} - {2} {3} {4} deleted'.format(job.session.year, job.session.term.code, job.course.code.name, job.course.number.name, job.course.section.name))
                else:
                    messages.error(request, 'An error occurred while deleting your favourite job. Please try again.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return HttpResponseRedirect( reverse('students:apply_job', args=[session_slug, job_slug]) + '?next=' + request.POST.get('next') )


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def history_jobs(request):
    ''' Display History of Jobs and total accepted assigned hours '''
    request = userApi.has_user_access(request, Role.STUDENT)

    year_q = request.GET.get('year')
    term_q = request.GET.get('term')
    code_q = request.GET.get('code')
    number_q = request.GET.get('number')
    section_q = request.GET.get('section')

    app_list = request.user.application_set.all()
    if bool(year_q):
        app_list = app_list.filter(job__session__year__icontains=year_q)
    if bool(term_q):
        app_list = app_list.filter(job__session__term__code__iexact=term_q)
    if bool(code_q):
        app_list = app_list.filter(job__course__code__name__icontains=code_q)
    if bool(number_q):
        app_list = app_list.filter(job__course__number__name__icontains=number_q)
    if bool(section_q):
        app_list = app_list.filter(job__course__section__name__icontains=section_q)

    page = request.GET.get('page', 1)
    paginator = Paginator(app_list, settings.PAGE_SIZE)

    try:
        apps = paginator.page(page)
    except PageNotAnInteger:
        apps = paginator.page(1)
    except EmptyPage:
        apps = paginator.page(paginator.num_pages)


    # Add applications with latest status
    for app in apps:
        app.applied = None
        applied = app.applicationstatus_set.filter(assigned=ApplicationStatus.NONE)
        if applied.exists(): app.applied = applied.first()

        status = app.applicationstatus_set.all().last()
        if status.assigned == ApplicationStatus.OFFERED:
            app.offered = None
            offered = app.applicationstatus_set.filter(assigned=ApplicationStatus.OFFERED)
            if offered.exists(): app.offered = offered.last()

        elif status.assigned == ApplicationStatus.ACCEPTED:
            app.accepted = None
            accepted = app.applicationstatus_set.filter(assigned=ApplicationStatus.ACCEPTED)
            if accepted.exists(): app.accepted = accepted.last()

        elif status.assigned == ApplicationStatus.DECLINED:
            app.declined = None
            declined = app.applicationstatus_set.filter(assigned=ApplicationStatus.DECLINED)
            if declined.exists():
                app.declined = declined.last()

        elif status.assigned == ApplicationStatus.CANCELLED:
            app.cancelled = None
            cancelled = app.applicationstatus_set.filter(assigned=ApplicationStatus.CANCELLED)
            if cancelled.exists(): app.cancelled = cancelled.last()

    return render(request, 'students/jobs/history_jobs.html', {
        'loggedin_user': request.user,
        'apps': apps,
        'total_apps': len(app_list)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def terminate_job(request, session_slug, job_slug):
    ''' Cancel/terminate an accepted job '''
    request = userApi.has_user_access(request, Role.STUDENT)
    adminApi.can_req_parameters_access(request, 'none', ['next'])

    apps = request.user.application_set.all()
    app = apps.filter(job__session__slug=session_slug, job__course__slug=job_slug)

    if app is None or len(app) == 0: raise Http404

    app = adminApi.add_app_info_into_application(app.first(), ['accepted', 'cancelled'])
    if not app.is_terminated or app.cancelled: raise Http404

    if request.method == 'POST':

        # Check whether a next url is valid or not
        adminApi.can_req_parameters_access(request, 'none', ['next'], 'POST')

        assigned_hours = request.POST.get('assigned_hours')
        form = ApplicationStatusReassignForm({
            'application': request.POST.get('application'),
            'assigned': ApplicationStatus.CANCELLED,
            'assigned_hours': assigned_hours,
            'parent_id': app.accepted.id
        })
        if form.is_valid():
            if form.save():
                if adminApi.update_job_accumulated_ta_hours(session_slug, job_slug, -1 * float(assigned_hours)):
                    messages.success(request, 'Application of {0} {1} - {2} {3} {4} terminated.'.format(app.job.session.year, app.job.session.term.code, app.job.course.code.name, app.job.course.number.name, app.job.course.section.name))
                    return HttpResponseRedirect(request.POST.get('next'))
                else:
                    messages.error(request, 'An error occurred while updating accumulated ta hours.')
            else:
                messages.error(request, 'An error occurred while saving application status.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return HttpResponseRedirect(request.get_full_path())

    return render(request, 'students/jobs/terminate_job.html', {
        'loggedin_user': request.user,
        'app': app
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def accept_decline_job(request, session_slug, job_slug):
    ''' Display a job to select accept or decline a job offer '''
    request = userApi.has_user_access(request, Role.STUDENT)
    adminApi.can_req_parameters_access(request, 'none', ['next'])

    apps = request.user.application_set.all()
    apps = apps.filter( Q(job__session__slug=session_slug) & Q(job__course__slug=job_slug) )
    if len(apps) == 0:
        raise Http404

    app = adminApi.add_app_info_into_application(apps.first(), ['offered', 'accepted', 'declined'])
    if app.job.session.is_archived == True or app.offered is None:
        raise PermissionDenied

    return render(request, 'students/jobs/accept_decline_job.html', {
        'loggedin_user': request.user,
        'app': app,
        'latest_status': adminApi.get_latest_status_in_app(app),
        'can_accept': userApi.add_confidentiality_validation(request.user),
        'job_offer_details': adminApi.get_job_offer_details(request.user, app, 'offered')
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def make_decision(request, session_slug, job_slug):
    ''' Students accept a job offer '''
    request = userApi.has_user_access(request, Role.STUDENT)
    if request.method == 'POST':

        # Check whether a next url is valid or not
        adminApi.can_req_parameters_access(request, 'none', ['next'], 'POST')
        errors = []
        if request.POST.get('has_contract_read') == None:
            errors.append('Please read and understand a Job Offer Contract')
        if request.POST.get('decision') == None:
            errors.append('Please choose "Accept" or "Decline"')
        if len(errors) > 0:
            messages.error(request, 'An error occurred. {0}.'.format( '. '.join(errors) ))
            return HttpResponseRedirect( reverse('students:accept_decline_job', args=[session_slug, job_slug]) + '?next=' + request.POST.get('next') )

        # Accept a job offer
        if request.POST.get('decision') == 'accept':

            # Check required documents
            can_accept = userApi.add_confidentiality_validation(request.user)
            if can_accept['status'] == False:
                messages.error(request, 'An error occurred. {0}'.format(can_accept['message']))
                return HttpResponseRedirect( reverse('students:accept_decline_job', args=[session_slug, job_slug]) + '?next=' + request.POST.get('next') )

            assigned_hours = request.POST.get('assigned_hours')
            form = ApplicationStatusForm({
                'application': request.POST.get('application'),
                'assigned': ApplicationStatus.ACCEPTED,
                'assigned_hours': assigned_hours,
                'has_contract_read': True
            })

            if form.is_valid():
                app = form.cleaned_data['application']
                if form.save():
                    app.updated_at = datetime.now()
                    app.save(update_fields=['updated_at'])

                    # Update acccumulated ta hours
                    if adminApi.update_job_accumulated_ta_hours(session_slug, job_slug, float(assigned_hours)):

                        # Update Worktag to Admin Docs
                        ad_filtered = AdminDocuments.objects.filter(application_id=app.id)
                        ws_filtered = WorktagSetting.objects.filter(application_id=app.id)
                        if ws_filtered.exists():
                            worktag = ws_filtered.first().worktag
                            if ad_filtered.exists():
                                ad_filtered.update(worktag=worktag)
                            else:
                                AdminDocuments.objects.create(application_id=app.id, worktag=worktag)
                        else:
                            if app.job.course.code.name in settings.WORKTAG_MAP.keys():
                                worktag = settings.WORKTAG_MAP[app.job.course.code.name]
                                if ad_filtered.exists():
                                    ad_filtered.update(worktag=worktag)
                                else:
                                    AdminDocuments.objects.create(application_id=app.id, worktag=worktag)

                        messages.success(request, 'Success! You accepted the job offer - {0} {1}: {2} {3} {4}'.format(app.job.session.year, app.job.session.term.code, app.job.course.code.name, app.job.course.number.name, app.job.course.section.name))
                        return HttpResponseRedirect(request.POST.get('next'))
                    else:
                        messages.error(request, 'An error occurred while updating ta hours.')
                else:
                    messages.error(request, 'An error occurred while saving a status of an application.')
            else:
                errors = form.errors.get_json_data()
                messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))


        # Decline a job offer
        elif request.POST.get('decision') == 'decline':
            form = ApplicationStatusForm({
                'application': request.POST.get('application'),
                'assigned': ApplicationStatus.DECLINED,
                'assigned_hours': 0.0,
                'has_contract_read': True
            })
            if form.is_valid():
                app = form.cleaned_data['application']
                if form.save():
                    app.updated_at = datetime.now()
                    app.save(update_fields=['updated_at'])

                    messages.success(request, 'You declined the job offer - {0} {1}: {2} {3} {4}.'.format(app.job.session.year, app.job.session.term.code, app.job.course.code.name, app.job.course.number.name, app.job.course.section.name))
                    return HttpResponseRedirect(request.POST.get('next'))
                else:
                    messages.error(request, 'An error occurred while saving an status of an application.')
            else:
                errors = form.errors.get_json_data()
                messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

    return HttpResponseRedirect( reverse('students:accept_decline_job', args=[session_slug, job_slug]) + '?next=' + request.POST.get('next') )


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET','POST'])
def reaccept_application(request, app_slug):
    ''' Re-accept an accepted application after declined '''
    request = userApi.has_user_access(request, Role.STUDENT)

    app = adminApi.get_application(app_slug, 'slug')
    app = adminApi.add_app_info_into_application(app, ['accepted','declined'])
    if app.job.session.is_archived == True or app.is_declined_reassigned != True:
        raise PermissionDenied

    if request.method == 'POST':

        # Check whether a next url is valid or not
        adminApi.can_req_parameters_access(request, 'none', ['next'], 'POST')

        errors = []
        if request.POST.get('has_contract_read') == None:
            errors.append('Please read and understand a Job Offer Contract')
        if request.POST.get('decision') == None:
            errors.append('Please choose "Accept" or "Decline"')
        if len(errors) > 0:
            messages.error(request, 'An error occurred. {0}.'.format( '. '.join(errors) ))
            return HttpResponseRedirect(request.get_full_path())

        # Accept a job offer
        if request.POST.get('decision') == 'accept':

            # Check required documents
            can_accept = userApi.add_confidentiality_validation(request.user)
            if can_accept['status'] == False:
                messages.error(request, 'An error occurred. {0}'.format(can_accept['message']))
                return HttpResponseRedirect(request.get_full_path())

            assigned_hours = request.POST.get('assigned_hours')
            form = ApplicationStatusForm({
                'application': request.POST.get('application'),
                'assigned': ApplicationStatus.ACCEPTED,
                'assigned_hours': assigned_hours,
                'has_contract_read': True
            })
            if form.is_valid():
                appl = form.cleaned_data['application']
                if form.save():
                    appl.updated_at = datetime.now()
                    appl.save(update_fields=['updated_at'])

                    # Update new hours
                    new_hours = float(assigned_hours) - float(app.accepted.assigned_hours )
                    if adminApi.update_job_accumulated_ta_hours(appl.job.session.slug, appl.job.course.slug, new_hours):
                        messages.success(request, 'Success! You accepted the job offer - {0} {1}: {2} {3} {4} '.format(appl.job.session.year, appl.job.session.term.code, appl.job.course.code.name, appl.job.course.number.name, appl.job.course.section.name))
                        return HttpResponseRedirect(request.POST.get('next'))
                    else:
                        messages.error(request, 'An error occurred while updating ta hours.')
                else:
                    messages.error(request, 'An error occurred while saving a status of an application.')
            else:
                errors = form.errors.get_json_data()
                messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        # Decline a job offer
        elif request.POST.get('decision') == 'decline':
            form = ApplicationStatusForm({
                'application': request.POST.get('application'),
                'assigned': ApplicationStatus.DECLINED,
                'assigned_hours': 0.0,
                'has_contract_read': True
            })
            if form.is_valid():
                appl = form.cleaned_data['application']
                if form.save():
                    appl.updated_at = datetime.now()
                    appl.save(update_fields=['updated_at'])

                    # Update new hours
                    new_hours = 0.0 - float(app.accepted.assigned_hours )
                    if adminApi.update_job_accumulated_ta_hours(appl.job.session.slug, appl.job.course.slug, new_hours):
                        messages.success(request, 'You declined the job offer - {0} {1}: {2} {3} {4}.'.format(appl.job.session.year, appl.job.session.term.code, appl.job.course.code.name, appl.job.course.number.name, appl.job.course.section.name))
                        return HttpResponseRedirect(request.POST.get('next'))
                    else:
                        messages.error(request, 'An error occurred while updating ta hours.')
                else:
                    messages.error(request, 'An error occurred while saving an status of an application.')
            else:
                errors = form.errors.get_json_data()
                messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return HttpResponseRedirect(request.get_full_path())
    else:
        adminApi.can_req_parameters_access(request, 'none', ['next'])

    return render(request, 'students/jobs/reaccept_application.html', {
        'loggedin_user': request.user,
        'app': app,
        'can_accept': userApi.add_confidentiality_validation(request.user),
        'job_offer_details': adminApi.get_job_offer_details(request.user, app, 'reassigned')
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_job(request, session_slug, job_slug):
    ''' Display job details '''
    request = userApi.has_user_access(request, Role.STUDENT)
    adminApi.can_req_parameters_access(request, 'student-job', ['next', 'p'])

    return render(request, 'students/jobs/show_job.html', {
        'loggedin_user': request.user,
        'job': adminApi.get_job_by_session_slug_job_slug(session_slug, job_slug)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def show_application(request, app_slug):
    ''' Display job details '''
    request = userApi.has_user_access(request, Role.STUDENT)
    adminApi.can_req_parameters_access(request, 'none', ['next'])

    return render(request, 'students/jobs/show_application.html', {
        'loggedin_user': request.user,
        'app': adminApi.get_application(app_slug, 'slug')
    })