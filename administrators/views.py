from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_control

from administrators.models import ApplicationStatus
from administrators.forms import *
from administrators import api as adminApi

from users.forms import *
from users import api as userApi

from datetime import datetime

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def index(request):
    ''' index page of Administrator's portal '''
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    return render(request, 'administrators/index.html', {
        'loggedin_user': loggedin_user
    })

# Courses

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def courses(request):
    if not userApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    return render(request, 'administrators/courses/courses.html', {
        'loggedin_user': loggedin_user,
        'courses': adminApi.get_courses()
    })
# LFS 100 001	W1
@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def create_course(request):
    if not userApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

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

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def all_courses(request):
    if not userApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    return render(request, 'administrators/courses/all_courses.html', {
        'loggedin_user': loggedin_user,
        'courses': adminApi.get_courses()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_course(request, course_slug):
    """ Edit a course """
    course = adminApi.get_course_by_slug(course_slug)
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
        'loggedin_user': userApi.loggedin_user(request.user),
        'course': course,
        'form': CourseForm(data=None, instance=course)
    })

#checked
def delete_course(request):
    """ Delete a course """
    if request.method == 'POST':
        course_id = request.POST.get('course')
        deleted = adminApi.delete_course(course_id)
        if deleted:
            messages.success(request, 'Success!')
        else:
            messages.error(request, 'Error!')

    return redirect("administrators:courses")


