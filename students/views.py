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
    if usersApi.has_user_resume_created(user) and user.resume.file != None:
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
    if request.method == 'POST':
        form = None
        old_resume = None
        if usersApi.has_user_resume_created(user) and user.resume.file != None:
            old_resume = user.resume.file
            form = ResumeForm(request.POST, request.FILES, instance=user.resume)
        else:
            form = ResumeForm(request.POST, request.FILES)

        if form.is_valid():
            resume = form.save(commit=False)
            if usersApi.has_user_resume_created(user) and user.resume.file != None and old_resume != None and len(old_resume.name) > 0:
                deleted_resume = usersApi.delete_user_resume(user.username)
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
@require_http_methods(['GET'])
def show_confidentiality(request):
    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user['roles']: raise PermissionDenied

    user = usersApi.get_user(request.user.id)
    confidentiality = usersApi.has_user_confidentiality_created(user)

    sin_file = None
    study_permit_file = None
    if confidentiality != None:
        sin_file = os.path.basename(confidentiality.sin.name)
        study_permit_file = os.path.basename(confidentiality.study_permit.name)


    return render(request, 'students/profile/show_confidentiality.html', {
        'loggedin_user': loggedin_user,
        'user': user,
        'confidentiality': confidentiality,
        'sin_file': sin_file,
        'study_permit_file': study_permit_file
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def check_confidentiality(request):
    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user['roles']: raise PermissionDenied

    user = usersApi.get_user(request.user.id)
    if request.method == 'POST':
        form = None
        confidentiality = usersApi.has_user_confidentiality_created(user)
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
            print(form.errors.get_json_data())
            messages.error(request, 'Error! Form is invalid')

    return redirect('students:submit_confidentiality')

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def submit_confidentiality(request):
    """ Submit user's confidentiality """

    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user['roles']: raise PermissionDenied

    user = usersApi.get_user(request.user.id)
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
    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user['roles']: raise PermissionDenied

    user = usersApi.get_user(request.user.id)

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
                    deleted_sin_file = usersApi.delete_user_sin(user.username)
                    if not deleted_sin_file:
                        messages.warning(request, 'Warning! Previous SIN file was not deleted')
                user.confidentiality.sin = sin_file

            if study_permit_file != None:
                if len(old_study_permit.name) > 0:
                    deleted_study_permit_file = usersApi.delete_user_study_permit(user.username)
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
        'user': user,
        'form': ConfidentialityForm(data=None, instance=user.confidentiality, initial={
            'user': user
        })
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def download_sin(request, filename):
    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    path = 'users/{0}/sin/{1}/'.format(request.user.username, filename)
    return serve(request, path, document_root=settings.MEDIA_ROOT)

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_sin(request):

    print("delete_sin  ")
    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user['roles']: raise PermissionDenied

    if request.method == 'POST':
        username = request.POST.get('user')
        deleted_sin = usersApi.delete_user_sin(username)
        if deleted_sin:
            messages.success(request, 'Success! {0} - SIN deleted'.format(username))
        else:
            messages.error(request, 'Error!')
    else:
        messages.error(request, 'Error!')
    print("here")
    return redirect('students:show_confidentiality')



@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def download_study_permit(request, filename):
    if not usersApi.is_valid_user(request.user): raise PermissionDenied

    path = 'users/{0}/study_permit/{1}/'.format(request.user.username, filename)
    return serve(request, path, document_root=settings.MEDIA_ROOT)


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_study_permit(request):
    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user['roles']: raise PermissionDenied

    if request.method == 'POST':
        username = request.POST.get('user')
        deleted_study_permit = usersApi.delete_user_study_permit(username)
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

    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if 'Student' not in loggedin_user['roles']: raise PermissionDenied

    user = usersApi.get_user(request.user.id)
    visible_current_sessions = administratorsApi.get_visible_current_sessions()
    student_jobs = administratorsApi.get_jobs_applied_by_student(user)
    offered_jobs, offered_summary = administratorsApi.get_offered_jobs_by_student(user, student_jobs)
    accepted_jobs, accepted_summary = administratorsApi.get_accepted_jobs_by_student(user, student_jobs)
    print(offered_summary)
    print(accepted_summary)


    return render(request, 'students/jobs/explore_jobs.html', {
        'loggedin_user': loggedin_user,
        'visible_current_sessions': visible_current_sessions,
        'applied_jobs': administratorsApi.get_jobs_applied_by_student(request.user),
        'offered_jobs': offered_jobs,
        'accepted_jobs': accepted_jobs
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
