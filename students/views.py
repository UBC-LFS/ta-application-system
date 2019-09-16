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

from users.forms import *
from users import api as userApi
from administrators.forms import *
from administrators import api as adminApi

from datetime import datetime


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def index(request):
    ''' '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    return render(request, 'students/index.html', {
        'loggedin_user': loggedin_user
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_profile(request):
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    user = userApi.get_user(request.user.id)
    return render(request, 'students/profile/show_profile.html', {
        'loggedin_user': loggedin_user,
        'user': user,
        'resume_form': ResumeForm(initial={ 'user': user })
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_profile(request, username):
    ''' '''
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
                    messages.error(request, 'Error!')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

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
def upload_resume(request, username):
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    user = userApi.get_user(request.user.id)
    print(user.resume_file)
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
                deleted_resume = userApi.delete_user_resume(user.username)
                if not deleted_resume:
                    messages.warning(request, 'Warning! resume is not deleted')

            resume.file = request.FILES.get('file')
            resume.created_at = datetime.now()
            resume.save()
            if resume:
                messages.success(request, 'Success! {0} - resume uploaded'.format(user.username))
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

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
    ''' '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    if request.method == 'POST':
        username = request.POST.get('user')
        deleted_resume = api.delete_user_resume(username)
        if deleted_resume:
            messages.success(request, 'Success! {0} - resume deleted'.format(username))
        else:
            messages.error(request, 'Error!')
    else:
        messages.error(request, 'Error!')
    return redirect('students:show_profile')


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_confidentiality(request):
    ''' '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    user = userApi.get_user(request.user.id)
    confidentiality = userApi.has_user_confidentiality_created(user)

    sin_file = None
    study_permit_file = None
    if confidentiality != None:
        sin_file = os.path.basename(confidentiality.sin.name)
        study_permit_file = os.path.basename(confidentiality.study_permit.name)

    print('sin_file ', user.sin_file)
    print('study_permit_file ', user.study_permit_file)
    return render(request, 'students/profile/show_confidentiality.html', {
        'loggedin_user': loggedin_user,
        'user': user,
        'confidentiality': confidentiality,
        #'sin_file': sin_file,
        #'study_permit_file': study_permit_file
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def check_confidentiality(request):
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    user = userApi.get_user(request.user.id)
    if request.method == 'POST':
        form = None
        confidentiality = userApi.has_user_confidentiality_created(user)
        if confidentiality:
            form = ConfidentialityCheckForm(request.POST, instance=user.confidentiality)
        else:
            form = ConfidentialityCheckForm(request.POST)
        if form.is_valid():
            confidentiality = form.save()
            if confidentiality:
                messages.info(request, 'Thank you for selecting.')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

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
                messages.success(request, 'Success! {0} - confidentiality created'.format(user.username))
                return redirect('students:show_confidentiality')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')
    else:
        if user.confidentiality.is_international == True:
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
    ''' '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    user = userApi.get_user(request.user.id)
    if request.method == 'POST':
        old_sin = user.confidentiality.sin
        old_study_permit = user.confidentiality.study_permit

        form = ConfidentialityForm(request.POST, request.FILES, instance=user.confidentiality)
        if form.is_valid():
            sin_file = request.FILES.get('sin')
            study_permit_file = request.FILES.get('study_permit')

            updated_confidentiality = form.save(commit=False)
            updated_confidentiality.updated_at = datetime.now()

            if sin_file != None:
                if len(old_sin.name) > 0:
                    deleted_sin_file = userApi.delete_user_sin(user.username)
                    if not deleted_sin_file:
                        messages.warning(request, 'Warning! Previous SIN file was not deleted')
                user.confidentiality.sin = sin_file

            if study_permit_file != None:
                if len(old_study_permit.name) > 0:
                    deleted_study_permit_file = userApi.delete_user_study_permit(user.username)
                    if not deleted_study_permit_file:
                        messages.warning(request, 'Warning! Previous study permit file was not deleted')
                user.confidentiality.study_permit = study_permit_file

            updated_confidentiality.save()

            if updated_confidentiality:
                messages.success(request, 'Success! {0} - confidentiality updated'.format(user.username))
                return redirect('students:show_confidentiality')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'students/profile/edit_confidentiality.html', {
        'loggedin_user': loggedin_user,
        'form': ConfidentialityForm(data=None, instance=user.confidentiality, initial={
            'user': user
        })
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def download_sin(request, username, filename):
    ''' '''
    if not userApi.is_valid_user(request.user): raise PermissionDenied
    path = 'users/{0}/sin/{1}/'.format(username, filename)
    return serve(request, path, document_root=settings.MEDIA_ROOT)

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_sin(request):
    ''' '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    if request.method == 'POST':
        username = request.POST.get('user')
        deleted_sin = userApi.delete_user_sin(username)
        if deleted_sin:
            messages.success(request, 'Success! {0} - SIN deleted'.format(username))
        else:
            messages.error(request, 'Error!')
    else:
        messages.error(request, 'Error!')
    return redirect('students:show_confidentiality')



@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def download_study_permit(request, username, filename):
    ''' '''
    if not userApi.is_valid_user(request.user): raise PermissionDenied
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
            messages.success(request, 'Success! {0} - study permit deleted'.format(username))
        else:
            messages.error(request, 'Error!')
    else:
        messages.error(request, 'Error!')
    return redirect('students:show_confidentiality')

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def explore_jobs(request):
    ''' '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    student_jobs = adminApi.get_jobs_applied_by_student(loggedin_user)
    offered_jobs, offered_summary = adminApi.get_offered_jobs_by_student(loggedin_user, student_jobs)
    accepted_jobs, accepted_summary = adminApi.get_accepted_jobs_by_student(loggedin_user, student_jobs)
    return render(request, 'students/jobs/explore_jobs.html', {
        'loggedin_user': loggedin_user,
        'visible_current_sessions': adminApi.get_visible_current_sessions(),
        'applied_jobs': adminApi.get_jobs_applied_by_student(loggedin_user),
        'offered_jobs': offered_jobs,
        'accepted_jobs': accepted_jobs
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def available_jobs(request, session_slug):
    ''' '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    return render(request, 'students/jobs/available_jobs.html', {
        'loggedin_user': loggedin_user,
        'session': adminApi.get_session_by_slug(session_slug),
        'jobs': adminApi.get_jobs_with_student_applied(session_slug, loggedin_user)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def apply_job(request, session_slug, job_slug):
    ''' '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    job = adminApi.get_session_job_by_slug(session_slug, job_slug)
    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            application = form.save()

            if application:
                app_status = adminApi.student_apply_job(application)

                if app_status:
                    messages.success(request, 'Success! {0} {1} - {2} {3} {4} applied'.format(job.session.year, job.session.term.code, job.course.code.name, job.course.number.name, job.course.section.name))
                    return HttpResponseRedirect( reverse('students:available_jobs', args=[session_slug]) )
                else:
                    messages.error(request, 'Error!')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! form is invalid')

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
    ''' '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    return render(request, 'students/jobs/applied_jobs.html', {
        'loggedin_user': loggedin_user,
        'applied_jobs': adminApi.get_jobs_applied_by_student(loggedin_user)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def offered_jobs(request):
    ''' '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    student_jobs = adminApi.get_jobs_applied_by_student(loggedin_user)
    offered_jobs, offered_summary = adminApi.get_offered_jobs_by_student(loggedin_user, student_jobs)
    return render(request, 'students/jobs/offered_jobs.html', {
        'loggedin_user': loggedin_user,
        'offered_jobs': offered_jobs,
        'offered_summary': offered_summary
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def accepted_jobs(request):
    ''' '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    student_jobs = adminApi.get_jobs_applied_by_student(loggedin_user)
    accepted_jobs, accepted_summary = adminApi.get_accepted_jobs_by_student(loggedin_user, student_jobs)
    return render(request, 'students/jobs/accepted_jobs.html', {
        'loggedin_user': loggedin_user,
        'accepted_jobs': accepted_jobs,
        'accepted_summary': accepted_summary
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def declined_jobs(request):
    ''' '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    student_jobs = adminApi.get_jobs_applied_by_student(loggedin_user)
    return render(request, 'students/jobs/declined_jobs.html', {
        'loggedin_user': loggedin_user,
        'declined_jobs': adminApi.get_declined_jobs_by_student(loggedin_user, student_jobs)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def offered_job(request, session_slug, job_slug):
    ''' '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    job = adminApi.get_job_applied_by_student(loggedin_user, session_slug, job_slug)
    application = adminApi.get_application_by_student_job(loggedin_user, job)
    return render(request, 'students/jobs/offered_job.html', {
        'loggedin_user': loggedin_user,
        'job': job,
        'application': application,
        'get_offered': adminApi.get_offered(application),
        'get_accepted': adminApi.get_accepted(application),
        'get_declined': adminApi.get_declined(application)
    })



@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def accept_offer(request, session_slug, job_slug):
    ''' Students accept job offers '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    if request.method == 'POST':
        application_id = request.POST.get('application')
        assigned_hours = request.POST.get('assigned_hours')
        assigned = ApplicationStatus.ACCEPTED
        form = ApplicationStatusForm({ 'assigned': assigned, 'assigned_hours': assigned_hours })
        if form.is_valid():
            status = form.save()
            if status:
                application = adminApi.get_application(application_id)
                application.status.add(status)
                application.save()
                if application:
                    updated = adminApi.update_job_ta_hours(session_slug, job_slug, assigned_hours)
                    if updated:
                        messages.success(request, 'Success! You accepted the job offer - {0} {1}: {2} {3} {4} '.format(application.job.session.year, application.job.session.term.code, application.job.course.code.name, application.job.course.number.name, application.job.course.section.name))
                    else:
                        message.error(request, 'Error!')
                else:
                    message.error(request, 'Error!')
            else:
                message.error(request, 'Error!')
        else:
            message.error(request, 'Error! Form is invalid')
    return redirect('students:offered_jobs')


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def decline_offer(request, session_slug, job_slug):
    ''' Students decline job offers '''
    loggedin_user = userApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user.roles: raise PermissionDenied

    if request.method == 'POST':
        application_id = request.POST.get('application')
        assigned = ApplicationStatus.DECLINED
        form = ApplicationStatusForm({ 'assigned': assigned, 'assigned_hours': 0.0 })
        if form.is_valid():
            status = form.save()
            if status:
                application = adminApi.get_application(application_id)
                application.status.add(status)
                application.save()
                if application:
                    messages.success(request, 'Success! You declined the job offer - {0} {1}: {2} {3} {4} '.format(application.job.session.year, application.job.session.term.code, application.job.course.code.name, application.job.course.number.name, application.job.course.section.name))
                else:
                    message.error(request, 'Error!')
            else:
                message.error(request, 'Error!')
        else:
            message.error(request, 'Error! Form is invalid')
    return redirect('students:offered_jobs')


# -------------

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
    """ Display student details """

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
