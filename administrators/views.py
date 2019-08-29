from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_control

from administrators import api as administratorsApi
from users import api as usersApi
from .models import ApplicationStatus
from .forms import *
from users.forms import *
from datetime import datetime

from django.forms.models import model_to_dict


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def index(request):
    
    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user): raise PermissionDenied

    return render(request, 'administrators/index.html', {
        'loggedin_user': loggedin_user
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def basics(request):
    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user): raise PermissionDenied

    return render(request, 'administrators/basics.html', {
        'loggedin_user': loggedin_user
    })

# ------------- Sessions -------------


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def sessions(request):
    """ Display all information of sessions and create a session """

    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user): raise PermissionDenied

    return render(request, 'administrators/sessions/sessions.html', {
        'loggedin_user': loggedin_user
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def create_session(request):
    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user): raise PermissionDenied

    if request.method == 'POST':
        request.session['session_form_data'] = request.POST
        return redirect('administrators:create_session_confirmation')

    return render(request, 'administrators/sessions/create_session.html', {
        'loggedin_user': loggedin_user,
        'form': SessionForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def create_session_confirmation(request):
    """ Confirm all the inforamtion to create a session """

    if not usersApi.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user):
        raise PermissionDenied

    data = None
    courses = None
    term = None
    if request.method == 'POST':
        form = SessionConfirmationForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            courses = data.get('courses')
            session = form.save()
            if session:
                jobs = api.create_jobs(session, courses)
                if jobs:
                    del request.session['session_form_data'] # remove session form data
                    messages.success(request, 'Success! {0} {1} {2} created'.format(session.year, session.term.code, session.title))
                    return redirect('administrators:current_sessions')
                else:
                    messages.error(request, 'Error!')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')
    else:
        data = request.session.get('session_form_data')
        term_id = data.get('term')
        term = api.get_term(term_id)
        courses = api.get_courses_by_term(term_id)
        data['courses'] = courses

    return render(request, 'administrators/sessions/create_session_confirmation.html', {
        'loggedin_user': loggedin_user,
        'form': SessionConfirmationForm(data=data, initial={
            'term': term
        }),
        'courses': courses
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def current_sessions(request):
    """ Display all information of sessions and create a session """

    if not usersApi.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user):
        raise PermissionDenied

    return render(request, 'administrators/sessions/current_sessions.html', {
        'loggedin_user': loggedin_user,
        'not_archived_sessions': api.get_current_sessions(),
        'form': SessionForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def archived_sessions(request):
    """ Display all information of sessions and create a session """

    if not usersApi.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user):
        raise PermissionDenied

    return render(request, 'administrators/sessions/archived_sessions.html', {
        'loggedin_user': loggedin_user,
        'archived_sessions': api.get_archived_sessions(),
        'form': SessionForm()
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_session(request, session_slug):
    """ Edit a session """

    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user): raise PermissionDenied

    session = api.get_session_by_slug(session_slug)
    session_courses = [ job.course for job in session.job_set.all() ]
    term = session.term

    if request.method == 'POST':
        form = SessionConfirmationForm(request.POST, instance=session)
        if form.is_valid():
            data = form.cleaned_data
            courses = data.get('courses')
            is_archived = data.get('is_archived')
            updated_session = form.save(commit=False)
            updated_session.updated_at = datetime.now()

            if is_archived:
                updated_session.is_visible = False
            form.save()

            if updated_session:
                updated_jobs = api.update_session_jobs(session, courses)
                if updated_jobs:
                    messages.success(request, 'Success! {0} {1} {2} updated'.format(session.year, session.term.code, session.title))
                    return HttpResponseRedirect( reverse('administrators:current_sessions') )
                else:
                    messages.error(request, 'Error!')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'administrators/sessions/edit_session.html', {
        'loggedin_user': loggedin_user,
        'session': session,
        'form': SessionConfirmationForm(data=None, instance=session, initial={
            'courses': session_courses,
            'term': term
        })
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_session(request):
    """ Delete a Session """

    if not usersApi.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user):
        raise PermissionDenied

    if request.method == 'POST':
        session_id = request.POST.get('session')
        deleted = api.delete_session(session_id)
        if deleted:
            messages.success(request, 'Success!')
        else:
            messages.error(request, 'Error!')

    return redirect('administrators:sessions')



# ------------- Jobs -------------

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def jobs(request):
    """ Display all jobs """

    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user): raise PermissionDenied

    return render(request, 'administrators/jobs/jobs.html', {
        'loggedin_user': loggedin_user
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def prepare_jobs(request):

    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user): raise PermissionDenied

    return render(request, 'administrators/jobs/prepare_jobs.html', {
        'loggedin_user': loggedin_user,
        'jobs': api.get_jobs(),
        'instructors': usersApi.get_instructors()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def progress_jobs(request):

    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user): raise PermissionDenied

    return render(request, 'administrators/jobs/progress_jobs.html', {
        'loggedin_user': loggedin_user,
        'jobs': api.get_jobs(),
        'instructors': usersApi.get_instructors()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_job(request, session_slug, job_slug):

    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user): raise PermissionDenied

    session = api.get_session_by_slug(session_slug)
    job = api.get_session_job_by_slug(session_slug, job_slug)
    job_instructors = job.instructors.all()

    if request.method == 'POST':
        form = AdminJobForm(request.POST, instance=job)
        if form.is_valid():
            data = form.cleaned_data
            new_instructors = data.get('instructors')

            updated_job = form.save(commit=False)
            updated_job.updated_at = datetime.now()
            updated_job.save()
            if updated_job:
                updated = api.update_job_instructors(updated_job, job_instructors, new_instructors)
                if updated:
                    messages.success(request, 'Success! {0} {1} {2} {3} {4} updated'.format(updated_job.session.year, updated_job.session.term.code, updated_job.course.code.name, updated_job.course.number.name, updated_job.course.section.name))
                    return redirect('administrators:prepare_jobs')
                else:
                    messages.error(request, 'Error!')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'administrators/jobs/edit_job.html', {
        'loggedin_user': loggedin_user,
        'session': session,
        'job': job,
        'form': AdminJobForm(data=None, instance=job, initial={
            'instructors': job_instructors
        })
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_job(request, session_slug, job_slug):

    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user): raise PermissionDenied

    return render(request, 'administrators/jobs/show_job.html', {
        'loggedin_user': loggedin_user,
        'session': api.get_session_by_slug(session_slug),
        'job': api.get_session_job_by_slug(session_slug, job_slug)
    })


# Applications

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def applications(request):
    """ Display all applicatinos including offered, accepted, declined """

    if not usersApi.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user):
        raise PermissionDenied

    return render(request, 'administrators/applications/applications.html', {
        'loggedin_user': loggedin_user,
        'applications': api.get_applications()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def selected_applications(request):
    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user): raise PermissionDenied

    return render(request, 'administrators/applications/selected_applications.html', {
        'loggedin_user': loggedin_user,
        'selected_applications': api.get_selected_applications(),
        'admin_application_form': AdminApplicationForm(),
        'status_form': ApplicationStatusForm(initial={
            'assigned': ApplicationStatus.OFFERED
        })
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_job_application(request, session_slug, job_slug):
    """ Edit classification and note """

    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user): raise PermissionDenied

    if request.method == 'POST':
        application_id = request.POST.get('application')
        form = AdminApplicationForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            updated_application = api.update_application_classification_note(application_id, data)
            if updated_application:
                messages.success(request, 'Success! {0} - application updated'.format(updated_application.applicant.username))
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error!')

    return redirect('administrators:selected_applications')

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def offer_job(request, session_slug, job_slug):
    """ Admin can offer a job to each job"""

    if not usersApi.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user):
        raise PermissionDenied

    job = api.get_session_job_by_slug(session_slug, job_slug)
    if request.method == 'POST':
        applicant_id = request.POST.get('applicant')
        assigned_hours = request.POST.get('assigned_hours')
        form = ApplicationStatusForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            status = form.save()
            if status:
                application = api.get_application_by_student_id_job(applicant_id, job)
                application.status.add(status)
                application.save()
                if application:
                    messages.success(request, 'Success! You offered {0} {1} hours for this job'.format(application.applicant.username, assigned_hours))
                else:
                    messages.error(request, 'Error!')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return redirect('administrators:selected_applications')




@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def offered_applications(request):
    if not usersApi.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user):
        raise PermissionDenied

    # add email lists

    return render(request, 'administrators/applications/offered_applications.html', {
        'loggedin_user': loggedin_user,
        'offered_applications': api.get_offered_applications()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def accepted_applications(request):
    if not usersApi.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user):
        raise PermissionDenied

    accepted_applications = api.get_selected_applications()
    print(accepted_applications)
    return render(request, 'administrators/applications/accepted_applications.html', {
        'loggedin_user': loggedin_user,
        'accepted_applications': api.get_accepted_applications(),
        'admin_application_form': AdminApplicationForm()
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def declined_applications(request):
    if not usersApi.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user):
        raise PermissionDenied

    return render(request, 'administrators/applications/declined_applications.html', {
        'loggedin_user': loggedin_user,
        'declined_applications': api.get_declined_applications()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_application(request, app_slug):

    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user): raise PermissionDenied

    return render(request, 'administrators/applications/show_application.html', {
        'loggedin_user': usersApi.loggedin_user(request.user),
        'app': api.get_application_slug(app_slug),
        'form': AdminApplicationForm(initial={
            'assigned': ApplicationStatus.OFFERED
        })
    })

# HR

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def hr(request):

    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user): raise PermissionDenied

    users = api.get_users()
    return render(request, 'administrators/hr/hr.html', {
        'loggedin_user': api.loggedin_user(request.user),
        'users': users,
        'total_users': len(users),
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def users(request):

    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user): raise PermissionDenied

    users = usersApi.get_users()
    return render(request, 'administrators/hr/users.html', {
        'loggedin_user': loggedin_user,
        'users': users,
        'total_users': len(users),
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def create_user(request):
    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user): raise PermissionDenied

    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save()
            if user:
                profile = usersApi.create_profile(user)
                if profile:
                    resume = usersApi.create_user_resume(user)
                    if resume:
                        confidentiality = usersApi.create_user_confidentiality(user)
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

    return render(request, 'administrators/hr/create_user.html', {
        'loggedin_user': loggedin_user,
        'users': usersApi.get_users(),
        'user_form': UserForm()
    })




# Courses

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def courses(request):
    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user): raise PermissionDenied

    return render(request, 'administrators/courses/courses.html', {
        'loggedin_user': loggedin_user,
        'courses': api.get_courses()
    })
# LFS 100 001	W1
@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def create_course(request):
    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user): raise PermissionDenied

    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            if course:
                messages.success(request, 'Success! {0} {1} {2} {3} created'.format(course.code.name, course.number.name, course.section.name, course.term.code))
                return redirect('administrators:courses')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'administrators/courses/create_course.html', {
        'loggedin_user': loggedin_user,
        'form': CourseForm()
    })

#checked
def edit_course(request, course_slug):
    """ Edit a course """
    course = api.get_course_by_slug(course_slug)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            updated_course = form.save()
            if updated_course:
                messages.success(request, 'Success! {0} {1} {2} {3} updated'.format(updated_course.code.name, updated_course.number.name, updated_course.section.name, updated_course.term.code))
                return redirect('administrators:courses')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'administrators/courses/edit_course.html', {
        'loggedin_user': usersApi.loggedin_user(request.user),
        'course': course,
        'form': CourseForm(data=None, instance=course)
    })

#checked
def delete_course(request):
    """ Delete a course """
    if request.method == 'POST':
        course_id = request.POST.get('course')
        deleted = api.delete_course(course_id)
        if deleted:
            messages.success(request, 'Success!')
        else:
            messages.error(request, 'Error!')

    return redirect("administrators:courses")


# Terms

#checked
def terms(request):
    """ Display all terms and create a term """
    if request.method == 'POST':
        form = TermForm(request.POST)
        if form.is_valid():
            term = form.save()
            if term:
                messages.success(request, 'Success!')
                return redirect('administrators:terms')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'administrators/terms/terms.html', {
        'loggedin_user': usersApi.loggedin_user(request.user),
        'terms': api.get_terms(),
        'form': TermForm()
    })

#checked
def show_term(request, code):
    """ Display term details """
    return render(request, 'administrators/terms/show_term.html', {
        'loggedin_user': usersApi.loggedin_user(request.user),
        'term': api.get_term_by_code(code)
    })

#checked
def edit_term(request, code):
    """ Edit a term """
    term = api.get_term_by_code(code)
    if request.method == 'POST':
        form = TermForm(request.POST, instance=term)
        if form.is_valid():
            updated_term = form.save()
            if updated_term:
                messages.success(request, 'Success!')
                return HttpResponseRedirect( reverse('administrators:show_course', args=[updated_term.slug]) )
            else:
                messages.error(request, 'Error!')

    return render(request, 'administrators/terms/edit_term.html', {
        'loggedin_user': usersApi.loggedin_user(request.user),
        'term': term,
        'form': TermForm(data=None, instance=term)
    })

#checked
def delete_term(request):
    """ Delete a term """
    if request.method == 'POST':
        term_id = request.POST.get('term')
        deleted = api.delete_term(term_id)
        if deleted:
            messages.success(request, 'Success!')
        else:
            messages.error(request, 'Error!')

    return redirect("administrators:terms")


def course_codes(request):
    if request.method == 'POST':
        form = CourseCodeForm(request.POST)
        if form.is_valid():
            course_code = form.save()
            if course_code:
                messages.success(request, 'Success!')
                return redirect('administrators:course_codes')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'administrators/course_codes/course_codes.html', {
        'loggedin_user': usersApi.loggedin_user(request.user),
        'course_codes': api.get_course_codes(),
        'form': CourseCodeForm()
    })

def show_course_code(request, name):
    return render(request, 'administrators/course_codes/show_course_code.html', {
        'loggedin_user': usersApi.loggedin_user(request.user),
        'course_code': api.get_course_code(name)
    })

def edit_course_code(request, name):
    course_code = api.get_course_code(name)
    if request.method == 'POST':
        form = CourseCodeForm(request.POST, instance=course_code)
        if form.is_valid():
            updated_course_code = form.save()
            if updated_course_code:
                messages.success(request, 'Success!')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error!')
    return redirect('administrators:course_codes')


def delete_course_code(request):
    if request.method == 'POST':
        course_code_id = request.POST.get('course_code')
        deleted = api.delete_course_code(course_code_id)
        if deleted:
            messages.success(request, 'Success!')
        else:
            messages.error(request, 'Error!')
    return redirect('administrators:course_codes')

# Course Number

def course_numbers(request):
    if request.method == 'POST':
        form = CourseNumberForm(request.POST)
        if form.is_valid():
            course_number = form.save()
            if course_number:
                messages.success(request, 'Success!')
                return redirect('administrators:course_numbers')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'administrators/course_numbers/course_numbers.html', {
        'loggedin_user': usersApi.loggedin_user(request.user),
        'course_numbers': api.get_course_numbers(),
        'form': CourseNumberForm()
    })

def show_course_number(request, name):
    return render(request, 'administrators/course_numbers/show_course_number.html', {
        'loggedin_user': usersApi.loggedin_user(request.user),
        'course_number': api.get_course_number(name)
    })

def edit_course_number(request, name):
    course_number = api.get_course_number(name)
    if request.method == 'POST':
        form = CourseNumberForm(request.POST, instance=course_number)
        if form.is_valid():
            updated_course_number = form.save()
            if updated_course_number:
                messages.success(request, 'Success!')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error!')
    return redirect('administrators:course_numbers')


def delete_course_number(request):
    if request.method == 'POST':
        course_number_id = request.POST.get('course_number')
        deleted = api.delete_course_number(course_number_id)
        if deleted:
            messages.success(request, 'Success!')
        else:
            messages.error(request, 'Error!')
    return redirect('administrators:course_numbers')

# Course Section

def course_sections(request):
    if request.method == 'POST':
        form = CourseSectionForm(request.POST)
        if form.is_valid():
            course_section = form.save()
            if course_section:
                messages.success(request, 'Success!')
                return redirect('administrators:course_sections')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'administrators/course_sections/course_sections.html', {
        'loggedin_user': usersApi.loggedin_user(request.user),
        'course_sections': api.get_course_sections(),
        'form': CourseSectionForm()
    })

def show_course_section(request, name):
    return render(request, 'administrators/course_sections/show_course_section.html', {
        'loggedin_user': usersApi.loggedin_user(request.user),
        'course_section': api.get_course_section(name)
    })

def edit_course_section(request, name):
    course_section = api.get_course_section(name)
    if request.method == 'POST':
        form = CourseSectionForm(request.POST, instance=course_section)
        if form.is_valid():
            updated_course_section = form.save()
            if updated_course_section:
                messages.success(request, 'Success!')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error!')
    return redirect('administrators:course_sections')

def delete_course_section(request):
    if request.method == 'POST':
        course_section_id = request.POST.get('course_section')
        deleted = api.delete_course_section(course_section_id)
        if deleted:
            messages.success(request, 'Success!')
        else:
            messages.error(request, 'Error!')
    return redirect('administrators:course_sections')




# to be removed

def temp_show_course(request, course_slug):
    """ Display course details """
    return render(request, 'administrators/courses/show_course.html', {
        'loggedin_user': usersApi.loggedin_user(request.user),
        'course': api.get_course_by_slug(course_slug)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def temp_show_session(request, session_slug):
    """ Display session details """

    if not usersApi.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user):
        raise PermissionDenied

    session = api.get_session_by_slug(session_slug)
    return render(request, 'administrators/sessions/show_session.html', {
        'loggedin_user': loggedin_user,
        'session': session
    })




"""
def create_session(request):
    pass

    form = SessionForm(data)
    if form.is_valid():
        cleaned_data = form.cleaned_data
        courses = api.get_courses_by_term(cleaned_data['term'].code)
        session = form.save()

        if session:
            jobs = api.create_jobs(session, courses)
            if jobs:
                messages.success(request, 'Success!')
                return redirect('administrators:sessions')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error!')
        return render(request, 'administrators/sessions/create_session_confirmation.html', {
            'loggedin_user': usersApi.loggedin_user(request.user)
        })

    else:
        messages.error(request, 'Error! Form is invalid')

    return redirect('administrators:sessions')
    """



"""

def edit_course(request, course_slug):
    course = api.get_course_by_slug(course_slug)
    course_instructors = course.instructors.all()

    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        print("valid ", form.is_valid())
        if form.is_valid():
            data = form.cleaned_data
            updated_course = form.save(commit=False)
            updated_course.updated_at = datetime.now()
            form.save()

            # Remove current instructors
            updated_course.instructors.remove( *course_instructors )

            # Add new instructors
            new_instructors = list( data.get('instructors') )
            updated_course.instructors.add( *new_instructors )
            if updated_course:
                messages.success(request, 'Success!')
                return HttpResponseRedirect( reverse('administrators:show_course', args=[updated_course.slug]) )
            else:
                messages.error(request, 'Error!')

    return render(request, 'administrators/edit_course.html', {
        'loggedin_user': usersApi.loggedin_user(request.user),
        'course': course,
        'form': CourseForm(data=None, instance=course)
    })

"""


"""
@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def assign_ta_hours(request, session_slug, job_slug):
    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user): raise PermissionDenied

    job = api.get_session_job_by_slug(session_slug, job_slug)
    if request.method == 'POST':
        form = AssignedTaHoursForm(request.POST, instance=job)
        if form.is_valid():
            data = form.cleaned_data
            assigned_ta_hours = data.get('assigned_ta_hours')
            updated_job = form.save(commit=False)
            updated_job.assigned_ta_hours = assigned_ta_hours
            updated_job.updated_at = datetime.now()
            updated_job.save()
            if updated_job:
                messages.success(request, 'Success! {0} TA Hours assigned to {1} {2} - {3} {4} {5}'.format(assigned_ta_hours, updated_job.session.year, updated_job.session.term.code, updated_job.course.code.name, updated_job.course.number.name, updated_job.course.section.name))
            else:
                messages.error(request, 'Error!')
        else:
            print(form.errors.get_json_data())
            messages.error(request, 'Error! Form is invalid')
    return redirect('administrators:prepare_jobs')


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def add_instructors(request, session_slug, job_slug):
    if not usersApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user): raise PermissionDenied

    job = api.get_session_job_by_slug(session_slug, job_slug)
    job_instructors = job.instructors.all()
    if request.method == 'POST':
        form = AddInstructorForm(request.POST, instance=job)
        if form.is_valid():
            data = form.cleaned_data
            new_instructors = data.get('instructors')
            updated_job = form.save(commit=False)
            updated_job.updated_at = datetime.now()
            updated_job.save()
            if updated_job:
                updated = api.update_job_instructors(updated_job, job_instructors, new_instructors)
                if updated:
                    messages.success(request, 'Success! {0} {1} {2} {3} {4} updated'.format(updated_job.session.year, updated_job.session.term.code, updated_job.course.code.name, updated_job.course.number.name, updated_job.course.section.name))
                else:
                    messages.error(request, 'Error!')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')
    return redirect('administrators:jobs')
"""
