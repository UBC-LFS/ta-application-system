from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_control

from . import api
from users import api as usersApi
from .models import ApplicationStatus
from .forms import *
from datetime import datetime

from django.forms.models import model_to_dict


# Pages

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def index(request):
    """ Display a summary of all data including a dashboard """

    if not usersApi.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user):
        raise PermissionDenied

    return render(request, 'department/index.html', {
        'loggedin_user': loggedin_user,
        'courses': api.get_courses()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def basics(request):
    if not usersApi.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user):
        raise PermissionDenied

    return render(request, 'department/pages/basics.html', {
        'loggedin_user': loggedin_user
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def courses(request):
    if not usersApi.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user):
        raise PermissionDenied

    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            if course:
                messages.success(request, 'Success!')
                return redirect('department:courses')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'department/pages/courses.html', {
        'loggedin_user': loggedin_user,
        'courses': api.get_courses(),
        'form': CourseForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def sessions(request):
    """ Display all information of sessions and create a session """

    if not usersApi.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user):
        raise PermissionDenied

    if request.method == 'POST':
        request.session['session_form_data'] = request.POST
        return redirect('department:create_session_confirmation')

    return render(request, 'department/pages/sessions.html', {
        'loggedin_user': loggedin_user,
        'not_archived_sessions': api.get_not_archived_sessions(),
        'archived_sessions': api.get_archived_sessions(),
        'form': SessionForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def jobs(request):
    """ Display all jobs """

    if not usersApi.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user):
        raise PermissionDenied

    instructors = usersApi.get_instructors()
    print("instructors", instructors)

    return render(request, 'department/pages/jobs.html', {
        'loggedin_user': loggedin_user,
        'jobs': api.get_jobs(),
        'instructors': instructors
    })







# ------------- Sessions -------------




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
                    messages.success(request, 'Success!')
                    return redirect('department:sessions')
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

    return render(request, 'department/sessions/create_session_confirmation.html', {
        'loggedin_user': loggedin_user,
        'form': SessionConfirmationForm(data=data, initial={
            'term': term
        }),
        'courses': courses
    })



@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_session(request, session_slug):
    """ Edit a session """

    if not usersApi.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user):
        raise PermissionDenied

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
                    return HttpResponseRedirect( reverse('department:sessions') )
                else:
                    messages.error(request, 'Error!')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'department/sessions/edit_session.html', {
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

    return redirect('department:sessions')



# ------------- Jobs -------------

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def add_instructors(request, session_slug, job_slug):
    if not usersApi.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user):
        raise PermissionDenied

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
            print(form.errors.get_json_data())
            messages.error(request, 'Error! Form is invalid')
    return redirect('department:jobs')


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_job(request, session_slug, job_slug):
    """ Edit a job """

    if not usersApi.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user):
        raise PermissionDenied

    session = api.get_session_by_slug(session_slug)
    job = api.get_session_job_by_slug(session_slug, job_slug)
    job_instructors = job.instructors.all()

    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
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
                    return HttpResponseRedirect( reverse('department:show_job', args=[session_slug, job_slug]) )
                else:
                    messages.error(request, 'Error!')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'department/jobs/edit_job.html', {
        'loggedin_user': loggedin_user,
        'session': session,
        'job': job,
        'form': JobForm(data=None, instance=job, initial={
            'instructors': job_instructors
        })
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_job(request, session_slug, job_slug):
    """ Display job details """

    if not usersApi.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user):
        raise PermissionDenied

    return render(request, 'department/jobs/show_job.html', {
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

    return render(request, 'department/applications/applications.html', {
        'loggedin_user': loggedin_user,
        'applications': api.get_applications()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def selected_applications(request):
    if not usersApi.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user):
        raise PermissionDenied

    return render(request, 'department/applications/selected_applications.html', {
        'loggedin_user': loggedin_user,
        'selected_applications': api.get_selected_applications(),
        'status_form': ApplicationStatusForm(initial={
            'assigned': ApplicationStatus.OFFERED
        })
    })

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

    return render(request, 'department/applications/offered_applications.html', {
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
    return render(request, 'department/applications/accepted_applications.html', {
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

    return render(request, 'department/applications/declined_applications.html', {
        'loggedin_user': loggedin_user,
        'declined_applications': api.get_declined_applications()
    })


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

    return HttpResponseRedirect( reverse('department:applications', args=[session_slug, job_slug]) )

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_job_application(request, session_slug, job_slug):
    """ Edit classification and note """

    if not usersApi.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user):
        raise PermissionDenied

    if request.method == 'POST':
        application_id = request.POST.get('application')
        form = AdminApplicationForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            updated = api.update_application_classification_note(application_id, data)
            if updated:
                messages.success(request, 'Success!')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error!')

    return HttpResponseRedirect( reverse('department:show_job', args=[session_slug, job_slug]) )

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_application(request, app_slug):

    if not usersApi.is_valid_user(request.user):
        raise PermissionDenied

    loggedin_user = usersApi.loggedin_user(request.user)
    if not usersApi.is_admin(loggedin_user):
        raise PermissionDenied

    return render(request, 'department/applications/show_application.html', {
        'loggedin_user': usersApi.loggedin_user(request.user),
        'app': api.get_application_slug(app_slug)
    })










# Courses



#checked
def edit_course(request, course_slug):
    """ Edit a course """
    course = api.get_course_by_slug(course_slug)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            course = form.save()
            if course:
                messages.success(request, 'Success!')
                return HttpResponseRedirect( reverse('department:show_course', args=[course.slug]) )
            else:
                messages.error(request, 'Error!')

    return render(request, 'department/courses/edit_course.html', {
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

    return redirect("department:courses")


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
                return redirect('department:terms')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'department/terms/terms.html', {
        'loggedin_user': usersApi.loggedin_user(request.user),
        'terms': api.get_terms(),
        'form': TermForm()
    })

#checked
def show_term(request, code):
    """ Display term details """
    return render(request, 'department/terms/show_term.html', {
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
                return HttpResponseRedirect( reverse('department:show_course', args=[updated_term.slug]) )
            else:
                messages.error(request, 'Error!')

    return render(request, 'department/terms/edit_term.html', {
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

    return redirect("department:terms")


def course_codes(request):
    if request.method == 'POST':
        form = CourseCodeForm(request.POST)
        if form.is_valid():
            course_code = form.save()
            if course_code:
                messages.success(request, 'Success!')
                return redirect('department:course_codes')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'department/course_codes/course_codes.html', {
        'loggedin_user': usersApi.loggedin_user(request.user),
        'course_codes': api.get_course_codes(),
        'form': CourseCodeForm()
    })

def show_course_code(request, name):
    return render(request, 'department/course_codes/show_course_code.html', {
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
    return redirect('department:course_codes')


def delete_course_code(request):
    if request.method == 'POST':
        course_code_id = request.POST.get('course_code')
        deleted = api.delete_course_code(course_code_id)
        if deleted:
            messages.success(request, 'Success!')
        else:
            messages.error(request, 'Error!')
    return redirect('department:course_codes')

# Course Number

def course_numbers(request):
    if request.method == 'POST':
        form = CourseNumberForm(request.POST)
        if form.is_valid():
            course_number = form.save()
            if course_number:
                messages.success(request, 'Success!')
                return redirect('department:course_numbers')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'department/course_numbers/course_numbers.html', {
        'loggedin_user': usersApi.loggedin_user(request.user),
        'course_numbers': api.get_course_numbers(),
        'form': CourseNumberForm()
    })

def show_course_number(request, name):
    return render(request, 'department/course_numbers/show_course_number.html', {
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
    return redirect('department:course_numbers')


def delete_course_number(request):
    if request.method == 'POST':
        course_number_id = request.POST.get('course_number')
        deleted = api.delete_course_number(course_number_id)
        if deleted:
            messages.success(request, 'Success!')
        else:
            messages.error(request, 'Error!')
    return redirect('department:course_numbers')

# Course Section

def course_sections(request):
    if request.method == 'POST':
        form = CourseSectionForm(request.POST)
        if form.is_valid():
            course_section = form.save()
            if course_section:
                messages.success(request, 'Success!')
                return redirect('department:course_sections')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error! Form is invalid')

    return render(request, 'department/course_sections/course_sections.html', {
        'loggedin_user': usersApi.loggedin_user(request.user),
        'course_sections': api.get_course_sections(),
        'form': CourseSectionForm()
    })

def show_course_section(request, name):
    return render(request, 'department/course_sections/show_course_section.html', {
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
    return redirect('department:course_sections')

def delete_course_section(request):
    if request.method == 'POST':
        course_section_id = request.POST.get('course_section')
        deleted = api.delete_course_section(course_section_id)
        if deleted:
            messages.success(request, 'Success!')
        else:
            messages.error(request, 'Error!')
    return redirect('department:course_sections')




# to be removed

def temp_show_course(request, course_slug):
    """ Display course details """
    return render(request, 'department/courses/show_course.html', {
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
    return render(request, 'department/sessions/show_session.html', {
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
                return redirect('department:sessions')
            else:
                messages.error(request, 'Error!')
        else:
            messages.error(request, 'Error!')
        return render(request, 'department/sessions/create_session_confirmation.html', {
            'loggedin_user': usersApi.loggedin_user(request.user)
        })

    else:
        messages.error(request, 'Error! Form is invalid')

    return redirect('department:sessions')
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
                return HttpResponseRedirect( reverse('department:show_course', args=[updated_course.slug]) )
            else:
                messages.error(request, 'Error!')

    return render(request, 'department/edit_course.html', {
        'loggedin_user': usersApi.loggedin_user(request.user),
        'course': course,
        'form': CourseForm(data=None, instance=course)
    })

"""
