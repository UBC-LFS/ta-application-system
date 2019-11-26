import os
from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404
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


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def index(request):
    ''' Index page of student's portal '''
    if request.user.is_impersonate:
        if not userApi.is_admin(request.session['loggedin_user'], 'dict'): raise PermissionDenied
        request.user.roles = userApi.get_user_roles(request.user)
    else:
        request.user.roles = request.session['loggedin_user']['roles']
    if 'Student' not in request.user.roles: raise PermissionDenied

    apps, total_accepted_assigned_hours = adminApi.get_applied_applications(request.user)
    return render(request, 'students/index.html', {
        'loggedin_user': request.user,
        'apps': apps,
        'total_accepted_assigned_hours': total_accepted_assigned_hours,
        'recent_apps': apps.filter( Q(created_at__year__gte=datetime.now().year) ),
        'favourites': adminApi.get_favourites(request.user)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_profile(request):
    ''' Display user profile '''
    if request.user.is_impersonate:
        if not userApi.is_admin(request.session['loggedin_user'], 'dict'): raise PermissionDenied
        request.user.roles = userApi.get_user_roles(request.user)
    else:
        request.user.roles = request.session['loggedin_user']['roles']
    if 'Student' not in request.user.roles: raise PermissionDenied

    request.user = userApi.add_resume(request.user)
    return render(request, 'students/profile/show_profile.html', {
        'loggedin_user': request.user,
        'form': ResumeForm(initial={ 'user': request.user })
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_profile(request):
    ''' Edit user's profile '''
    if request.user.is_impersonate:
        if not userApi.is_admin(request.session['loggedin_user'], 'dict'): raise PermissionDenied
        request.user.roles = userApi.get_user_roles(request.user)
    else:
        request.user.roles = request.session['loggedin_user']['roles']
    if 'Student' not in request.user.roles: raise PermissionDenied

    loggedin_user = request.user
    profile_degrees = loggedin_user.profile.degrees.all()
    profile_trainings = loggedin_user.profile.trainings.all()
    if request.method == 'POST':
        form = StudentProfileForm(request.POST, instance=loggedin_user.profile)
        if form.is_valid():
            data = form.cleaned_data
            updated_profile = form.save(commit=False)
            updated_profile.updated_at = datetime.now()
            form.save()

            if updated_profile:
                updated = userApi.update_student_profile_degrees_trainings(updated_profile, profile_degrees, profile_trainings, data)
                if updated:
                    messages.success(request, 'Success! {0} - profile updated'.format(loggedin_user.username))
                    return redirect('students:show_profile')
                else:
                    messages.error(request, 'An error occurred while degrees and trainings of a profile.')
            else:
                messages.error(request, 'An error occurred while updating student\'s profile.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return HttpResponseRedirect( reverse('students:edit_profile', args=[username]) )

    return render(request, 'students/profile/edit_profile.html', {
        'loggedin_user': loggedin_user,
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
    if request.user.is_impersonate:
        if not userApi.is_admin(request.session['loggedin_user'], 'dict'): raise PermissionDenied
        request.user.roles = userApi.get_user_roles(request.user)
    else:
        request.user.roles = request.session['loggedin_user']['roles']
    if 'Student' not in request.user.roles: raise PermissionDenied

    request.user = userApi.add_resume(request.user)
    if request.method == 'POST':
        if len(request.FILES) == 0:
            messages.error(request, 'An error occurred. Please select your resume, then try again.')
            return redirect('students:show_profile')

        if request.user.resume_filename:
            messages.error(request, 'An error occurred. Please remove your previous resume, then try again.')
            return redirect('students:show_profile')

        form = ResumeForm(request.POST, request.FILES)
        if form.is_valid():
            resume = form.save(commit=False)
            resume.uploaded = request.FILES.get('uploaded')
            resume.save()
            if resume:
                messages.success(request, 'Success! {0} - Resume uploaded'.format(request.user.get_full_name()))
            else:
                messages.error(request, 'An error occurred while saving a resume.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

    return redirect('students:show_profile')

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def download_resume(request, username, filename):
    ''' Download user's resume '''
    if not userApi.is_valid_user(request.user): raise PermissionDenied

    path = 'users/{0}/resume/{1}/'.format(username, filename)
    return serve(request, path, document_root=settings.MEDIA_ROOT)


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_resume(request):
    ''' Delete user's resume '''
    if request.user.is_impersonate:
        if not userApi.is_admin(request.session['loggedin_user'], 'dict'): raise PermissionDenied
        request.user.roles = userApi.get_user_roles(request.user)
    else:
        request.user.roles = request.session['loggedin_user']['roles']
    if 'Student' not in request.user.roles: raise PermissionDenied

    if request.method == 'POST':
        username = request.POST.get('user')
        deleted_resume = userApi.delete_user_resume(username)
        if deleted_resume:
            messages.success(request, 'Success! {0} - Resume deleted'.format(username))
        else:
            messages.error(request, 'An error occurred. Failed to delete your resume.')
    else:
        messages.error(request, 'An error occurred. Request is not POST.')

    return redirect('students:show_profile')


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_confidentiality(request):
    ''' Display user's confidentiality '''
    if request.user.is_impersonate:
        if not userApi.is_admin(request.session['loggedin_user'], 'dict'): raise PermissionDenied
        request.user.roles = userApi.get_user_roles(request.user)
    else:
        request.user.roles = request.session['loggedin_user']['roles']
    if 'Student' not in request.user.roles: raise PermissionDenied

    request.user = userApi.add_confidentiality(request.user)
    return render(request, 'students/profile/show_confidentiality.html', {
        'loggedin_user': request.user,
        #'user': userApi.get_user_with_confidentiality(loggedin_user.username)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def check_confidentiality(request):
    ''' Check whether an international student or not '''
    if request.user.is_impersonate:
        if not userApi.is_admin(request.session['loggedin_user'], 'dict'): raise PermissionDenied
        request.user.roles = userApi.get_user_roles(request.user)
    else:
        request.user.roles = request.session['loggedin_user']['roles']
    if 'Student' not in request.user.roles: raise PermissionDenied

    if request.method == 'POST':
        form = None
        confidentiality = userApi.has_user_confidentiality_created(request.user)
        if confidentiality:
            form = ConfidentialityCheckForm(request.POST, instance=request.user.confidentiality)
        else:
            form = ConfidentialityCheckForm(request.POST)

        if form.is_valid():
            confidentiality = form.save()
            if confidentiality:
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
    if request.user.is_impersonate:
        if not userApi.is_admin(request.session['loggedin_user'], 'dict'): raise PermissionDenied
        request.user.roles = userApi.get_user_roles(request.user)
    else:
        request.user.roles = request.session['loggedin_user']['roles']
    if 'Student' not in request.user.roles: raise PermissionDenied

    user = userApi.get_user(request.user.id)
    form = None
    if request.method == 'POST':
        if user.confidentiality.is_international == True:
            form = ConfidentialityInternationalForm(request.POST, request.FILES, instance=user.confidentiality)
        else:
            form = ConfidentialityNonInternationalForm(request.POST, request.FILES, instance=user.confidentiality)

        if form.is_valid():
            sin_file = request.FILES.get('sin')
            study_permit_file = request.FILES.get('study_permit')

            updated_confidentiality = form.save(commit=False)
            updated_confidentiality.created_at = datetime.now()
            updated_confidentiality.updated_at = datetime.now()

            updated_confidentiality.sin = sin_file
            updated_confidentiality.study_permit = study_permit_file

            updated_confidentiality.save()
            if updated_confidentiality:
                messages.success(request, 'Success! {0} - confidentiality submitted'.format(user.username))
                return redirect('students:show_confidentiality')
            else:
                messages.error(request, 'An error occurred while saving confidentiality.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return redirect('students:submit_confidentiality')

    else:
        if userApi.has_user_confidentiality_created(user):
            if bool(user.confidentiality.is_international):
                form = ConfidentialityInternationalForm(initial={ 'user': user })
            else:
                form = ConfidentialityNonInternationalForm(initial={ 'user': user })

    return render(request, 'students/profile/submit_confidentiality.html', {
        'loggedin_user': request.user,
        'form': form
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_confidentiality(request):
    ''' Edit user's confidentiality '''
    if request.user.is_impersonate:
        if not userApi.is_admin(request.session['loggedin_user'], 'dict'): raise PermissionDenied
        request.user.roles = userApi.get_user_roles(request.user)
    else:
        request.user.roles = request.session['loggedin_user']['roles']
    if 'Student' not in request.user.roles: raise PermissionDenied

    loggedin_user = request.user
    confidentiality = userApi.has_user_confidentiality_created(loggedin_user)
    sin_file = None
    study_permit_file = None
    if request.method == 'POST':
        form = ConfidentialityForm(request.POST, request.FILES, instance=request.user.confidentiality)
        if form.is_valid():
            data = form.cleaned_data
            user_id = request.POST.get('user')
            user = userApi.get_user(user_id)

            updated_confidentiality = form.save(commit=False)
            updated_confidentiality.updated_at = datetime.now()

            if data['is_international'] == None:
                messages.error(request, 'An error occurred. Please select your nationality.')
                return redirect('students:edit_confidentiality')

            # Check SIN and Study Permit
            sin_study_permit_errors = []
            if request.FILES.get('sin') and bool(user.confidentiality.sin):
                sin_study_permit_errors.append('SIN')
            if request.FILES.get('study_permit') and bool(user.confidentiality.study_permit):
                sin_study_permit_errors.append('Study Permit')

            if len(sin_study_permit_errors) > 0:
                msg = ' and '.join(sin_study_permit_errors)
                messages.error(request, 'An error occurred. Please delete your previous {0} information first, and then try again.'.format(msg))
                return redirect('students:edit_confidentiality')

            update_fields = []

            if data['is_international'] is not None:
                updated_confidentiality.is_international = data['is_international']
                update_fields.append('is_international')

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

            if not data['is_international']:
                updated_confidentiality.sin_expiry_date = None
                if 'sin_expiry_date' not in update_fields: update_fields.append('sin_expiry_date')
                updated_confidentiality.study_permit_expiry_date = None
                if 'study_permit_expiry_date' not in update_fields: update_fields.append('study_permit_expiry_date')

                if request.FILES.get('study_permit') or data['study_permit']:
                    messages.error(request, 'An error occurred. If you are a Canadian Citizen or Permanent Resident, you won\'t need to update your Study Permit. If you have your Study Permit, please delete it, and then try it again.')
                    return redirect('students:edit_confidentiality')

            updated_confidentiality.save(update_fields=update_fields)

            if updated_confidentiality:
                messages.success(request, 'Success! {0} - confidentiality updated'.format(loggedin_user.username))
                return redirect('students:show_confidentiality')
            else:
                messages.error(request, 'An error occurred while updating confidentiality.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

    else:
        if userApi.has_user_confidentiality_created(loggedin_user) and bool(loggedin_user.confidentiality.sin):
            sin_file = os.path.basename(loggedin_user.confidentiality.sin.name)

        if userApi.has_user_confidentiality_created(loggedin_user) and bool(loggedin_user.confidentiality.study_permit):
            study_permit_file = os.path.basename(loggedin_user.confidentiality.study_permit.name)


    return render(request, 'students/profile/edit_confidentiality.html', {
        'loggedin_user': loggedin_user,
        'sin_file': sin_file,
        'study_permit_file': study_permit_file,
        'form': ConfidentialityForm(data=None, instance=confidentiality, initial={
            'user': loggedin_user
        })
    })

#@login_required(login_url=settings.LOGIN_URL)
#@cache_control(no_cache=True, must_revalidate=True, no_store=True)
#@require_http_methods(['GET'])
def download_sin(request, username, filename):
    ''' '''
    #if not userApi.is_valid_user(request.user): raise PermissionDenied
    path = 'users/{0}/sin/{1}/'.format(username, filename)
    return serve(request, path, document_root=settings.MEDIA_ROOT)

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_sin(request):
    ''' Delete a SIN '''
    if request.user.is_impersonate:
        if not userApi.is_admin(request.session['loggedin_user'], 'dict'): raise PermissionDenied
        request.user.roles = userApi.get_user_roles(request.user)
    else:
        request.user.roles = request.session['loggedin_user']['roles']
    if 'Student' not in request.user.roles: raise PermissionDenied

    if request.method == 'POST':
        username = request.POST.get('user')
        deleted_sin = userApi.delete_user_sin(username)
        if deleted_sin:
            messages.success(request, 'Success! {0} - SIN deleted'.format(username))
        else:
            messages.error(request, 'An error occurred while deleting a SIN. Please try again.')

    return redirect('students:edit_confidentiality')


#@login_required(login_url=settings.LOGIN_URL)
#@cache_control(no_cache=True, must_revalidate=True, no_store=True)
#@require_http_methods(['GET'])
def download_study_permit(request, username, filename):
    ''' '''
    #if not userApi.is_valid_user(request.user): raise PermissionDenied
    path = 'users/{0}/study_permit/{1}/'.format(username, filename)
    return serve(request, path, document_root=settings.MEDIA_ROOT)


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_study_permit(request):
    ''' '''
    if request.user.is_impersonate:
        if not userApi.is_admin(request.session['loggedin_user'], 'dict'): raise PermissionDenied
        request.user.roles = userApi.get_user_roles(request.user)
    else:
        request.user.roles = request.session['loggedin_user']['roles']
    if 'Student' not in request.user.roles: raise PermissionDenied

    if request.method == 'POST':
        username = request.POST.get('user')
        deleted_study_permit = userApi.delete_user_study_permit(username)
        if deleted_study_permit:
            messages.success(request, 'Success! {0} - Study Permit deleted'.format(username))
        else:
            messages.error(request, 'An error occurred while deleting a study permit. Please try again.')

    return redirect('students:edit_confidentiality')



# Jobs


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def explore_jobs(request):
    ''' Display all lists of session terms '''
    if request.user.is_impersonate:
        if not userApi.is_admin(request.session['loggedin_user'], 'dict'): raise PermissionDenied
        request.user.roles = userApi.get_user_roles(request.user)
    else:
        request.user.roles = request.session['loggedin_user']['roles']
    if 'Student' not in request.user.roles: raise PermissionDenied

    return render(request, 'students/jobs/explore_jobs.html', {
        'loggedin_user': request.user,
        'visible_current_sessions': adminApi.get_visible_current_sessions(),
        'favourites': adminApi.get_favourites(request.user)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def favourite_jobs(request):
    ''' Display all lists of session terms '''
    if request.user.is_impersonate:
        if not userApi.is_admin(request.session['loggedin_user'], 'dict'): raise PermissionDenied
        request.user.roles = userApi.get_user_roles(request.user)
    else:
        request.user.roles = request.session['loggedin_user']['roles']
    if 'Student' not in request.user.roles: raise PermissionDenied

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

        return redirect('students:favourite_jobs')

    return render(request, 'students/jobs/favourite_jobs.html', {
        'loggedin_user': request.user,
        'favourites': adminApi.get_favourites(request.user)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def available_jobs(request, session_slug):
    ''' Display jobs available to apply '''
    if request.user.is_impersonate:
        if not userApi.is_admin(request.session['loggedin_user'], 'dict'): raise PermissionDenied
        request.user.roles = userApi.get_user_roles(request.user)
    else:
        request.user.roles = request.session['loggedin_user']['roles']
    if 'Student' not in request.user.roles: raise PermissionDenied

    year_q = request.GET.get('year')
    term_q = request.GET.get('term')
    code_q = request.GET.get('code')
    number_q = request.GET.get('number')
    section_q = request.GET.get('section')
    instructor_first_name_q = request.GET.get('instructor_first_name')
    instructor_last_name_q = request.GET.get('instructor_last_name')
    exclude_applied_jobs_q = request.GET.get('exclude_applied_jobs')

    job_list = adminApi.get_jobs_session(session_slug)
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
    if exclude_applied_jobs_q == '1':
        job_list = job_list.exclude(application__applicant__id=request.user.id)

    page = request.GET.get('page', 1)
    paginator = Paginator(job_list, settings.PAGE_SIZE)

    try:
        jobs = paginator.page(page)
    except PageNotAnInteger:
        jobs = paginator.page(1)
    except EmptyPage:
        jobs = paginator.page(paginator.num_pages)

    return render(request, 'students/jobs/available_jobs.html', {
        'loggedin_user': request.user,
        'session_slug': session_slug,
        'jobs': adminApi.add_applied_favourite_jobs(request.user, jobs)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def apply_job(request, session_slug, job_slug):
    ''' Students can apply for each job '''
    if request.user.is_impersonate:
        if not userApi.is_admin(request.session['loggedin_user'], 'dict'): raise PermissionDenied
        request.user.roles = userApi.get_user_roles(request.user)
    else:
        request.user.roles = request.session['loggedin_user']['roles']
    if 'Student' not in request.user.roles: raise PermissionDenied

    job = adminApi.get_job_by_session_slug_job_slug(session_slug, job_slug)
    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            app = form.save()
            if app:
                app_status = adminApi.create_application_status(app)
                if app_status:
                    messages.success(request, 'Success! {0} {1} - {2} {3} {4} applied'.format(job.session.year, job.session.term.code, job.course.code.name, job.course.number.name, job.course.section.name))
                    return HttpResponseRedirect( reverse('students:available_jobs', args=[session_slug]) )
                else:
                    messages.error(request, 'An error occurred while creating a status of an application.')
            else:
                messages.error(request, 'An error occurred while saving an application.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return HttpResponseRedirect( reverse('students:apply_job', args=[session_slug, job_slug]) )

    return render(request, 'students/jobs/apply_job.html', {
        'loggedin_user': request.user,
        'job': adminApi.add_favourite_job(request.user, job),
        'has_applied_job': adminApi.has_applied_job(session_slug, job_slug, request.user),
        'form': ApplicationForm(initial={ 'applicant': request.user.id, 'job': job.id }),
        'applied_jobs': adminApi.get_jobs_applied_by_student(request.user).order_by('-created_at')[:10]
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def select_favourite_job(request, session_slug, job_slug):
    ''' '''
    if request.user.is_impersonate:
        if not userApi.is_admin(request.session['loggedin_user'], 'dict'): raise PermissionDenied
        request.user.roles = userApi.get_user_roles(request.user)
    else:
        request.user.roles = request.session['loggedin_user']['roles']
    if 'Student' not in request.user.roles: raise PermissionDenied

    if request.method == 'POST':
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

        return HttpResponseRedirect( reverse('students:apply_job', args=[session_slug, job_slug]) )


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def history_jobs(request):
    ''' Display History of Jobs and total accepted assigned hours '''
    if request.user.is_impersonate:
        if not userApi.is_admin(request.session['loggedin_user'], 'dict'): raise PermissionDenied
        request.user.roles = userApi.get_user_roles(request.user)
    else:
        request.user.roles = request.session['loggedin_user']['roles']
    if 'Student' not in request.user.roles: raise PermissionDenied

    apps, total_accepted_assigned_hours = adminApi.get_applications_with_status(request.user)
    return render(request, 'students/jobs/history_jobs.html', {
        'loggedin_user': request.user,
        'apps': apps,
        'total_accepted_assigned_hours': total_accepted_assigned_hours
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def cancel_job(request, session_slug, job_slug):
    ''' Cancel an accepted job '''
    if request.user.is_impersonate:
        if not userApi.is_admin(request.session['loggedin_user'], 'dict'): raise PermissionDenied
        request.user.roles = userApi.get_user_roles(request.user)
    else:
        request.user.roles = request.session['loggedin_user']['roles']
    if 'Student' not in request.user.roles: raise PermissionDenied

    job = adminApi.get_job_by_session_slug_job_slug(session_slug, job_slug)
    app = adminApi.get_application_with_status_by_user(request.user, job, ApplicationStatus.ACCEPTED)

    if request.method == 'POST':
        app_id = request.POST.get('application')
        assigned_hours = request.POST.get('assigned_hours')
        form = ApplicationStatusReassignForm({ 'application': app_id, 'assigned': ApplicationStatus.CANCELLED, 'assigned_hours': assigned_hours, 'parent_id': app.status.id })
        if form.is_valid():
            cancelled_status = form.save()
            if cancelled_status:
                messages.success(request, 'Success! Application of {0} {1} - {2} {3} {4} cancelled.'.format(job.session.year, job.session.term.code, job.course.code.name, job.course.number.name, job.course.section.name))
                return redirect('students:history_jobs')
            else:
                messages.error(request, 'An error occurred while saving application status.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return HttpResponseRedirect( reverse('students:cancel_job', args=[session_slug, job_slug]) )

    return render(request, 'students/jobs/cancel_job.html', {
        'loggedin_user': request.user,
        'app': app
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def accept_decline_job(request, session_slug, job_slug):
    ''' Display a job to select accept or decline a job offer '''
    if request.user.is_impersonate:
        if not userApi.is_admin(request.session['loggedin_user'], 'dict'): raise PermissionDenied
        request.user.roles = userApi.get_user_roles(request.user)
    else:
        request.user.roles = request.session['loggedin_user']['roles']
    if 'Student' not in request.user.roles: raise PermissionDenied

    apps, total_assigned_hours = adminApi.get_applications_with_status_by_user(request.user, ApplicationStatus.OFFERED)

    # Find an application with session_slug and job_slug
    app = None
    for app in apps:
        if app.job.session.slug == session_slug and app.job.course.slug == job_slug:
            app = app
            break

    if not app: raise Http404

    return render(request, 'students/jobs/accept_decline_job.html', {
        'loggedin_user': request.user,
        'app': app
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def accept_offer(request, session_slug, job_slug):
    ''' Students accept a job offer '''
    if request.user.is_impersonate:
        if not userApi.is_admin(request.session['loggedin_user'], 'dict'): raise PermissionDenied
        request.user.roles = userApi.get_user_roles(request.user)
    else:
        request.user.roles = request.session['loggedin_user']['roles']
    if 'Student' not in request.user.roles: raise PermissionDenied

    if request.method == 'POST':
        app_id = request.POST.get('application')
        assigned_hours = request.POST.get('assigned_hours')
        assigned = ApplicationStatus.ACCEPTED
        form = ApplicationStatusForm({ 'application': app_id, 'assigned': assigned, 'assigned_hours': assigned_hours })
        if form.is_valid():
            status = form.save()
            if status:
                app = adminApi.get_application(app_id)
                updated = adminApi.update_job_accumulated_ta_hours(session_slug, job_slug, assigned_hours)
                if updated:
                    messages.success(request, 'Success! You accepted the job offer - {0} {1}: {2} {3} {4} '.format(app.job.session.year, app.job.session.term.code, app.job.course.code.name, app.job.course.number.name, app.job.course.section.name))
                else:
                    messages.error(request, 'An error occurred while updating ta hours.')
            else:
                messages.error(request, 'An error occurred while saving a status of an application.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

    return redirect('students:history_jobs')

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def decline_offer(request, session_slug, job_slug):
    ''' Students decline job offers '''
    if request.user.is_impersonate:
        if not userApi.is_admin(request.session['loggedin_user'], 'dict'): raise PermissionDenied
        request.user.roles = userApi.get_user_roles(request.user)
    else:
        request.user.roles = request.session['loggedin_user']['roles']
    if 'Student' not in request.user.roles: raise PermissionDenied

    if request.method == 'POST':
        app_id = request.POST.get('application')
        assigned = ApplicationStatus.DECLINED
        form = ApplicationStatusForm({ 'application': app_id, 'assigned': assigned, 'assigned_hours': 0.0 })
        if form.is_valid():
            status = form.save()
            if status:
                app = adminApi.get_application(app_id)
                messages.success(request, 'Success! You declined the job offer - {0} {1}: {2} {3} {4} '.format(app.job.session.year, app.job.session.term.code, app.job.course.code.name, app.job.course.number.name, app.job.course.section.name))
            else:
                messages.error(request, 'An error occurred while saving an status of an application.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

    return redirect('students:history_jobs')

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def show_job(request, session_slug, job_slug):
    ''' Display job details '''
    if request.user.is_impersonate:
        if not userApi.is_admin(request.session['loggedin_user'], 'dict'): raise PermissionDenied
        request.user.roles = userApi.get_user_roles(request.user)
    else:
        request.user.roles = request.session['loggedin_user']['roles']
    if 'Student' not in request.user.roles: raise PermissionDenied

    return render(request, 'students/jobs/show_job.html', {
        'loggedin_user': request.user,
        'job': adminApi.get_job_by_session_slug_job_slug(session_slug, job_slug)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def show_application(request, app_slug):
    ''' Display job details '''
    if request.user.is_impersonate:
        if not userApi.is_admin(request.session['loggedin_user'], 'dict'): raise PermissionDenied
        request.user.roles = userApi.get_user_roles(request.user)
    else:
        request.user.roles = request.session['loggedin_user']['roles']
    if 'Student' not in request.user.roles: raise PermissionDenied

    return render(request, 'students/jobs/show_application.html', {
        'loggedin_user': request.user,
        'app': adminApi.get_application(app_slug, 'slug')
    })