# ------------- Sessions -------------


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def sessions(request):
    """ Display all information of sessions and create a session """

    if not userApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    return render(request, 'administrators/sessions/sessions.html', {
        'loggedin_user': loggedin_user
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def create_session(request):
    if not userApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

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

    if not userApi.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user):
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
                jobs = adminApi.create_jobs(session, courses)
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
        term = adminApi.get_term(term_id)
        courses = adminApi.get_courses_by_term(term_id)
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

    if not userApi.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user):
        raise PermissionDenied

    return render(request, 'administrators/sessions/current_sessions.html', {
        'loggedin_user': loggedin_user,
        'not_archived_sessions': adminApi.get_current_sessions(),
        'form': SessionForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def archived_sessions(request):
    """ Display all information of sessions and create a session """

    if not userApi.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user):
        raise PermissionDenied

    return render(request, 'administrators/sessions/archived_sessions.html', {
        'loggedin_user': loggedin_user,
        'archived_sessions': adminApi.get_archived_sessions(),
        'form': SessionForm()
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_session(request, session_slug):
    """ Edit a session """

    if not userApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    session = adminApi.get_session_by_slug(session_slug)
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
                updated_jobs = adminApi.update_session_jobs(session, courses)
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

    if not userApi.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user):
        raise PermissionDenied

    if request.method == 'POST':
        session_id = request.POST.get('session')
        deleted = adminApi.delete_session(session_id)
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

    if not userApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    return render(request, 'administrators/jobs/jobs.html', {
        'loggedin_user': loggedin_user
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def prepare_jobs(request):

    if not userApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    return render(request, 'administrators/jobs/prepare_jobs.html', {
        'loggedin_user': loggedin_user,
        'jobs': adminApi.get_jobs(),
        'instructors': userApi.get_instructors()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def progress_jobs(request):

    if not userApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    return render(request, 'administrators/jobs/progress_jobs.html', {
        'loggedin_user': loggedin_user,
        'jobs': adminApi.get_jobs(),
        'instructors': userApi.get_instructors()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def student_jobs(request):
    if not userApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    return render(request, 'administrators/jobs/student_jobs.html', {
        'loggedin_user': loggedin_user,
        'students': userApi.get_students()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def instructor_jobs(request):
    if not userApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    return render(request, 'administrators/jobs/instructor_jobs.html', {
        'loggedin_user': loggedin_user,
        'instructors': userApi.get_instructors()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def instructor_jobs_details(request, username):
    if not userApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied
    instructor = userApi.get_user_by_username(username)
    return render(request, 'administrators/jobs/instructor_jobs_details.html', {
        'loggedin_user': loggedin_user,
        'instructor': instructor
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_job(request, session_slug, job_slug):

    if not userApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    session = adminApi.get_session_by_slug(session_slug)
    job = adminApi.get_session_job_by_slug(session_slug, job_slug)
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
                updated = adminApi.update_job_instructors(updated_job, job_instructors, new_instructors)
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

    if not userApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    return render(request, 'administrators/jobs/show_job.html', {
        'loggedin_user': loggedin_user,
        'session': adminApi.get_session_by_slug(session_slug),
        'job': adminApi.get_session_job_by_slug(session_slug, job_slug)
    })


# Applications

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def applications(request):
    """ Display all applicatinos including offered, accepted, declined """

    if not userApi.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user):
        raise PermissionDenied

    return render(request, 'administrators/applications/applications.html', {
        'loggedin_user': loggedin_user,
        'applications': adminApi.get_applications()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def selected_applications(request):
    if not userApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    return render(request, 'administrators/applications/selected_applications.html', {
        'loggedin_user': loggedin_user,
        'selected_applications': adminApi.get_selected_applications(),
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

    if not userApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    if request.method == 'POST':
        application_id = request.POST.get('application')
        form = AdminApplicationForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            updated_application = adminApi.update_application_classification_note(application_id, data)
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

    if not userApi.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user):
        raise PermissionDenied

    job = adminApi.get_session_job_by_slug(session_slug, job_slug)
    if request.method == 'POST':
        applicant_id = request.POST.get('applicant')
        assigned_hours = request.POST.get('assigned_hours')
        form = ApplicationStatusForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            status = form.save()
            if status:
                application = adminApi.get_application_by_student_id_job(applicant_id, job)
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
    if not userApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    return render(request, 'administrators/applications/offered_applications.html', {
        'loggedin_user': loggedin_user,
        'offered_applications': adminApi.get_offered_applications()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def offered_applications_send_email(request):
    if not userApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    if request.method == 'POST':
        applications = request.POST.getlist('application')
        print( applications )
        request.session['offered_applications_form_data'] = applications
        return redirect('administrators:offered_applications_send_email_confirmation')

    return redirect('administrators:offered_applications')

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def offered_applications_send_email_confirmation(request):
    if not userApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    form_data = request.session.get('offered_applications_form_data')
    applications = []
    receiver_list = []
    for data in form_data:
        app = adminApi.get_application(data)
        applications.append(app)
        receiver_list.append(app.applicant.email)

    if request.method == 'POST':
        form = EmailForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            count = 0
            for app in applications:
                name = app.applicant.first_name + ' ' + app.applicant.last_name
                job = app.job.session.year + ' ' + app.job.session.term.code + ' ' + app.job.course.code.name + ' ' + app.job.course.number.name + ' ' + app.job.course.section.name
                assigned_hours = 0.0
                for st in app.status.all():
                    if st.assigned == ApplicationStatus.OFFERED:
                        assigned_hours = st.assigned_hours

                message = data['message'].format(name, job, assigned_hours, app.get_classification_display(), settings.TA_APP_URL)

                # TODO: replace a receiver
                receiver = '{0} <brandon.oh@ubc.ca>'.format(name)
                #receiver = '{0} <{1}>'.format(name, app.applicant.email)

                email = adminApi.send_and_create_email(data['sender'], receiver, data['title'], message, data['type'])
                if email: count += 1

            if count == len(applications):
                messages.success(request, 'Success! Email has sent to {0}'.format( data['receiver'] ))
            else:
                messages.error(request, 'Error!')

            del request.session['offered_applications_form_data']
            return redirect('administrators:offered_applications')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'administrators/applications/offered_applications_send_email_confirmation.html', {
        'loggedin_user': loggedin_user,
        'applications': applications,
        'sender': settings.EMAIL_FROM,
        'receiver': receiver_list
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def email_history(request):
    if not userApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied
    if request.method == 'POST':
        form = EmailForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            email = adminApi.send_and_create_email(data['sender'], data['receiver'], data['title'], data['message'], data['type'])
            if email:
                messages.success(request, 'Success! Email has sent to {0}'.format(data['receiver']))
                return redirect('administrators:email_history')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'administrators/applications/email_history.html', {
        'loggedin_user': loggedin_user,
        'emails': adminApi.get_emails()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def accepted_applications(request):
    if not userApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    accepted_applications = adminApi.get_selected_applications()
    return render(request, 'administrators/applications/accepted_applications.html', {
        'loggedin_user': loggedin_user,
        'accepted_applications': adminApi.get_accepted_applications(),
        'admin_application_form': AdminApplicationForm()
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def declined_applications(request):
    if not userApi.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user):
        raise PermissionDenied

    return render(request, 'administrators/applications/declined_applications.html', {
        'loggedin_user': loggedin_user,
        'declined_applications': adminApi.get_declined_applications()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_application(request, app_slug):

    if not userApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    return render(request, 'administrators/applications/show_application.html', {
        'loggedin_user': userApi.loggedin_user(request.user),
        'app': adminApi.get_application_slug(app_slug),
        'form': AdminApplicationForm(initial={
            'assigned': ApplicationStatus.OFFERED
        })
    })

# HR

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def hr(request):

    if not userApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    users = api.get_users()
    return render(request, 'administrators/hr/hr.html', {
        'loggedin_user': api.loggedin_user(request.user),
        'users': users,
        'total_users': len(users),
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def create_user(request):
    if not userApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save()
            if user:
                profile = userApi.create_profile(user, request.POST)
                if profile:
                    messages.success(request, 'Success! New user - CWL: {0} created. Please check at All Users'.format(user.username))
                    return redirect('administrators:create_user')
                else:
                    messages.error(request, 'Error! at profile')
            else:
                messages.error(request, 'Error! at user')
        else:
            messages.error(request, 'Error! form invalid')

    return render(request, 'administrators/hr/create_user.html', {
        'loggedin_user': loggedin_user,
        'users': userApi.get_users(),
        'roles': userApi.get_roles(),
        'user_form': UserForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def create_user2(request):
    if not userApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save()
            if user:
                profile = userApi.create_profile(user)
                if profile:
                    resume = userApi.create_user_resume(user)
                    if resume:
                        confidentiality = userApi.create_user_confidentiality(user)
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
        'users': userApi.get_users(),
        'user_form': UserForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def users(request):

    if not userApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    if request.method == 'POST':
        user_id = request.POST.get('user')
        user = userApi.get_user(user_id)
        profile_roles = user.profile.roles.all()

        form = ProfileRoleForm(request.POST, instance=user.profile)
        if form.is_valid():
            data = form.cleaned_data
            updated_profile = form.save(commit=False)
            updated_profile.updated_at = datetime.now()
            updated_profile.save()
            if updated_profile:
                updated = userApi.update_user_profile_roles(updated_profile, profile_roles, data)
                if updated:
                    messages.success(request, 'Success! {0} - roles updated'.format(user.username))
                    return redirect('administrators:users')
                else:
                    messages.error(request, 'Error!')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! form invalid')


    users = userApi.get_users()
    return render(request, 'administrators/hr/users.html', {
        'loggedin_user': loggedin_user,
        'users': users,
        'total_users': len(users),
        'roles': userApi.get_roles()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_user(request, username):

    if not userApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    user = userApi.get_user_by_username(username)
    resume_file = None
    if userApi.has_user_resume_created(user) and user.resume.file != None:
        resume_file = os.path.basename(user.resume.file.name)

    return render(request, 'administrators/hr/show_user.html', {
        'loggedin_user': loggedin_user,
        'user': user,
        'resume_file': resume_file,
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def view_confidentiality(request):

    if not userApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    return render(request, 'administrators/hr/view_confidentiality.html', {
        'loggedin_user': loggedin_user,
        'users': userApi.get_users(),
    })


# ------------- Preparation -------------

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def preparation(request):
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    return render(request, 'administrators/preparation/preparation.html', {
        'loggedin_user': loggedin_user
    })

# Terms
@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def terms(request):
    ''' Display all terms and create a term '''
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    if request.method == 'POST':
        form = TermForm(request.POST)
        if form.is_valid():
            term = form.save()
            if term:
                messages.success(request, 'Success! {0} ({1}) created'.format(term.name, term.code))
                return redirect('administrators:terms')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'administrators/preparation/terms.html', {
        'loggedin_user': loggedin_user,
        'terms': adminApi.get_terms(),
        'form': TermForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_term(request, code):
    ''' Edit a term '''
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    if request.method == 'POST':
        term = adminApi.get_term_by_code(code)
        form = TermForm(request.POST, instance=term)
        if form.is_valid():
            updated_term = form.save()
            if updated_term:
                messages.success(request, 'Success! {0} ({1}) updated'.format(updated_term.name, updated_term.code))
            else:
                messages.error(request, 'Error!')
        else:
            print(form.errors.get_json_data())
            messages.error(request, 'Error! Form is invalid')
    return redirect("administrators:terms")

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_term(request):
    ''' Delete a term '''
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    if request.method == 'POST':
        term_id = request.POST.get('term')
        deleted_term = adminApi.delete_term(term_id)
        if deleted_term:
            messages.success(request, 'Success! {0} ({1}) deleted'.format(deleted_term.name, deleted_term.code))
        else:
            messages.error(request, 'Error!')
    return redirect("administrators:terms")

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def course_codes(request):
    ''' Display all course codes and create a course code '''
    print('course_codes')
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    if request.method == 'POST':
        form = CourseCodeForm(request.POST)
        if form.is_valid():
            course_code = form.save()
            if course_code:
                messages.success(request, 'Success! {0} created'.format(course_code.name))
                return redirect('administrators:course_codes')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'administrators/preparation/course_codes.html', {
        'loggedin_user': loggedin_user,
        'course_codes': adminApi.get_course_codes(),
        'form': CourseCodeForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_course_code(request, name):
    ''' Edit a course code '''
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    if request.method == 'POST':
        course_code = adminApi.get_course_code_by_name(name)
        form = CourseCodeForm(request.POST, instance=course_code)
        if form.is_valid():
            updated_course_code = form.save()
            if updated_course_code:
                messages.success(request, 'Success! {0} updated'.format(updated_course_code.name))
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error!')
    return redirect('administrators:course_codes')

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_course_code(request):
    ''' '''
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    if request.method == 'POST':
        course_code_id = request.POST.get('course_code')
        deleted_course_code = adminApi.delete_course_code(course_code_id)
        if deleted_course_code:
            messages.success(request, 'Success! {0} deleted'.format(deleted_course_code.name))
        else:
            messages.error(request, 'Error!')
    return redirect('administrators:course_codes')



# Course Number

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def course_numbers(request):
    ''' '''
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    if request.method == 'POST':
        form = CourseNumberForm(request.POST)
        if form.is_valid():
            course_number = form.save()
            if course_number:
                messages.success(request, 'Success! {0} created'.format(course_number.name))
                return redirect('administrators:course_numbers')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'administrators/preparation/course_numbers.html', {
        'loggedin_user': userApi.loggedin_user(request.user),
        'course_numbers': adminApi.get_course_numbers(),
        'form': CourseNumberForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_course_number(request, name):
    ''' '''
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    if request.method == 'POST':
        course_number = adminApi.get_course_number_by_name(name)
        form = CourseNumberForm(request.POST, instance=course_number)
        if form.is_valid():
            updated_course_number = form.save()
            if updated_course_number:
                messages.success(request, 'Success! {0} updated'.format(updated_course_number.name))
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error!')
    return redirect('administrators:course_numbers')

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_course_number(request):
    ''' '''
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    if request.method == 'POST':
        course_number_id = request.POST.get('course_number')
        deleted_course_number = adminApi.delete_course_number(course_number_id)
        if deleted_course_number:
            messages.success(request, 'Success! {0} deleted'.format(deleted_course_number.name))
        else:
            messages.error(request, 'Error!')
    return redirect('administrators:course_numbers')

# Course Section

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def course_sections(request):
    ''' '''
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    if request.method == 'POST':
        form = CourseSectionForm(request.POST)
        if form.is_valid():
            course_section = form.save()
            if course_section:
                messages.success(request, 'Success! {0} created'.format(course_section.name))
                return redirect('administrators:course_sections')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'administrators/preparation/course_sections.html', {
        'loggedin_user': userApi.loggedin_user(request.user),
        'course_sections': adminApi.get_course_sections(),
        'form': CourseSectionForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_course_section(request, name):
    ''' '''
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    if request.method == 'POST':
        course_section = adminApi.get_course_section_by_name(name)
        form = CourseSectionForm(request.POST, instance=course_section)
        if form.is_valid():
            updated_course_section = form.save()
            if updated_course_section:
                messages.success(request, 'Success! {0} updated'.format(updated_course_section.name))
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error!')
    return redirect('administrators:course_sections')

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_course_section(request):
    ''' '''
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    if request.method == 'POST':
        course_section_id = request.POST.get('course_section')
        deleted_course_section = adminApi.delete_course_section(course_section_id)
        if deleted_course_section:
            messages.success(request, 'Success! {0} deleted'.format(deleted_course_section.name))
        else:
            messages.error(request, 'Error!')
    return redirect('administrators:course_sections')


# Roles

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def roles(request):
    ''' Display all roles and create a role '''
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    if request.method == 'POST':
        form = RoleForm(request.POST)
        if form.is_valid():
            role = form.save()
            if role:
                messages.success(request, 'Success! {0} created'.format(role.name))
                return redirect('administrators:roles')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'administrators/preparation/roles.html', {
        'loggedin_user': loggedin_user,
        'roles': userApi.get_roles(),
        'form': RoleForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_role(request, slug):
    ''' Edit a role '''
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    if request.method == 'POST':
        role = userApi.get_role_by_slug(slug)
        form = RoleForm(request.POST, instance=role)
        if form.is_valid():
            updated_role = form.save()
            if updated_role:
                messages.success(request, 'Success! {0} updated'.format(updated_role.name))
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')
    return redirect("administrators:roles")

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_role(request):
    ''' Delete a role '''
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    if request.method == 'POST':
        role_id = request.POST.get('role')
        deleted_role = userApi.delete_role(role_id)
        if deleted_role:
            messages.success(request, 'Success! {0} deleted'.format(deleted_role.name))
        else:
            messages.error(request, 'Error!')
    return redirect("administrators:roles")



# Statuses

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def statuses(request):
    ''' Display all statuses and create a status '''
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    if request.method == 'POST':
        form = StatusForm(request.POST)
        if form.is_valid():
            status = form.save()
            if status:
                messages.success(request, 'Success! {0} created'.format(status.name))
                return redirect('administrators:statuses')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'administrators/preparation/statuses.html', {
        'loggedin_user': loggedin_user,
        'statuses': userApi.get_statuses(),
        'form': StatusForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_status(request, slug):
    ''' Edit a status '''
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    if request.method == 'POST':
        status = userApi.get_status_by_slug(slug)
        form = StatusForm(request.POST, instance=status)
        if form.is_valid():
            updated_status = form.save()
            if updated_status:
                messages.success(request, 'Success! {0} updated'.format(updated_status.name))
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')
    return redirect("administrators:statuses")

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_status(request):
    ''' Delete a status '''
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    if request.method == 'POST':
        status_id = request.POST.get('status')
        deleted_status = userApi.delete_status(status_id)
        if deleted_status:
            messages.success(request, 'Success! {0} deleted'.format(deleted_status.name))
        else:
            messages.error(request, 'Error!')
    return redirect("administrators:statuses")



# Programs

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def programs(request):
    ''' Display all programs and create a program '''
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    if request.method == 'POST':
        form = ProgramForm(request.POST)
        if form.is_valid():
            program = form.save()
            if program:
                messages.success(request, 'Success! {0} created'.format(program.name))
                return redirect('administrators:programs')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'administrators/preparation/programs.html', {
        'loggedin_user': loggedin_user,
        'programs': userApi.get_programs(),
        'form': ProgramForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_program(request, slug):
    ''' Edit a program '''
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    if request.method == 'POST':
        program = userApi.get_program_by_slug(slug)
        form = ProgramForm(request.POST, instance=program)
        if form.is_valid():
            updated_program = form.save()
            if updated_program:
                messages.success(request, 'Success! {0} updated'.format(updated_program.name))
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')
    return redirect("administrators:programs")

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_program(request):
    ''' Delete a program '''
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    if request.method == 'POST':
        program_id = request.POST.get('program')
        deleted_program = userApi.delete_program(program_id)
        if deleted_program:
            messages.success(request, 'Success! {0} deleted'.format(deleted_program.name))
        else:
            messages.error(request, 'Error!')
    return redirect("administrators:programs")


# Degrees

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def degrees(request):
    ''' Display all degrees and create a degree '''
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    if request.method == 'POST':
        form = DegreeForm(request.POST)
        if form.is_valid():
            degree = form.save()
            if degree:
                messages.success(request, 'Success! {0} created'.format(degree.name))
                return redirect('administrators:degrees')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'administrators/preparation/degrees.html', {
        'loggedin_user': loggedin_user,
        'degrees': userApi.get_degrees(),
        'form': DegreeForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_degree(request, slug):
    ''' Edit a degree '''
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    if request.method == 'POST':
        degree = userApi.get_degree_by_slug(slug)
        form = DegreeForm(request.POST, instance=degree)
        if form.is_valid():
            updated_degree = form.save()
            if updated_degree:
                messages.success(request, 'Success! {0} updated'.format(updated_degree.name))
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')
    return redirect("administrators:degrees")

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_degree(request):
    ''' Delete a degree '''
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    if request.method == 'POST':
        degree_id = request.POST.get('degree')
        deleted_degree = userApi.delete_degree(degree_id)
        if deleted_degree:
            messages.success(request, 'Success! {0} deleted'.format(deleted_degree.name))
        else:
            messages.error(request, 'Error!')
    return redirect("administrators:degrees")


# Trainings

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def trainings(request):
    ''' Display all trainings and create a training '''
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    if request.method == 'POST':
        form = TrainingForm(request.POST)
        if form.is_valid():
            training = form.save()
            if training:
                messages.success(request, 'Success! {0} created'.format(training.name))
                return redirect('administrators:trainings')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'administrators/preparation/trainings.html', {
        'loggedin_user': loggedin_user,
        'trainings': userApi.get_trainings(),
        'form': TrainingForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_training(request, slug):
    ''' Edit a training '''
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    if request.method == 'POST':
        training = userApi.get_training_by_slug(slug)
        form = TrainingForm(request.POST, instance=training)
        if form.is_valid():
            updated_training = form.save()
            if updated_training:
                messages.success(request, 'Success! {0} updated'.format(updated_training.name))
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')
    return redirect("administrators:trainings")

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_training(request):
    ''' Delete a training '''
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

    if request.method == 'POST':
        training_id = request.POST.get('training')
        deleted_training = userApi.delete_training(training_id)
        if deleted_training:
            messages.success(request, 'Success! {0} deleted'.format(deleted_training.name))
        else:
            messages.error(request, 'Error!')
    return redirect("administrators:trainings")



# to be removed ------------------------

def temp_show_course(request, course_slug):
    """ Display course details """
    return render(request, 'administrators/courses/show_course.html', {
        'loggedin_user': userApi.loggedin_user(request.user),
        'course': adminApi.get_course_by_slug(course_slug)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def temp_show_session(request, session_slug):
    """ Display session details """

    if not userApi.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user):
        raise PermissionDenied

    session = adminApi.get_session_by_slug(session_slug)
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
            'loggedin_user': userApi.loggedin_user(request.user)
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
        'loggedin_user': userApi.loggedin_user(request.user),
        'course': course,
        'form': CourseForm(data=None, instance=course)
    })

"""


"""
@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def assign_ta_hours(request, session_slug, job_slug):
    if not userApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

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
    if not userApi.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = userApi.loggedin_user(request.user)
    if not userApi.is_admin(loggedin_user): raise PermissionDenied

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
