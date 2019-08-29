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
from administrators.forms import *
from users import api as usersApi
from administrators import api as administratorsApi

from datetime import datetime


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def index(request):
    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user['roles']: raise PermissionDenied

    return render(request, 'students/index.html', {
        'loggedin_user': loggedin_user
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_profile(request):
    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user['roles']: raise PermissionDenied

    user = usersApi.get_user(request.user.id)
    resume_file = None
    if user.resume.file != None:
        resume_file = os.path.basename(user.resume.file.name)

    return render(request, 'students/profile/show_profile.html', {
        'loggedin_user': loggedin_user,
        'user': user,
        'resume_file': resume_file,
        'resume_form': ResumeForm(initial={ 'user': user })
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_profile(request, username):
    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user['roles']: raise PermissionDenied

    user = usersApi.get_user(request.user.id)
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
                updated = usersApi.update_student_profile_degrees_trainings(updated_profile, profile_degrees, profile_trainings, data)
                if updated:
                    messages.success(request, 'Success! {0} - profile updated'.format(user.username))
                    return redirect('students:show_profile')
                else:
                    messages.error(request, 'Error!')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'students/profile/edit_profile.html', {
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
def edit_confidentiality(request, username):
    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user['roles']: raise PermissionDenied


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def upload_resume(request, username):
    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user['roles']: raise PermissionDenied

    user = usersApi.get_user(request.user.id)
    old_resume = user.resume.file
    if request.method == 'POST':
        form = ResumeForm(request.POST, request.FILES, instance=user.resume)
        if form.is_valid():
            files = request.FILES
            resume = form.save(commit=False)

            if len(old_resume.name) > 0:
                deleted_resume = usersApi.delete_user_resume(user.username)
                if not deleted_resume:
                    messages.warning(request, 'Warning! resume is not deleted')

            resume.file = files.get('file')
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
    """ Download user's resume """

    if not usersApi.is_valid_user(request.user):
        raise PermissionDenied

    path = 'users/{0}/resume/{1}/'.format(username, filename)
    return serve(request, path, document_root=settings.MEDIA_ROOT)


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_resume(request):
    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user['roles']: raise PermissionDenied

    if request.method == 'POST':
        username = request.POST.get('user')
        resume = api.delete_user_resume(username)
        if resume:
            messages.success(request, 'Success! {0} - resume deleted'.format(username))
        else:
            messages.error(request, 'Error!')
    else:
        messages.error(request, 'Error!')
    return redirect('students:show_profile')



@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def submit_confidentiality(request, username):
    """ Submit user's confidentiality """

    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user['roles']: raise PermissionDenied

    user = usersApi.get_user(request.user.id)
    confidentiality = user.confidentiality
    old_study_permit = confidentiality.study_permit
    old_work_permit = confidentiality.work_permit

    if request.method == 'POST':
        form = ConfidentialityForm(request.POST, request.FILES, instance=confidentiality)
        if form.is_valid():
            study_permit_file = request.FILES.get('study_permit')
            work_permit_file = request.FILES.get('work_permit')

            updated_confidentiality = form.save(commit=False)
            updated_confidentiality.updated_at = datetime.now()

            if study_permit_file != None:
                if len(old_study_permit.name) > 0:
                    deleted_study_permit_file = usersApi.delete_user_study_permit(username)
                    if not deleted_study_permit_file:
                        messages.warning(request, 'Warning! Previous study permit file was not deleted')
                confidentiality.study_permit = study_permit_file

            if work_permit_file != None:
                if len(old_work_permit.name) > 0:
                    deleted_work_permit_file = usersApi.delete_user_work_permit(username)
                    if not deleted_work_permit_file:
                        messages.warning(request, 'Warning! Previous work permit file was not deleted')
                confidentiality.work_permit = work_permit_file

            updated_confidentiality.save()

            if updated_confidentiality:
                messages.success(request, 'Success! {0} - confidentiality updated'.format(username))
                return HttpResponseRedirect( reverse('students:submit_confidentiality', args=[username]) )
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'students/profile/submit_confidentiality.html', {
        'loggedin_user': loggedin_user,
        'user': user,
        'form': ConfidentialityForm(data=None, instance=confidentiality, initial={ 'user': user })
    })



@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def download_study_permit(request, username, filename):
    """ Download user's resume """

    if not usersApi.is_valid_user(request.user): raise PermissionDenied

    path = 'users/{0}/study_permit/{1}/'.format(username, filename)
    return serve(request, path, document_root=settings.MEDIA_ROOT)


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_study_permit(request):
    """ Delete user's study permit """

    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user['roles']: raise PermissionDenied

    if request.method == 'POST':
        username = request.POST.get('user')
        study_permit = usersApi.delete_user_study_permit(username)
        if study_permit:
            messages.success(request, 'Success! {0} - study permit deleted'.format(username))
        else:
            messages.error(request, 'Error!')
    else:
        messages.error(request, 'Error!')
    return HttpResponseRedirect( reverse('students:submit_confidentiality', args=[username]) )


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def download_work_permit(request, username, filename):
    """ Download user's work permit """

    if not usersApi.is_valid_user(request.user): raise PermissionDenied

    path = 'users/{0}/work_permit/{1}/'.format(username, filename)
    return serve(request, path, document_root=settings.MEDIA_ROOT)


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_work_permit(request):
    """ Delete user's work permit """

    if not api.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user['roles']: raise PermissionDenied

    if request.method == 'POST':
        username = request.POST.get('user')
        work_permit = usersApi.delete_user_work_permit(username)
        if work_permit:
            messages.success(request, 'Success! {0} - work permit deleted'.format(username))
        else:
            messages.error(request, 'Error!')
    else:
        messages.error(request, 'Error!')
    return HttpResponseRedirect( reverse('students:submit_confidentiality', args=[username]) )


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def explore_jobs(request):

    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user['roles']: raise PermissionDenied

    visible_current_sessions = administratorsApi.get_visible_current_sessions()
    return render(request, 'students/jobs/explore_jobs.html', {
        'loggedin_user': loggedin_user,
        'visible_current_sessions': visible_current_sessions,
        'applied_jobs': administratorsApi.get_jobs_applied_by_student(request.user)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def list_jobs(request, session_slug):

    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user['roles']: raise PermissionDenied

    return render(request, 'students/jobs/list_jobs.html', {
        'loggedin_user': loggedin_user,
        'session': administratorsApi.get_session_by_slug(session_slug),
        'jobs': administratorsApi.get_jobs_with_student_applied(session_slug, request.user)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def apply_job(request, session_slug, job_slug):
    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user['roles']: raise PermissionDenied

    session = administratorsApi.get_session_by_slug(session_slug)
    job = administratorsApi.get_session_job_by_slug(session_slug, job_slug)
    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            application = form.save()

            if application:
                status_form = ApplicationStatusForm({ 'assigned': ApplicationStatus.NONE, 'assigned_hours': 0.00 })
                #status_data = status_form.cleaned_data
                status = status_form.save()

                if status:
                    application.status.add(status)
                    #job.applications.add(application)
                    messages.success(request, 'Success! {0} {1} {2} {3} {4} applied'.format(job.session.year, job.session.term.code, job.course.code.name, job.course.number.name, job.course.section.name))
                    return HttpResponseRedirect( reverse('students:list_jobs', args=[session_slug]) )
                else:
                    messages.error(request, 'Error!')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! form is invalid')

    return render(request, 'students/jobs/apply_job.html', {
        'loggedin_user': loggedin_user,
        'session': session,
        'job': job,
        'has_applied_job': administratorsApi.has_applied_job(session_slug, job_slug, request.user),
        'form': ApplicationForm(initial={
            'applicant': request.user.id,
            'job': job.id
        })
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def applied_jobs(request):

    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user['roles']: raise PermissionDenied

    user = usersApi.get_user(request.user.id)

    jobs = administratorsApi.get_jobs_applied_by_student(user)
    for job in jobs:
        print(job, job.my_application)

    return render(request, 'students/jobs/applied_jobs.html', {
        'loggedin_user': loggedin_user,
        'applied_jobs': administratorsApi.get_jobs_applied_by_student(user)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def offered_jobs(request):

    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user['roles']: raise PermissionDenied

    user = usersApi.get_user(request.user.id)
    student_jobs = administratorsApi.get_jobs_applied_by_student(user)
    offered_jobs, offered_summary = administratorsApi.get_offered_jobs_by_student(user, student_jobs)
    return render(request, 'students/jobs/offered_jobs.html', {
        'loggedin_user': loggedin_user,
        'user': user,
        'offered_jobs': offered_jobs,
        'offered_summary': offered_summary
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def accepted_jobs(request):

    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user['roles']: raise PermissionDenied

    user = usersApi.get_user(request.user.id)
    student_jobs = administratorsApi.get_jobs_applied_by_student(user)
    accepted_jobs, accepted_summary = administratorsApi.get_accepted_jobs_by_student(user, student_jobs)
    return render(request, 'students/jobs/accepted_jobs.html', {
        'loggedin_user': loggedin_user,
        'user': user,
        'accepted_jobs': accepted_jobs,
        'accepted_summary': accepted_summary,
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def declined_jobs(request):

    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user['roles']: raise PermissionDenied

    user = usersApi.get_user(request.user.id)
    student_jobs = administratorsApi.get_jobs_applied_by_student(user)
    return render(request, 'students/jobs/declined_jobs.html', {
        'loggedin_user': loggedin_user,
        'user': user,
        'declined_jobs': administratorsApi.get_declined_jobs_by_student(user, student_jobs)
    })



# -------------

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_student(request, username):
    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user['roles']: raise PermissionDenied

    user = usersApi.get_user(request.user.id)
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

    if not api.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = api.loggedin_user(request.user)
    if 'Student' not in loggedin_user['roles']:
        raise PermissionDenied

    user = api.get_user_by_username(username)
    student_jobs = administratorsApi.get_jobs_applied_by_student(user)
    offered_jobs, offered_summary = administratorsApi.get_offered_jobs_by_student(user, student_jobs)
    accepted_jobs, accepted_summary = administratorsApi.get_accepted_jobs_by_student(user, student_jobs)

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
        'student_jobs': administratorsApi.get_jobs_applied_by_student(user),
        'offered_jobs': offered_jobs,
        'offered_summary': offered_summary,
        'accepted_jobs': accepted_jobs,
        'accepted_summary': accepted_summary,
        'declined_jobs': administratorsApi.get_declined_jobs_by_student(user, student_jobs),
        'resume_form': ResumeForm(initial={ 'user': user })
    })
