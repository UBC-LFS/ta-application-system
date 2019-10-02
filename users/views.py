
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.views.static import serve
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_control
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

from datetime import datetime

from users import api as userApi
from administrators import api as administratorsApi
from users.forms import *
from administrators.forms import *
from administrators.models import *


from django.forms.models import model_to_dict


# Users

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def users(request):

    if not api.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = api.loggedin_user(request.user)
    if not api.is_admin(loggedin_user) or 'HR' not in loggedin_user['roles']: raise PermissionDenied

    users = api.get_users()
    return render(request, 'users/users.html', {
        'loggedin_user': api.loggedin_user(request.user),
        'users': users,
        'total_users': len(users),
    })


"""
@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def create_user(request):
    if not api.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = api.loggedin_user(request.user)
    if not api.is_admin(loggedin_user): raise PermissionDenied

    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save()
            if user:
                profile = api.create_profile(user)
                if profile:
                    resume = api.create_user_resume(user)
                    if resume:
                        confidentiality = api.create_user_confidentiality(user)
                        if confidentiality:
                            messages.success(request, 'Success! {0} created'.format(user.username))
                            return redirect('users:index')
                        else:
                            messages.error(request, 'Error! at confidentiality')
                    else:
                        messages.error(request, 'Error! at resume')
                else:
                    messages.error(request, 'Error! at profile')
            else:
                messages.error(request, 'Error! at user')
        else:
            messages.error(request, 'Error! form invalid')

    return render(request, 'users/create_user.html', {
        'loggedin_user': loggedin_user,
        'users': api.get_users(),
        'form': UserForm()
    })
"""


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_user(request, username):
    """ Display user details """

    if not api.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = api.loggedin_user(request.user)
    if not api.is_admin(loggedin_user):
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


    return render(request, 'users/show_user.html', {
        'loggedin_user': loggedin_user,
        'user': user,
        'roles': api.get_user_roles(user),
        'instructor_jobs': administratorsApi.get_jobs_of_instructor(user),
        #'job_application_applied_by_student': administratorsApi.get_job_application_applied_by_student(user),
        'applications': administratorsApi.get_applications_by_student(user),
        'student_jobs': student_jobs,
        'offered_jobs': offered_jobs,
        'offered_summary': offered_summary,
        'accepted_jobs': accepted_jobs,
        'accepted_summary': accepted_summary,
        'declined_jobs': administratorsApi.get_declined_jobs_by_student(user, student_jobs),
        'resume_file': resume_file,
        'study_permit_file': study_permit_file,
        'work_permit_file': work_permit_file,
        'confidentiality': user.confidentiality,
        'form': UserInfoForm(data=None, instance=user)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_user_info(request, username):
    """ Edit user's information (first_name, last_name) """

    if not api.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = api.loggedin_user(request.user)
    if not api.is_admin(loggedin_user):
        raise PermissionDenied

    user = api.get_user_by_username(username)
    if request.method == 'POST':
        form = UserInfoForm(request.POST, instance=user)
        if form.is_valid():
            updated_user = form.save()
            if updated_user:
                messages.success(request, 'Success! {0} updated'.format(user.username))
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')
    return HttpResponseRedirect( reverse('users:show_user', args=[username]) )



@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_profile(request, username):
    """ Edit user's profile """

    if not api.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = api.loggedin_user(request.user)
    if not api.is_admin(loggedin_user):
        raise PermissionDenied

    user = api.get_user_by_username(username)
    profile = api.get_profile(user)
    profile_roles = profile.roles.all()
    profile_degrees = profile.degrees.all()
    profile_trainings = profile.trainings.all()

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            data = form.cleaned_data
            updated_profile = form.save(commit=False)
            updated_profile.updated_at = datetime.now()
            updated_profile.save()
            if updated_profile:
                updated = api.update_user_profile(updated_profile, profile_roles, profile_degrees, profile_trainings, data)
                if updated:
                    messages.success(request, 'Success! {0} - profile updated'.format(username))
                    return HttpResponseRedirect( reverse('users:show_user', args=[username]) )
                else:
                    messages.error(request, 'Error!')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'users/edit_profile.html', {
        'loggedin_user': loggedin_user,
        'user': user,
        'form': ProfileForm(data=None, instance=profile, initial={
            'roles': profile_roles,
            'degrees': profile_degrees,
            'trainings': profile_trainings
        })
    })




@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def submit_confidentiality(request, username):
    """ Submit user's confidentiality """

    if not api.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = api.loggedin_user(request.user)
    if 'Student' not in loggedin_user['roles']:
        raise PermissionDenied

    user = api.get_user_by_username(username)
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
                    deleted_study_permit_file = api.delete_user_study_permit(username)
                    if not deleted_study_permit_file:
                        messages.warning(request, 'Warning! Previous study permit file was not deleted')
                confidentiality.study_permit = study_permit_file

            if work_permit_file != None:
                if len(old_work_permit.name) > 0:
                    deleted_work_permit_file = api.delete_user_work_permit(username)
                    if not deleted_work_permit_file:
                        messages.warning(request, 'Warning! Previous work permit file was not deleted')
                confidentiality.work_permit = work_permit_file

            updated_confidentiality.save()

            if updated_confidentiality:
                messages.success(request, 'Success! {0} - confidentiality updated'.format(username))
                return HttpResponseRedirect( reverse('users:show_student', args=[username]) )
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'users/students/edit_confidentiality.html', {
        'loggedin_user': loggedin_user,
        'user': user,
        'form': ConfidentialityForm(data=None, instance=confidentiality, initial={ 'user': user })
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def download_sin(request, username, filename):

    if not api.is_valid_user(request.user): raise PermissionDenied

    path = 'users/{0}/sin/{1}/'.format(username, filename)
    return serve(request, path, document_root=settings.MEDIA_ROOT)


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_sin(request):

    if not api.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = api.loggedin_user(request.user)
    if 'Student' not in loggedin_user['roles']:
        raise PermissionDenied

    if request.method == 'POST':
        username = request.POST.get('user')
        work_permit = api.delete_user_work_permit(username)
        if work_permit:
            messages.success(request, 'Success! {0} - SIN deleted'.format(username))
        else:
            messages.error(request, 'Error!')
    else:
        messages.error(request, 'Error!')
    return HttpResponseRedirect( reverse('users:show_student', args=[username]) )


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def download_study_permit(request, username, filename):

    if not api.is_valid_user(request.user): raise PermissionDenied

    path = 'users/{0}/study_permit/{1}/'.format(username, filename)
    return serve(request, path, document_root=settings.MEDIA_ROOT)


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_study_permit(request):

    if not api.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = api.loggedin_user(request.user)
    if 'Student' not in loggedin_user['roles']:
        raise PermissionDenied

    if request.method == 'POST':
        username = request.POST.get('user')
        study_permit = api.delete_user_study_permit(username)
        if study_permit:
            messages.success(request, 'Success! {0} - study permit deleted'.format(username))
        else:
            messages.error(request, 'Error!')
    else:
        messages.error(request, 'Error!')
    return HttpResponseRedirect( reverse('users:show_student', args=[username]) )








@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_student(request, username):

    if not api.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = api.loggedin_user(request.user)
    if 'Student' not in loggedin_user['roles']:
        raise PermissionDenied

    user = api.get_user_by_username(username)
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

    return render(request, 'users/students/edit_student.html', {
        'loggedin_user': loggedin_user,
        'user': user,
        'form': StudentProfileForm(data=None, instance=profile, initial={
            'degrees': profile_degrees,
            'trainings': profile_trainings
        })
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_student_job(request, username, session_slug, job_slug):

    if not api.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = api.loggedin_user(request.user)
    if 'Student' not in loggedin_user['roles']:
        raise PermissionDenied

    user = api.get_user_by_username(username)
    job = administratorsApi.get_job_applied_by_student(user, session_slug, job_slug)
    application = administratorsApi.get_application_by_student_job(user, job)
    return render(request, 'users/students/show_student_job.html', {
        'loggedin_user': loggedin_user,
        'user': user,
        'session': administratorsApi.get_session_by_slug(session_slug),
        'job': job,
        'application': application,
        'get_offered': administratorsApi.get_offered(application),
        'get_accepted': administratorsApi.get_accepted(application),
        'get_declined': administratorsApi.get_declined(application)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def accept_offer(request, username, session_slug, job_slug):

    if not api.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = api.loggedin_user(request.user)

    if request.method == 'POST':
        application_id = request.POST.get('application')
        assigned_hours = request.POST.get('assigned_hours')
        assigned = ApplicationStatus.ACCEPTED
        form = ApplicationStatusForm({ 'assigned': assigned, 'assigned_hours': assigned_hours })
        if form.is_valid():
            status = form.save()
            if status:
                application = administratorsApi.get_application(application_id)
                application.status.add(status)
                application.save()
                if application:
                    updated = administratorsApi.update_job_ta_hours(session_slug, job_slug, assigned_hours)
                    if updated:
                        messages.success(request, 'Success!')
                    else:
                        message.error(request, 'Error!')
                else:
                    message.error(request, 'Error!')
            else:
                message.error(request, 'Error!')
        else:
            message.error(request, 'Error! Form is invalid')

    return HttpResponseRedirect( reverse('users:show_student_job', args=[username, session_slug, job_slug]) )


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def decline_offer(request, username, session_slug, job_slug):

    if not api.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = api.loggedin_user(request.user)

    if request.method == 'POST':
        application_id = request.POST.get('application')
        #assigned_hours = request.POST.get('assigned_hours')
        assigned = ApplicationStatus.DECLINED
        form = ApplicationStatusForm({ 'assigned': assigned, 'assigned_hours': 0.0 })
        if form.is_valid():
            status = form.save()
            if status:
                application = administratorsApi.get_application(application_id)
                application.status.add(status)
                application.save()
                if application:
                    messages.success(request, 'Success!')
                else:
                    message.error(request, 'Error!')
            else:
                message.error(request, 'Error!')
        else:
            message.error(request, 'Error! Form is invalid')

    return HttpResponseRedirect( reverse('users:show_student_job', args=[username, session_slug, job_slug]) )



# Instructor Profile

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_instructor(request, username):

    if not api.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = api.loggedin_user(request.user)
    if 'Instructor' not in loggedin_user['roles']:
        raise PermissionDenied

    return render(request, 'users/instructors/show_instructor.html', {
        'loggedin_user': loggedin_user,
        'user': api.get_user_by_username(username)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_instructor(request, username):

    if not api.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = api.loggedin_user(request.user)
    if 'Instructor' not in loggedin_user['roles']:
        raise PermissionDenied

    user = api.get_user_by_username(username)
    if request.method == 'POST':
        form = InstructorProfileForm(request.POST, instance=user.profile)
        if form.is_valid():
            updated_profile = form.save(commit=False)
            updated_profile.updated_at = datetime.now()
            updated_profile.save()
            if updated_profile:
                messages.success(request, 'Success!')
                return HttpResponseRedirect( reverse('users:show_instructor', args=[username]) )
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'users/instructors/edit_instructor.html', {
        'loggedin_user': api.loggedin_user(request.user),
        'user': user,
        'jobs': user.job_set.all(),
        'form': InstructorProfileForm(data=None, instance=user.profile)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def show_instructor_jobs(request, username, session_slug, job_slug):

    if not api.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = api.loggedin_user(request.user)
    if 'Instructor' not in loggedin_user['roles']:
        raise PermissionDenied

    job = administratorsApi.get_session_job_by_slug(session_slug, job_slug)
    instructor_preference = [ app.instructor_preference for app in job.application_set.all() ]
    print(instructor_preference)
    if request.method == 'POST':
        form = InstructorApplicationForm(request.POST)
        if form.is_valid():
            data = request.POST
            application_id = data.get('application')
            instructor_preference = data.get('instructor_preference')
            updated = administratorsApi.update_application_instructor_preference(application_id, instructor_preference)
            if updated:
                messages.success(request, 'Success!')
                return HttpResponseRedirect( reverse('users:show_instructor_jobs', args=[username, session_slug, job_slug]) )
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'users/instructors/show_instructor_jobs.html', {
        'loggedin_user': api.loggedin_user(request.user),
        'user': api.get_user_by_username(username),
        'session': administratorsApi.get_session_by_slug(session_slug),
        'job': administratorsApi.get_session_job_by_slug(session_slug, job_slug),
        'form': InstructorApplicationForm()
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_instructor_jobs(request, username, session_slug, job_slug):

    if not api.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = api.loggedin_user(request.user)
    if 'Instructor' not in loggedin_user['roles']:
        raise PermissionDenied

    user = api.get_user_by_username(username)
    job = administratorsApi.get_session_job_by_slug(session_slug, job_slug)
    if request.method == 'POST':
        form = InstructorJobForm(request.POST, instance=job)
        if form.is_valid():
            job = form.save(commit=False)
            job.updated_at = datetime.now()
            job.save()
            if job:
                messages.success(request, 'Success! {0} - job details updated'.format(user.username))
                return HttpResponseRedirect( reverse('users:show_instructor_jobs', args=[username, session_slug, job_slug]) )
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error!')

    return render(request, 'users/instructors/edit_instructor_jobs.html', {
        'loggedin_user': api.loggedin_user(request.user),
        'user': user,
        'session': administratorsApi.get_session_by_slug(session_slug),
        'job': job,
        'form': InstructorJobForm(data=None, instance=job)
    })


# HR

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def hr(request):
    ''' Display HR's page '''

    if not api.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = api.loggedin_user(request.user)
    if  'Admin' not in loggedin_user['roles'] or 'HR' not in loggedin_user['roles']: raise PermissionDenied

    users = api.get_users()
    total_users = len(users)

    # Pagination enables
    '''
    user_list = api.get_users()
    total_users = len(user_list)
    query = request.GET.get('q')
    if query:
        user_list = User.objects.filter(
            Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query)
        ).distinct()

    page = request.GET.get('page', 1)
    paginator = Paginator(user_list, 5) # Set 10 users in a page
    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)
    '''


    return render(request, 'users/hr/hr.html', {
        'loggedin_user': api.loggedin_user(request.user),
        'users': users,
        'total_users': total_users,
    })



"""
# Training
@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def trainings(request):

    if not api.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = api.loggedin_user(request.user)
    if not api.is_admin(loggedin_user):
        raise PermissionDenied

    if request.method == 'POST':
        form = TrainingForm(request.POST)
        if form.is_valid():
            training = form.save()
            if training:
                messages.success(request, 'Success! {0} created'.format(training.name))
                return redirect('users:trainings')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'users/trainings/trainings.html', {
        'loggedin_user': api.loggedin_user(request.user),
        'trainings': api.get_trainings(),
        'form': TrainingForm()
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_training(request, slug):

    if not api.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = api.loggedin_user(request.user)
    if not api.is_admin(loggedin_user):
        raise PermissionDenied

    return render(request, 'users/trainings/show_training.html', {
        'loggedin_user': api.loggedin_user(request.user),
        'training': api.get_training(slug)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_training(request, slug):

    if not api.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = api.loggedin_user(request.user)
    if not api.is_admin(loggedin_user):
        raise PermissionDenied

    training = api.get_training(slug)
    if request.method == 'POST':
        form = TrainingForm(request.POST, instance=training)
        if form.is_valid():
            updated_training = form.save()
            if updated_training:
                messages.success(request, 'Success! {0} updated'.format(updated_training.name))
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error!')
    return redirect('users:trainings')


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_training(request):

    if not api.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = api.loggedin_user(request.user)
    if not api.is_admin(loggedin_user):
        raise PermissionDenied

    if request.method == 'POST':
        training_id = request.POST.get('training')
        deleted_training = api.delete_training(training_id)
        if deleted_training:
            messages.success(request, 'Success! {0} deleted'.format(deleted_training.name))
        else:
            messages.error(request, 'Error!')
    return redirect('users:trainings')


# Program

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def programs(request):

    if not api.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = api.loggedin_user(request.user)
    if not api.is_admin(loggedin_user):
        raise PermissionDenied

    if request.method == 'POST':
        form = ProgramForm(request.POST)
        if form.is_valid():
            program = form.save()
            if program:
                messages.success(request, 'Success! {0} created'.format(program.name))
                return redirect('users:programs')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'users/programs/programs.html', {
        'loggedin_user': api.loggedin_user(request.user),
        'programs': api.get_programs(),
        'form': ProgramForm()
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_program(request, slug):

    if not api.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = api.loggedin_user(request.user)
    if not api.is_admin(loggedin_user):
        raise PermissionDenied

    return render(request, 'users/programs/show_program.html', {
        'loggedin_user': api.loggedin_user(request.user),
        'program': api.get_program(slug)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_program(request, slug):

    if not api.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = api.loggedin_user(request.user)
    if not api.is_admin(loggedin_user):
        raise PermissionDenied

    program = api.get_program(slug)
    if request.method == 'POST':
        form = ProgramForm(request.POST, instance=program)
        if form.is_valid():
            updated_program = form.save()
            if updated_program:
                messages.success(request, 'Success! {0} updated'.format(updated_program.name))
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error!')
    return redirect('users:programs')


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_program(request):

    if not api.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = api.loggedin_user(request.user)
    if not api.is_admin(loggedin_user):
        raise PermissionDenied

    if request.method == 'POST':
        program_id = request.POST.get('program')
        deleted_program = api.delete_program(program_id)
        if deleted_program:
            messages.success(request, 'Success! {0} deleted'.format(deleted_program.name))
        else:
            messages.error(request, 'Error!')
    return redirect('users:programs')



# Degree

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def degrees(request):

    if not api.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = api.loggedin_user(request.user)
    if not api.is_admin(loggedin_user):
        raise PermissionDenied

    if request.method == 'POST':
        form = DegreeForm(request.POST)
        if form.is_valid():
            degree = form.save()
            if degree:
                messages.success(request, 'Success! {0} created'.format(degree.name))
                return redirect('users:degrees')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'users/degrees/degrees.html', {
        'loggedin_user': api.loggedin_user(request.user),
        'degrees': api.get_degrees(),
        'form': DegreeForm()
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_degree(request, slug):

    if not api.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = api.loggedin_user(request.user)
    if not api.is_admin(loggedin_user):
        raise PermissionDenied

    return render(request, 'users/degrees/show_degree.html', {
        'loggedin_user': api.loggedin_user(request.user),
        'degree': api.get_degree(slug)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_degree(request, slug):

    if not api.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = api.loggedin_user(request.user)
    if not api.is_admin(loggedin_user):
        raise PermissionDenied

    degree = api.get_degree(slug)
    if request.method == 'POST':
        form = DegreeForm(request.POST, instance=degree)
        if form.is_valid():
            updated_degree = form.save()
            if updated_degree:
                messages.success(request, 'Success! {0} updated'.format(updated_degree.name))
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error!')
    return redirect('users:degrees')


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_degree(request):

    if not api.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = api.loggedin_user(request.user)
    if not api.is_admin(loggedin_user):
        raise PermissionDenied

    if request.method == 'POST':
        degree_id = request.POST.get('degree')
        deleted_degree = api.delete_degree(degree_id)
        if deleted_degree:
            messages.success(request, 'Success! {0} deleted'.format(deleted_degree.name))
        else:
            messages.error(request, 'Error!')
    return redirect('users:degrees')




# Role

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def roles(request):

    if not api.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = api.loggedin_user(request.user)
    if not api.is_admin(loggedin_user):
        raise PermissionDenied

    if request.method == 'POST':
        form = RoleForm(request.POST)
        if form.is_valid():
            role = form.save()
            if role:
                messages.success(request, 'Success! {0} created'.format(role.name))
                return redirect('users:roles')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'users/roles/roles.html', {
        'loggedin_user': api.loggedin_user(request.user),
        'roles': api.get_roles(),
        'form': RoleForm()
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_role(request, slug):

    if not api.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = api.loggedin_user(request.user)
    if not api.is_admin(loggedin_user):
        raise PermissionDenied

    return render(request, 'users/roles/show_role.html', {
        'loggedin_user': api.loggedin_user(request.user),
        'role': api.get_role(slug)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_role(request, slug):

    if not api.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = api.loggedin_user(request.user)
    if not api.is_admin(loggedin_user):
        raise PermissionDenied

    role = api.get_role(slug)
    if request.method == 'POST':
        form = RoleForm(request.POST, instance=role)
        if form.is_valid():
            updated_role = form.save()
            if updated_role:
                messages.success(request, 'Success! {0} updated'.format(updated_role.name))
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error!')
    return redirect('users:roles')



@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_role(request):

    if not api.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = api.loggedin_user(request.user)
    if not api.is_admin(loggedin_user):
        raise PermissionDenied

    if request.method == 'POST':
        role_id = request.POST.get('role')
        deleted_role = api.delete_role(role_id)
        if deleted_role:
            messages.success(request, 'Success! {0} deleted'.format(deleted_role.name))
        else:
            messages.error(request, 'Error!')
    return redirect('users:roles')


# Status

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def statuses(request):

    if not api.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = api.loggedin_user(request.user)
    if not api.is_admin(loggedin_user):
        raise PermissionDenied

    if request.method == 'POST':
        form = StatusForm(request.POST)
        if form.is_valid():
            status = form.save()
            if status:
                messages.success(request, 'Success! {0} created'.format(status.name))
                return redirect('users:statuses')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'users/statuses/statuses.html', {
        'loggedin_user': api.loggedin_user(request.user),
        'statuses': api.get_statuses(),
        'form': StatusForm()
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_status(request, slug):

    if not api.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = api.loggedin_user(request.user)
    if not api.is_admin(loggedin_user):
        raise PermissionDenied

    return render(request, 'users/statuses/show_status.html', {
        'loggedin_user': api.loggedin_user(request.user),
        'status': api.get_status(slug)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_status(request, slug):

    if not api.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = api.loggedin_user(request.user)
    if not api.is_admin(loggedin_user):
        raise PermissionDenied

    status = api.get_status(slug)
    if request.method == 'POST':
        form = StatusForm(request.POST, instance=status)
        if form.is_valid():
            updated_status = form.save()
            if updated_status:
                messages.success(request, 'Success! {0} updated'.format(updated_status.name))
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error!')
    return redirect('users:statuses')


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_status(request):

    if not api.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = api.loggedin_user(request.user)
    if not api.is_admin(loggedin_user):
        raise PermissionDenied

    if request.method == 'POST':
        status_id = request.POST.get('status')
        deleted_status = api.delete_status(status_id)
        if deleted_status:
            messages.success(request, 'Success! {0} deleted'.format(deleted_status.name))
        else:
            messages.error(request, 'Error!')
    return redirect('users:statuses')
"""


"""
@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def submit_confidentiality(request, username):

    if not api.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = api.loggedin_user(request.user)
    if 'Student' not in loggedin_user['roles']:
        raise PermissionDenied

    user = api.get_user_by_username(username)
    if request.method == 'POST':
        print(request.POST)
        print(user.confidentiality, user.confidentiality.sin, user.confidentiality.employee_number)
        form = ConfidentialityForm(request.POST, request.FILES, instance=user.confidentiality)

        if form.is_valid():
            data = form.cleaned_data
            print("data: ", data)


            study_permit = request.FILES.get('study_permit')
            work_permit = request.FILES.get('work_permit')

            print(study_permit, work_permit)

            confidentiality = form.save(commit=False)

            print("1 ", confidentiality.sin, confidentiality.employee_number)
            confidentiality.updated_at = datetime.now()



            if study_permit != None:
                #confidentiality.delete_existing_study_permit_file()
                confidentiality.study_permit = study_permit
            if work_permit != None:
                #confidentiality.delete_existing_work_permit_file()
                confidentiality.work_permit = work_permit

            print("2 ", confidentiality.sin, confidentiality.employee_number)
            confidentiality.save()

            if confidentiality:
                messages.success(request, 'Success! {0} - confidentiality submitted'.format(user.username))
            else:
                messages.error(request, 'Error!')
        else:
            print( form.errors.get_json_data() )
            messages.error(request, 'Error! Form is invalid')

    return HttpResponseRedirect( reverse('users:show_student', args=[username]) )
"""
