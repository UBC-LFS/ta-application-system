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
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    return render(request, 'students/index.html', {
        'loggedin_user': loggedin_user
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_profile(request):
    ''' Display user profile '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    return render(request, 'students/profile/show_profile.html', {
        'loggedin_user': loggedin_user,
        'user': userApi.get_user_by_username_with_resume(loggedin_user.username),
        'form': ResumeForm(initial={ 'user': loggedin_user })
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_profile(request):
    ''' Edit user's profile '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

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
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    user = userApi.get_user_by_username_with_resume(loggedin_user.username)
    if request.method == 'POST':
        form = None
        old_resume = None
        if user.resume_file:
            old_resume = user.resume.file
            form = ResumeForm(request.POST, request.FILES, instance=user.resume)
        else:
            form = ResumeForm(request.POST, request.FILES)

        if form.is_valid():
            resume = form.save(commit=False)
            if user.resume_file and old_resume != None and len(old_resume.name) > 0:
                deleted_resume = userApi.delete_user_resume(user)
                if not deleted_resume:
                    messages.warning(request, 'Warning! Resume is not deleted')

            resume.file = request.FILES.get('file')
            resume.created_at = datetime.now()
            resume.save()
            if resume:
                messages.success(request, 'Success! {0} - Resume uploaded'.format(user.username))
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
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

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
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    return render(request, 'students/profile/show_confidentiality.html', {
        'loggedin_user': loggedin_user,
        'user': userApi.get_user_with_data(loggedin_user.id)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def check_confidentiality(request):
    ''' Check whether an international student or not '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    if request.method == 'POST':
        form = None
        confidentiality = userApi.has_user_confidentiality_created(loggedin_user)
        if confidentiality:
            form = ConfidentialityCheckForm(request.POST, instance=loggedin_user.confidentiality)
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

    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

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

    else:
        if userApi.has_user_confidentiality_created(user):
            if bool(user.confidentiality.is_international):
                form = ConfidentialityInternationalForm(initial={ 'user': user })
            else:
                form = ConfidentialityNonInternationalForm(initial={ 'user': user })

    return render(request, 'students/profile/submit_confidentiality.html', {
        'loggedin_user': loggedin_user,
        'user': user,
        'form': form
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_confidentiality(request):
    ''' Edit user's confidentiality '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    confidentiality = userApi.has_user_confidentiality_created(loggedin_user)
    sin_file = None
    study_permit_file = None
    if request.method == 'POST':
        form = ConfidentialityForm(request.POST, request.FILES, instance=loggedin_user.confidentiality)
        if form.is_valid():
            print('post ', request.POST)
            data = form.cleaned_data            
            print('data ', data)

            user_id = request.POST.get('user')
            user = userApi.get_user(user_id)

            updated_confidentiality = userApi.updated_confidentiality(user, form.cleaned_data)
            


            """is_international = request.POST.get('is_international')
            employee_number = request.POST.get('employee_number')
            
            sin_file = request.FILES.get('sin')
            sin_expiry_date = data['sin_expiry_date']

            study_permit_file = request.FILES.get('study_permit')
            study_permit_expiry_date = data['study_permit_expiry_date']

            print('user', user)
            print('is_international', is_international)
            print('employee_number', employee_number)
            print('sin_file', sin_file)
            print('sin_expiry_date', sin_expiry_date)
            print('study_permit_file', study_permit_file)
            print('study_permit_expiry_date', study_permit_expiry_date)"""



            #updated_confidentiality = form.save(commit=False)
            #updated_confidentiality.updated_at = datetime.now()

            #if is_international:
            #    study_permit_file = request.FILES.get('study_permit')   
            #else:
            #    userApi.delete_user_study_permit(loggedin_user)

            """
            if new_sin:
                if bool(old_sin):
                    deleted_sin_file = userApi.delete_user_sin(loggedin_user)
                    if not deleted_sin_file:
                        messages.warning(request, 'Warning! Previous SIN file was not deleted')
                loggedin_user.confidentiality.sin = new_sin

            if new_study_permit:
                if bool(old_study_permit):
                    deleted_study_permit_file = userApi.delete_user_study_permit(loggedin_user)
                    if not deleted_study_permit_file:
                        messages.warning(request, 'Warning! Previous study permit file was not deleted')
                loggedin_user.confidentiality.study_permit = new_study_permit
            """

            #updated_confidentiality.save()
            #print(updated_confidentiality)

            if updated_confidentiality:
                messages.success(request, 'Success! {0} - confidentiality updated'.format(loggedin_user.username))
                return redirect('students:show_confidentiality')
            else:
                messages.error(request, 'An error occurred while updating confidentiality.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

    else:
        if bool(loggedin_user.confidentiality.sin):
            sin_file = os.path.basename(loggedin_user.confidentiality.sin.name)

        if bool(loggedin_user.confidentiality.study_permit):
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
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    if request.method == 'POST':
        username = request.POST.get('user')
        deleted_sin = userApi.delete_user_sin(username)
        if deleted_sin:
            messages.success(request, 'Success! {0} - SIN deleted'.format(username))
        else:
            messages.error(request, 'An error occurred while deleting a SIN.')

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
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    if request.method == 'POST':
        username = request.POST.get('user')
        deleted_study_permit = userApi.delete_user_study_permit(username)
        if deleted_study_permit:
            messages.success(request, 'Success! {0} - Study Permit deleted'.format(username))
        else:
            messages.error(request, 'An error occurred while deleting a study permit.')

    return redirect('students:edit_confidentiality')



# Jobs


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def explore_jobs(request):
    ''' Display all lists of session terms '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    return render(request, 'students/jobs/explore_jobs.html', {
        'loggedin_user': loggedin_user,
        'visible_current_sessions': adminApi.get_visible_current_sessions(),
        'applied_jobs': adminApi.get_jobs_applied_by_student(loggedin_user).order_by('-created_at')[:10]
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def available_jobs(request, session_slug):
    ''' Display jobs available to apply '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    return render(request, 'students/jobs/available_jobs.html', {
        'loggedin_user': loggedin_user,
        'session': adminApi.get_session_by_slug(session_slug),
        'jobs': adminApi.get_available_jobs_to_apply(loggedin_user, session_slug)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def apply_job(request, session_slug, job_slug):
    ''' Students can apply for each job '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

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
        'loggedin_user': loggedin_user,
        'job': job,
        'has_applied_job': adminApi.has_applied_job(session_slug, job_slug, loggedin_user),
        'form': ApplicationForm(initial={ 'applicant': loggedin_user.id, 'job': job.id })
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def applied_jobs(request):
    ''' Display jobs applied by a student '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    apps, total_assigned_hours = adminApi.get_applications_with_status_by_user(loggedin_user, ApplicationStatus.NONE)
    return render(request, 'students/jobs/applied_jobs.html', {
        'loggedin_user': loggedin_user,
        'apps': apps
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def show_job(request, session_slug, job_slug, path):
    ''' Display job details '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    return render(request, 'students/jobs/show_job.html', {
        'loggedin_user': loggedin_user,
        'job': adminApi.get_job_by_session_slug_job_slug(session_slug, job_slug),
        'path': path
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def show_application(request, app_slug, path):
    ''' Display job details '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    return render(request, 'students/jobs/show_application.html', {
        'loggedin_user': loggedin_user,
        'app': adminApi.get_application_by_slug(app_slug),
        'path': path
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def offered_jobs(request):
    ''' Display jobs offered from admins '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    apps, total_assigned_hours = adminApi.get_applications_with_status_by_user(loggedin_user, ApplicationStatus.OFFERED, 'first')
    return render(request, 'students/jobs/offered_jobs.html', {
        'loggedin_user': loggedin_user,
        'apps': apps,
        'total_assigned_hours': total_assigned_hours
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def accepted_jobs(request):
    ''' Display jobs accepted by a student '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    apps, total_assigned_hours = adminApi.get_applications_with_status_by_user(loggedin_user, ApplicationStatus.ACCEPTED)
    return render(request, 'students/jobs/accepted_jobs.html', {
        'loggedin_user': loggedin_user,
        'apps': apps,
        'total_assigned_hours': total_assigned_hours
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def cancel_job(request, session_slug, job_slug):
    ''' Cancel an accepted job '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    job = adminApi.get_job_by_session_slug_job_slug(session_slug, job_slug)
    app = adminApi.get_application_with_status_by_user(loggedin_user, job, ApplicationStatus.ACCEPTED)

    if request.method == 'POST':
        app_id = request.POST.get('application')
        assigned_hours = request.POST.get('assigned_hours')
        form = ApplicationStatusReassignForm({ 'application': app_id, 'assigned': ApplicationStatus.CANCELLED, 'assigned_hours': assigned_hours, 'parent_id': app.status.id })
        if form.is_valid():
            cancelled_status = form.save()
            if cancelled_status:
                messages.success(request, 'Success! Application of {0} {1} - {2} {3} {4} cancelled.'.format(job.session.year, job.session.term.code, job.course.code.name, job.course.number.name, job.course.section.name))
                return redirect('students:accepted_jobs')
            else:
                messages.error(request, 'An error occurred while saving application status.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return HttpResponseRedirect( reverse('students:cancel_job', args=[session_slug, job_slug]) )

    return render(request, 'students/jobs/cancel_job.html', {
        'loggedin_user': loggedin_user,
        'app': app
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def declined_jobs(request):
    ''' Display jobs declined by a student '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    apps, total_assigned_hours = adminApi.get_applications_with_status_by_user(loggedin_user, ApplicationStatus.DECLINED, 'declined only')
    return render(request, 'students/jobs/declined_jobs.html', {
        'loggedin_user': loggedin_user,
        'apps': apps
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def accept_decline_job(request, session_slug, job_slug):
    ''' Display a job to select accept or decline a job offer '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    apps, total_assigned_hours = adminApi.get_applications_with_status_by_user(loggedin_user, ApplicationStatus.OFFERED)

    # Find an application with session_slug and job_slug
    app = None
    for app in apps:
        if app.job.session.slug == session_slug and app.job.course.slug == job_slug:
            app = app
            break

    if not app: raise Http404

    return render(request, 'students/jobs/accept_decline_job.html', {
        'loggedin_user': loggedin_user,
        'app': app
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def accept_offer(request, session_slug, job_slug):
    ''' Students accept a job offer '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    if request.method == 'POST':
        app_id = request.POST.get('application')
        assigned_hours = request.POST.get('assigned_hours')
        assigned = ApplicationStatus.ACCEPTED
        form = ApplicationStatusForm({ 'application': app_id, 'assigned': assigned, 'assigned_hours': assigned_hours })
        if form.is_valid():
            status = form.save()
            if status:
                app = adminApi.get_application(app_id)
                updated = adminApi.update_job_ta_hours(session_slug, job_slug, assigned_hours)
                if updated:
                    messages.success(request, 'Success! You accepted the job offer - {0} {1}: {2} {3} {4} '.format(app.job.session.year, app.job.session.term.code, app.job.course.code.name, app.job.course.number.name, app.job.course.section.name))
                else:
                    messages.error(request, 'An error occurred while updating ta hours.')
            else:
                messages.error(request, 'An error occurred while saving a status of an application.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

    return redirect('students:offered_jobs')

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def decline_offer(request, session_slug, job_slug):
    ''' Students decline job offers '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

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

    return redirect('students:offered_jobs')




# -------------
"""
@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_student(request, username):
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    user = userApi.get_user(request.user.id)
    profile = user.profile

    profile_degrees = profile.degrees.all()
    profile_trainings = profile.trainings.all()

    if request.method == 'POST':
        form = StudentProfileForm(request.POST, instance=profile)
        if form.is_valid():
            data = form.cleaned_data
            updated_profile = form.save(commit=False)
            updated_profile.updated_at = datetime.now()
            form.save()

            if updated_profile:
                updated = api.update_student_profile_degrees_trainings(updated_profile, profile_degrees, profile_trainings, data)
                if updated:
                    messages.success(request, 'Success! {0} - profile updated'.format(user.username))
                    return HttpResponseRedirect( reverse('users:show_student', args=[username]) )
                else:
                    messages.error(request, 'Error!')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'students/edit_profile.html', {
        'loggedin_user': loggedin_user,
        'user': user,
        'form': StudentProfileForm(data=None, instance=profile, initial={
            'degrees': profile_degrees,
            'trainings': profile_trainings
        })
    })



@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def show_student(request, username):
    ''' Display student details '''

    loggedin_user = api.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    user = api.get_user_by_username(username)
    student_jobs = adminApi.get_jobs_applied_by_student(user)
    offered_jobs, offered_summary = adminApi.get_offered_jobs_by_student(user, student_jobs)
    accepted_jobs, accepted_summary = adminApi.get_accepted_jobs_by_student(user, student_jobs)

    resume_file = None
    if user.resume.file != None:
        resume_file = os.path.basename(user.resume.file.name)

    study_permit_file = None
    if user.confidentiality.study_permit != None:
        study_permit_file = os.path.basename(user.confidentiality.study_permit.name)

    work_permit_file = None
    if user.confidentiality.work_permit != None:
        work_permit_file = os.path.basename(user.confidentiality.work_permit.name)


    return render(request, 'users/students/show_student.html', {
        'loggedin_user': loggedin_user,
        'user': user,
        'resume_file': resume_file,
        'study_permit_file': study_permit_file,
        'work_permit_file': work_permit_file,
        'student_jobs': adminApi.get_jobs_applied_by_student(user),
        'offered_jobs': offered_jobs,
        'offered_summary': offered_summary,
        'accepted_jobs': accepted_jobs,
        'accepted_summary': accepted_summary,
        'declined_jobs': adminApi.get_declined_jobs_by_student(user, student_jobs),
        'resume_form': ResumeForm(initial={ 'user': user })
    })
"""
