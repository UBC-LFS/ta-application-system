import os
from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_control
from django.views.static import serve
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from users.forms import *
from users import api as userApi
from administrators.forms import *
from administrators import api as adminApi

from datetime import datetime

IMPORTANT_MESSAGE = '<strong>Important:</strong> Please complete all items in your Additional Information tab. If you have not already done so, also upload your Resume. <br />When these tabs are complete, you will be able to Explore Jobs when the TA Application is open.<br />No official TA offer can be sent to you unless these two sections are completed.  Thanks.'


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def index(request):
    ''' Index page of student's portal '''
    request = userApi.has_user_access(request, 'Student')

    can_apply = userApi.can_apply(request.user)
    if can_apply == False:
        return HttpResponseRedirect( reverse('students:show_profile') + '?next=' + reverse('students:index') + '&p=Home&t=basic' )

    apps = request.user.application_set.all()
    return render(request, 'students/index.html', {
        'loggedin_user': userApi.add_avatar(request.user),
        'apps': apps,
        'total_assigned_hours': adminApi.get_total_assigned_hours(apps, ['accepted']),
        'recent_apps': apps.filter( Q(created_at__year__gte=datetime.now().year) ).order_by('-created_at'),
        'favourites': adminApi.get_favourites(request.user)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_profile(request):
    ''' Display user profile '''
    request = userApi.has_user_access(request, 'Student')
    adminApi.can_req_parameters_access(request, 'student', ['next', 'p','t'])

    loggedin_user = userApi.add_resume(request.user)

    can_apply = userApi.can_apply(request.user)
    if can_apply == False:
        messages.warning(request, IMPORTANT_MESSAGE)

    return render(request, 'students/profile/show_profile.html', {
        'loggedin_user': userApi.add_avatar(loggedin_user),
        'form': ResumeForm(initial={ 'user': loggedin_user }),
        'current_tab': request.GET.get('t'),
        'can_apply': can_apply
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_profile(request):
    ''' Edit user's profile '''
    request = userApi.has_user_access(request, 'Student')

    PROGRAM_OTHERS = userApi.get_program_others_id()
    if PROGRAM_OTHERS == None:
        raise PermissionDenied

    loggedin_user = request.user
    profile_degrees = loggedin_user.profile.degrees.all()
    profile_trainings = loggedin_user.profile.trainings.all()
    if request.method == 'POST':
        form = StudentProfileForm(request.POST, instance=loggedin_user.profile)
        if form.is_valid():
            data = form.cleaned_data

            errors = []
            if data['program'].id == PROGRAM_OTHERS and bool(data['program_others']) == False:
                errors.append('Please indicate the name of your program if you select "Other" in Current Program.')

            if data['graduation_date'] == None:
                errors.append('Anticipated Graduation Date: This field is required.')

            if len(data['trainings']) != len(userApi.get_trainings()):
                errors.append('Training: You must check all fields to proceed.')

            if len(errors) > 0:
                messages.error(request, 'An error occurred. {0}'.format(' '.join(errors)))
                return redirect('students:edit_profile')

            updated_profile = form.save(commit=False)
            updated_profile.updated_at = datetime.now()
            updated_profile.save()
            if updated_profile:
                updated = userApi.update_student_profile_degrees_trainings(updated_profile, profile_degrees, profile_trainings, data)
                if updated:
                    messages.success(request, 'Success! {0} - additional information updated'.format(loggedin_user.username))
                    return HttpResponseRedirect( reverse('students:show_profile') + '?next=' + reverse('students:edit_profile') + '&p=Edit Profile&t=additional' )
                else:
                    messages.error(request, 'An error occurred while degrees and trainings of a profile.')
            else:
                messages.error(request, "An error occurred while updating student's profile.")
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return redirect('students:edit_profile')

    return render(request, 'students/profile/edit_profile.html', {
        'loggedin_user': userApi.add_avatar(loggedin_user),
        'form': StudentProfileForm(data=None, instance=loggedin_user.profile, initial={
            'degrees': profile_degrees,
            'trainings': profile_trainings
        })
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def upload_resume(request):
    ''' Upload user's resume '''
    request = userApi.has_user_access(request, 'Student')
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
    request = userApi.has_user_access(request, 'Student')
    adminApi.can_req_parameters_access(request, 'student', ['next', 'p'])

    if request.method == 'POST':
        username = request.POST.get('user')
        deleted_resume = userApi.delete_user_resume(username)
        if deleted_resume:
            messages.success(request, 'Success! {0} - Resume deleted'.format(username))
        else:
            messages.error(request, 'An error occurred. Failed to delete your resume.')
    else:
        messages.error(request, 'An error occurred. Request is not POST.')

    return HttpResponseRedirect( reverse('students:show_profile') + '?next=' + request.GET.get('next') + '&p=' + request.GET.get('p') + '&t=resume' )


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_confidentiality(request):
    ''' Display user's confidentiality '''
    request = userApi.has_user_access(request, 'Student')

    template = 'choose'
    if userApi.has_user_confidentiality_created(request.user) and request.user.confidentiality and request.user.confidentiality.nationality != None:
        template = 'detail'

    user = userApi.add_confidentiality_given_list(request.user, ['sin', 'study_permit'])
    user = userApi.add_avatar(user)
    return render(request, 'students/profile/show_confidentiality.html', {
        'loggedin_user': userApi.add_personal_data_form(user),
        'template': template
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def check_confidentiality(request):
    ''' Check whether an international student or not '''
    request = userApi.has_user_access(request, 'Student')

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
    request = userApi.has_user_access(request, 'Student')

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

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_confidentiality(request):
    ''' Edit user's confidentiality '''
    request = userApi.has_user_access(request, 'Student')

    loggedin_user = request.user
    form = None
    sin_file = None
    study_permit_file = None
    personal_data_form_file = None
    can_delete = False

    confidentiality = userApi.has_user_confidentiality_created(loggedin_user)
    if request.method == 'POST':
        is_new_employee = request.POST.get('is_new_employee')
        employee_number = request.POST.get('employee_number')

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

            if request.FILES.get('personal_data_form') is not None:
                updated_confidentiality.personal_data_form = request.FILES.get('personal_data_form')
                update_fields.append('personal_data_form')

            updated_confidentiality.save(update_fields=update_fields)

            if updated_confidentiality:
                messages.success(request, 'Success! Confidential information of {0} updated'.format(loggedin_user.get_full_name()))
                return redirect('students:show_confidentiality')
            else:
                messages.error(request, 'An error occurred while updating confidential information.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return redirect('students:edit_confidentiality')

    else:
        if confidentiality:
            if bool(confidentiality.employee_number):
                can_delete = True
            if bool(confidentiality.sin):
                sin_file = os.path.basename(confidentiality.sin.name)
                can_delete = True

            if bool(confidentiality.study_permit):
                study_permit_file = os.path.basename(confidentiality.study_permit.name)
                can_delete = True

            if bool(confidentiality.personal_data_form):
                personal_data_form_file = os.path.basename(confidentiality.personal_data_form.name)
                can_delete = True

            if confidentiality.nationality == '0':
                form = ConfidentialityDomesticForm(data=None, instance=confidentiality, initial={ 'user': loggedin_user })
            else:
                form = ConfidentialityInternationalForm(data=None, instance=confidentiality, initial={ 'user': loggedin_user })
                if bool(confidentiality.sin_expiry_date):
                    can_delete = True
                if bool(confidentiality.study_permit_expiry_date):
                    can_delete = True

    return render(request, 'students/profile/edit_confidentiality.html', {
        'loggedin_user': userApi.add_avatar(loggedin_user),
        'sin_file': sin_file,
        'study_permit_file': study_permit_file,
        'personal_data_form_file': personal_data_form_file,
        'form': form,
        'can_delete': can_delete,
        'confidentiality': confidentiality
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_confidential_information(request):
    ''' Delete a confidential information '''
    request = userApi.has_user_access(request, 'Student')

    if request.method == 'POST':
        data = []
        if request.POST.get('employee_number') != None: data.append('employee_number')
        if request.POST.get('sin') != None: data.append('sin')
        if request.POST.get('sin_expiry_date') != None: data.append('sin_expiry_date')
        if request.POST.get('study_permit') != None: data.append('study_permit')
        if request.POST.get('study_permit_expiry_date') != None: data.append('study_permit_expiry_date')
        if request.POST.get('personal_data_form') != None: data.append('personal_data_form')

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


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def explore_jobs(request):
    ''' Display all lists of session terms '''
    request = userApi.has_user_access(request, 'Student')

    can_apply = userApi.can_apply(request.user)
    if can_apply == False:
        messages.warning(request, IMPORTANT_MESSAGE)

    sessions = adminApi.get_sessions()
    return render(request, 'students/jobs/explore_jobs.html', {
        'loggedin_user': userApi.add_avatar(request.user),
        'visible_current_sessions': sessions.filter( Q(is_visible=True) & Q(is_archived=False) ),
        'favourites': adminApi.get_favourites(request.user),
        'can_apply': can_apply
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def favourite_jobs(request):
    ''' Display all lists of session terms '''
    request = userApi.has_user_access(request, 'Student')

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
            favourite_list = favourite_list.filter(job__session__term__code__icontains=term_q)
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


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def available_jobs(request, session_slug):
    ''' Display jobs available to apply '''
    request = userApi.has_user_access(request, 'Student')

    can_apply = userApi.can_apply(request.user)
    if can_apply == False:
        raise PermissionDenied

    adminApi.available_session(session_slug)

    code_q = request.GET.get('code')
    number_q = request.GET.get('number')
    section_q = request.GET.get('section')
    instructor_first_name_q = request.GET.get('instructor_first_name')
    instructor_last_name_q = request.GET.get('instructor_last_name')
    exclude_applied_jobs_q = request.GET.get('exclude_applied_jobs')
    exclude_inactive_jobs_q = request.GET.get('exclude_inactive_jobs')

    job_list = adminApi.get_jobs().filter(session__slug=session_slug)
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
        'session_slug': session_slug,
        'jobs': adminApi.add_applied_favourite_jobs(request.user, jobs),
        'total_jobs': len(job_list),
        'can_apply': can_apply,
        'new_next': adminApi.build_new_next(request)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def apply_job(request, session_slug, job_slug):
    ''' Students can apply for each job '''
    request = userApi.has_user_access(request, 'Student')
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

    if session.is_visible == False or session.is_archived == True or job.is_active == False or can_apply == False or UNDERGRADUATE_STUDENT == None:
        raise PermissionDenied

    if request.method == 'POST':

        # Check whether a next url is valid or not
        adminApi.can_req_parameters_access(request, 'none', ['next'], 'POST')

        if request.user.profile.status is not None and request.user.profile.status.id != UNDERGRADUATE_STUDENT and request.POST.get('supervisor_approval') == None:
            messages.error(request, 'An error occurred. You must check "Yes" in the box under "Supervisor Approval" if you are a graduate student. Undergraduate students should leave this box blank.')
            return HttpResponseRedirect(request.get_full_path())

        if request.POST.get('availability') == None:
            messages.error(request, 'An error occurred. You must check "I understand" in the box under "Availability requirements". Please read through it.')
            return HttpResponseRedirect(request.get_full_path())

        if request.POST.get('how_qualified') == '0' or request.POST.get('how_interested') == '0':
            messages.error(request, 'An error occurred. Please select both "How qualifed are you?" and "How interested are you?".')
            return HttpResponseRedirect(request.get_full_path())

        form = ApplicationForm(request.POST)
        if form.is_valid():
            app = form.save()
            if app:
                app_status = adminApi.create_application_status(app)
                if app_status:
                    messages.success(request, 'Success! {0} {1} - {2} {3} {4} applied'.format(job.session.year, job.session.term.code, job.course.code.name, job.course.number.name, job.course.section.name))
                    return HttpResponseRedirect(request.POST.get('next'))
                else:
                    messages.error(request, 'An error occurred while creating a status of an application.')
            else:
                messages.error(request, 'An error occurred while saving an application.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return HttpResponseRedirect(request.get_full_path())

    return render(request, 'students/jobs/apply_job.html', {
        'loggedin_user': request.user,
        'job': adminApi.add_favourite_job(request.user, job),
        'has_applied_job': job.application_set.filter(applicant__id=request.user.id).exists(),
        'form': ApplicationForm(initial={ 'applicant': request.user.id, 'job': job.id }),
        'next':next
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def select_favourite_job(request, session_slug, job_slug):
    ''' Select favourite jobs '''
    request = userApi.has_user_access(request, 'Student')

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
    request = userApi.has_user_access(request, 'Student')

    year_q = request.GET.get('year')
    term_q = request.GET.get('term')
    code_q = request.GET.get('code')
    number_q = request.GET.get('number')
    section_q = request.GET.get('section')

    app_list = request.user.application_set.all()
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

    page = request.GET.get('page', 1)
    paginator = Paginator(app_list, settings.PAGE_SIZE)

    try:
        apps = paginator.page(page)
    except PageNotAnInteger:
        apps = paginator.page(1)
    except EmptyPage:
        apps = paginator.page(paginator.num_pages)

    return render(request, 'students/jobs/history_jobs.html', {
        'loggedin_user': request.user,
        'apps': adminApi.add_applications_with_latest_status(apps),
        'total_apps': len(app_list)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def terminate_job(request, session_slug, job_slug):
    ''' Cancel/terminate an accepted job '''
    request = userApi.has_user_access(request, 'Student')
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
    request = userApi.has_user_access(request, 'Student')
    adminApi.can_req_parameters_access(request, 'none', ['next'])

    apps = request.user.application_set.all()
    apps = apps.filter( Q(job__session__slug=session_slug) & Q(job__course__slug=job_slug) )
    if len(apps) == 0: raise Http404

    app = adminApi.add_app_info_into_application(apps.first(), ['offered', 'accepted', 'declined'])
    if app.job.session.is_archived == True or app.offered is None:
        raise PermissionDenied

    #can_accept_or_decline = userApi.add_confidentiality_validation(request.user)
    #if can_accept_or_decline['status'] == False:
    #    raise PermissionDenied

    return render(request, 'students/jobs/accept_decline_job.html', {
        'loggedin_user': request.user,
        'app': app,
        'can_accept': userApi.add_confidentiality_validation(request.user)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def make_decision(request, session_slug, job_slug):
    ''' Students accept a job offer '''
    request = userApi.has_user_access(request, 'Student')
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

                    if adminApi.update_job_accumulated_ta_hours(session_slug, job_slug, float(assigned_hours)):
                        messages.success(request, 'Success! You accepted the job offer - {0} {1}: {2} {3} {4} '.format(app.job.session.year, app.job.session.term.code, app.job.course.code.name, app.job.course.number.name, app.job.course.section.name))
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
    request = userApi.has_user_access(request, 'Student')

    app = adminApi.get_application(app_slug, 'slug')
    app = adminApi.add_app_info_into_application(app, ['accepted','declined'])
    if app.job.session.is_archived == True or app.is_declined_reassigned != True:
        raise PermissionDenied

    #can_accept_or_decline = userApi.add_confidentiality_validation(request.user)
    #if can_accept_or_decline['status'] == False:
    #    raise PermissionDenied

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
        'can_accept': userApi.add_confidentiality_validation(request.user)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_job(request, session_slug, job_slug):
    ''' Display job details '''
    request = userApi.has_user_access(request, 'Student')
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
    request = userApi.has_user_access(request, 'Student')
    adminApi.can_req_parameters_access(request, 'none', ['next'])

    return render(request, 'students/jobs/show_application.html', {
        'loggedin_user': request.user,
        'app': adminApi.get_application(app_slug, 'slug')
    })
