import os
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.forms.models import model_to_dict
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.db import IntegrityError
from django.core.exceptions import PermissionDenied
from django.urls import resolve
from urllib.parse import urlparse

from administrators.models import *
from administrators.forms import AdminDocumentsForm
from users.models import *
from users import api as userApi

from datetime import datetime, timedelta, date
import math
import csv

# Request parameter validation

def validate_parameters(request, params, option=None):
    ''' Validate request parameters '''
    for param in params:
        if option == 'POST':
            if request.POST.get(param) == None: raise Http404
        else:
            if request.GET.get(param) == None: raise Http404
    return True

def validate_url_page(request, path):
    ''' Validate a page name in url '''
    if request.GET.get('p') not in path:
        raise Http404

def validate_url_tab(request, path):
    ''' Validate a tab name in url '''
    if request.GET.get('t') not in path:
        raise Http404

def can_req_parameters_access(request, domain, params, option=None):
    ''' Check whether request parameters are valid or not '''

    SESSION_PATH = ['Current Sessions', 'Archived Sessions']
    JOB_PATH = ['Prepare Jobs', 'Jobs in Progress', 'Jobs by Instructor', 'Jobs by Student',
                'Jobs']
    APP_PATH = ['Dashboard', 'All Applications', 'Selected Applications',
                'Offered Applications', 'Accepted Applications',
                'Declined Applications', 'Terminated Applications',
                'Email History']
    USER_PATH = ['All Users', 'Jobs by Instructor', 'Jobs by Student', 'Applications'] + APP_PATH
    STUDENT_PATH = ['Home', 'Edit Profile','Confidential Information']

    # True if parameters are in the params list
    if validate_parameters(request, params, option):
        next = None
        res = None
        if option == 'POST':
            next = urlparse(request.POST.get('next'))
            res = resolve(next.path)
            if 'session_slug' in res.kwargs.keys() and len(res.kwargs['session_slug']) > 0:
                validate_next(request.POST.get('next'), ['session'])
                if 'job_slug' in res.kwargs.keys() and len(res.kwargs['job_slug']) > 0:
                    validate_next(request.POST.get('next'), ['session', 'job'])
        else:
            next = urlparse(request.GET.get('next'))
            res = resolve(next.path)

        if domain == 'session':
            validate_url_page(request, SESSION_PATH)

        elif domain == 'job':
            validate_url_page(request, JOB_PATH)

        elif domain == 'job-app':
            if 'jobs' in res.url_name:
                validate_url_page(request, JOB_PATH)
            elif 'applications' in res.url_name:
                validate_url_page(request, APP_PATH)

        elif domain == 'job-tab':
            validate_url_page(request, JOB_PATH)
            validate_url_tab(request, ['all', 'offered', 'accepted'])

        elif domain == 'app':
            validate_url_page(request, APP_PATH)

        elif domain == 'user':
            validate_url_page(request, USER_PATH)

        elif domain == 'user-tab':
            validate_url_page(request, USER_PATH)
            role = res.app_name
            tabs = []
            if role == 'administrators':
                tabs = ['basic', 'additional', 'confidential']
            elif role == 'instructors':
                tabs = ['basic', 'additional', 'resume']
                get_job_by_session_slug_job_slug(res.kwargs['session_slug'], res.kwargs['job_slug'])

            validate_url_tab(request, tabs)

        elif domain == 'student':
            validate_url_page(request, STUDENT_PATH)
            validate_url_tab(request, ['basic', 'additional', 'resume'])

        elif domain == 'student-job':
            validate_url_page(request, ['Home', 'History of Jobs'])

        elif domain == 'instructor-note':
            get_job_by_session_slug_job_slug(res.kwargs['session_slug'], res.kwargs['job_slug'])


def validate_next(next, list):
    ''' Validate next values'''
    parse = urlparse(next)
    res = resolve(parse.path)
    if 'session' in list:
        get_session(res.kwargs['session_slug'], 'slug')
        if 'job' in list:
            get_job_by_session_slug_job_slug(res.kwargs['session_slug'], res.kwargs['job_slug'])

def build_url(path, next_path, page, tab):
    return "{0}?next={1}&p={2}&t={3}".format(path, next_path, page, tab)


def build_new_next(request):
    full_path = request.get_full_path()
    next = urlparse(full_path)
    query = ''
    if len(next.query) > 0:
        for q in next.query.split('&'):
            arr = q.split('=')
            if len(arr[1]) > 0:
                if len(query) > 0:
                    query += '&'
                query += arr[0] + '=' + arr[1]

    new_next = next.path
    if len(query) > 0: new_next += '?' + query
    return new_next

def get_next(request):
    full_path = request.get_full_path()
    next = urlparse(full_path)
    return next.query.split('&p=')[0][5:]



# Courses

def get_courses():
    ''' Get all courses '''
    return Course.objects.all().order_by('id')

def get_course(data, option=None):
    ''' Get a course '''
    if option == 'slug': return get_object_or_404(Course, slug=data)
    return get_object_or_404(Course, id=data)


def get_courses_by_term(term_id):
    ''' Get courses by term '''
    try:
        return Course.objects.filter(term__id=term_id)
    except Course.DoesNotExist:
        return None

def delete_course(course_id):
    ''' Delete a course '''
    course = get_course(course_id)
    course.delete()
    return course if course else False


# Sessions

def get_sessions():
    ''' Get all sessions '''
    return Session.objects.all()

def get_session(data, by=None):
    ''' Get a session '''
    if by == 'slug':
        return get_object_or_404(Session, slug=data)
    return get_object_or_404(Session, id=data)

def available_session(session_slug):
    session = get_session(session_slug, 'slug')
    if session.is_visible == False or session.is_archived == True:
        raise PermissionDenied

def get_sessions_by_year(year):
    """ Get sessions by year """
    return Session.objects.filter(year=year)

def session_exists(session_id):
    """ Check a session exists """
    if Session.objects.filter(id=session_id).exists():
        return True
    return False

def delete_session(session_id):
    ''' Delete a session '''
    session = get_session(session_id)
    session.delete()
    return session

def update_session_jobs(session, courses):
    ''' Update courses/jobs in a session '''

    new_course_ids = [ course.id for course in courses ]
    jobs = Job.objects.filter(session_id=session.id)
    old_course_ids = [ job.course_id for job in jobs ]

    intersection = list( set(old_course_ids) & set(new_course_ids) )

    # if no intersection, then remove all existing courses
    if len(intersection) == 0:
        result = Job.objects.filter(session_id=session.id).delete()
        return create_jobs(session, courses) if result else None
    else:
        diff = list( set(old_course_ids) - set(new_course_ids) )

        # if no difference, new courses updateed
        if len(diff) == 0:
            new = list( set(new_course_ids) - set(intersection) )
            if len(new) > 0:
                courses = [ get_course(id) for id in new ]
                return create_jobs(session, courses)
            return True

        deleted = delete_job_by_course_ids(session, diff)
        if deleted:
            new = list( set(new_course_ids) - set(intersection) )
            if len(new) > 0:
                courses = [ get_course(id) for id in new ]
                return create_jobs(session, courses)
            return True
        else:
            return None

def add_num_instructors(sessions):
    for session in sessions:
        count = 0
        for job in session.job_set.all():
            if job.instructors.count() > 0: count += 1
        session.num_instructors = count
    return sessions


# end sessions

# Jobs

def get_jobs():
    ''' Get all jobs '''
    return Job.objects.all()

def get_job_by_session_slug_job_slug(session_slug, job_slug):
    ''' Get a job by session_slug and job_slug '''
    return get_object_or_404(Job, Q(session__slug=session_slug) & Q(course__slug=job_slug) )

def create_jobs(session, courses):
    ''' Create jobs in a session '''
    objs = [ Job(session=session, course=course, course_overview=course.overview, description=course.job_description, note=course.job_note) for course in courses ]
    jobs = Job.objects.bulk_create(objs)
    return True if jobs else False

def get_favourites(user):
    ''' Get user's favourite jobs '''
    #return Favourite.objects.filter( Q(applicant_id=user.id) & Q(job__is_active=True) )
    return Favourite.objects.filter(applicant_id=user.id).order_by('created_at')

def add_applied_jobs_to_favourites(user, favourites):
    ''' Add applied information into favourites '''
    for fav in favourites:
        fav.my_app = None
        my_app = fav.job.application_set.filter(applicant__id=user.id)
        if my_app.exists(): fav.my_app = my_app.first()
    return favourites

def add_applied_favourite_jobs(user, jobs):
    ''' Add applied and favourite infomation into jobs'''
    for job in jobs:
        job.my_app = None
        job.my_fav = None

        my_app = job.application_set.filter(applicant__id=user.id)
        if my_app.exists(): job.my_app = my_app.first()

        my_fav = job.favourite_set.filter(applicant__id=user.id)
        if my_fav.exists(): job.my_fav = my_fav.first()

    return jobs

def add_favourite_job(user, job):
    ''' Add user's favourite job '''
    job.my_fav = None
    my_fav = job.favourite_set.filter(applicant__id=user.id)
    if my_fav.exists(): job.my_fav = my_fav.first()

    return job

def delete_favourite_job(user, job):
    ''' Delete user's favourite job '''
    my_fav = job.favourite_set.filter(applicant__id=user.id)
    if my_fav.exists():
        my_fav.delete()
        return True
    return False

def add_job_with_applications_statistics(job):
    ''' Add a job with statistics of applications '''
    selected_app = 0
    offered_app = 0
    accepted_app = 0
    declined_app = 0
    for app in job.application_set.all():
        if get_selected(app): selected_app += 1
        if get_offered(app): offered_app += 1
        if get_accepted(app): accepted_app += 1
        if get_declined(app): declined_app += 1

    job.num_selected_apps = selected_app
    job.num_offered_apps = offered_app
    job.num_accepted_apps = accepted_app
    job.num_declined_apps = declined_app

    return job

def add_total_applicants(instructor):
    ''' Add total applicants in an instructor '''
    count = 0
    for job in instructor.job_set.all():
        count += job.application_set.count()

    return count

def remove_job_instructors(job, instructors):
    ''' Remove job instructors'''
    job.instructors.remove( *instructors )
    return True if job else None

def add_job_instructors(job, new_instructors):
    ''' Add instructors into a job '''
    job.instructors.add( *list(new_instructors) )
    return True if job else None

def update_job_instructors(job, old_instructors, new_instructors):
    ''' Update instructors into a job '''
    job.instructors.remove( *old_instructors )
    job.instructors.add( *list(new_instructors) )
    return True if job else None

def update_job_accumulated_ta_hours(session_slug, job_slug, ta_hours):
    ''' Update ta hours in a job '''
    job = get_job_by_session_slug_job_slug(session_slug, job_slug)

    new_hours = job.accumulated_ta_hours + ta_hours
    job.accumulated_ta_hours = new_hours
    job.updated_at = datetime.now()
    job.save(update_fields=['accumulated_ta_hours', 'updated_at'])

    return True if job else False

def get_recent_ten_job_details(course, year):
    ''' Get recent ten job '''
    return Job.objects.filter( Q(session__year__lt=year) & Q(course__code=course.code) & Q(course__number=course.number) ).order_by('-created_at')[:10]

def delete_job_by_course_ids(session, course_ids):
    ''' Delete a job by course id '''
    result = Job.objects.filter(session_id=session.id, course_id__in=course_ids).delete()
    return True if result else None


# end jobs


# Applications

def get_application(data, option=None):
    ''' Get an application '''
    if option == 'slug': return get_object_or_404(Application, slug=data)
    return get_object_or_404(Application, id=data)

def get_applications_user(user):
    ''' Get an user's applications '''
    return Application.objects.filter(applicant__id=user.id)

def create_application_status(app):
    ''' Create a status of an application '''
    app_status = ApplicationStatus.objects.create(application=app, assigned=ApplicationStatus.NONE, assigned_hours=0.0)
    return app_status if app_status else None

def add_app_info_into_application(app, list):
    ''' Add some information into an application given by list '''
    if 'resume' in list:
        app.resume_filename = None
        if userApi.has_user_resume_created(app.applicant) and bool(app.applicant.resume.uploaded):
            app.resume_filename = os.path.basename(app.applicant.resume.uploaded.name)

    if 'applied' in list:
        app.applied = None
        applied = app.applicationstatus_set.filter(assigned=ApplicationStatus.NONE)
        if applied.exists(): app.applied = applied.first()

    if 'selected' in list:
        app.selected = None
        selected = app.applicationstatus_set.filter(assigned=ApplicationStatus.SELECTED)
        if selected.exists(): app.selected = selected.first()

    if 'offered' in list:
        app.offered = None
        offered = app.applicationstatus_set.filter(assigned=ApplicationStatus.OFFERED)
        if offered.exists(): app.offered = offered.last()

    if 'accepted' in list:
        app.accepted = None
        accepted = app.applicationstatus_set.filter(assigned=ApplicationStatus.ACCEPTED)
        if accepted.exists(): app.accepted = accepted.last()

    if 'declined' in list:
        app.declined = None
        declined = app.applicationstatus_set.filter(assigned=ApplicationStatus.DECLINED)
        if declined.exists(): app.declined = declined.last()

    if 'cancelled' in list:
        app.cancelled = None
        cancelled = app.applicationstatus_set.filter(assigned=ApplicationStatus.CANCELLED)
        if cancelled.exists(): app.cancelled = cancelled.last()

    return app

def add_app_info_into_applications(apps, list):
    ''' Add some information into applications given by list '''
    for app in apps:
        if 'resume' in list:
            app.resume_filename = None
            if userApi.has_user_resume_created(app.applicant) and bool(app.applicant.resume.uploaded):
                app.resume_filename = os.path.basename(app.applicant.resume.uploaded.name)

        if 'applied' in list:
            app.applied = None
            applied = app.applicationstatus_set.filter(assigned=ApplicationStatus.NONE)
            if applied.exists(): app.applied = applied.first()

        if 'selected' in list:
            app.selected = None
            selected = app.applicationstatus_set.filter(assigned=ApplicationStatus.SELECTED)
            if selected.exists(): app.selected = selected.first()

        if 'offered' in list:
            app.offered = None
            offered = app.applicationstatus_set.filter(assigned=ApplicationStatus.OFFERED)
            if offered.exists(): app.offered = offered.last()

        if 'accepted' in list:
            app.accepted = None
            accepted = app.applicationstatus_set.filter(assigned=ApplicationStatus.ACCEPTED)
            if accepted.exists(): app.accepted = accepted.last()

        if 'declined' in list:
            app.declined = None
            declined = app.applicationstatus_set.filter(assigned=ApplicationStatus.DECLINED)
            if declined.exists(): app.declined = declined.last()

        if 'cancelled' in list:
            app.cancelled = None
            cancelled = app.applicationstatus_set.filter(assigned=ApplicationStatus.CANCELLED)
            if cancelled.exists(): app.cancelled = cancelled.last()

    return apps

def get_total_assigned_hours(apps, list):
    ''' Get total assigend hours in list '''
    total_hours = {}
    for name in list:
        total_hours[name] = {}

    for app in apps:
        if 'offered' in list:
            offered = app.applicationstatus_set.filter(assigned=ApplicationStatus.OFFERED)
            if offered.exists():
                year_term = '{0}-{1}'.format(app.job.session.year, app.job.session.term.code)
                if year_term in total_hours['offered'].keys():
                    total_hours['offered'][year_term] += offered.last().assigned_hours
                else:
                    total_hours['offered'][year_term] = offered.last().assigned_hours

        if 'accepted' in list:
            accepted = app.applicationstatus_set.filter(assigned=ApplicationStatus.ACCEPTED)
            if accepted.exists():
                can_add = True

                cancelled = app.applicationstatus_set.filter(assigned=ApplicationStatus.CANCELLED)
                if app.is_terminated == True and cancelled.exists() == True:
                    can_add = False

                declined = app.applicationstatus_set.filter(assigned=ApplicationStatus.DECLINED)
                if declined.exists() and declined.last().parent_id == None:
                    can_add = False

                if can_add == True:
                    year_term = '{0}-{1}'.format(app.job.session.year, app.job.session.term.code)
                    if year_term in total_hours['accepted'].keys():
                        total_hours['accepted'][year_term] += accepted.last().assigned_hours
                    else:
                        total_hours['accepted'][year_term] = accepted.last().assigned_hours

    return total_hours


def add_applications_with_latest_status(apps):
    ''' Add applications with latest status '''
    for app in apps:
        app.applied = None
        applied = app.applicationstatus_set.filter(assigned=ApplicationStatus.NONE)
        if applied.exists(): app.applied = applied.first()

        status = app.applicationstatus_set.all().last()
        if status.assigned == ApplicationStatus.OFFERED:
            app.offered = None
            offered = app.applicationstatus_set.filter(assigned=ApplicationStatus.OFFERED)
            if offered.exists(): app.offered = offered.last()

        elif status.assigned == ApplicationStatus.ACCEPTED:
            app.accepted = None
            accepted = app.applicationstatus_set.filter(assigned=ApplicationStatus.ACCEPTED)
            if accepted.exists(): app.accepted = accepted.last()

        elif status.assigned == ApplicationStatus.DECLINED:
            app.declined = None
            declined = app.applicationstatus_set.filter(assigned=ApplicationStatus.DECLINED)
            if declined.exists():
                app.declined = declined.last()

        elif status.assigned == ApplicationStatus.CANCELLED:
            app.cancelled = None
            cancelled = app.applicationstatus_set.filter(assigned=ApplicationStatus.CANCELLED)
            if cancelled.exists(): app.cancelled = cancelled.last()

        else:
            app.applied = None
            applied = app.applicationstatus_set.filter(assigned=ApplicationStatus.NONE)
            if applied.exists(): app.applied = applied.first()

    return apps


def add_salary(apps):
    ''' Add a salary in applications '''
    for app in apps:
        app.salary = round(app.accepted.assigned_hours * app.classification.wage / app.job.session.term.by_month, 2)
        app.pt_percentage = round(app.accepted.assigned_hours / app.job.session.term.max_hours * 100, 2)
    return apps

def get_offered_apps_no_response(apps):
    ''' Get offered apps with no response '''
    return apps.filter(applicationstatus__assigned=ApplicationStatus.OFFERED).filter( ~Q(applicationstatus__assigned=ApplicationStatus.ACCEPTED) & ~Q(applicationstatus__assigned=ApplicationStatus.DECLINED) ).order_by('-id').distinct()

def get_accepted_apps_by_day(apps, when):
    ''' Get accepted apps by day '''

    day = date.today()
    query = Q(applicationstatus__created_at=day)
    if when == 'yesterday':
        day = date.today() - timedelta(days=1)
        query = Q(applicationstatus__created_at=day)
    elif when == 'week_ago':
        day = date.today() - timedelta(days=7)
        query = Q(applicationstatus__created_at__gte=day)

    apps = apps.filter( Q(applicationstatus__assigned=ApplicationStatus.ACCEPTED) & Q(is_terminated=False) & query ).order_by('-id').distinct()

    return add_app_info_into_applications(apps, ['accepted']), day


def get_eform_stats(apps):
    ''' Get the staticstics of eForm '''
    processed = 0
    not_processed = 0
    for app in apps:
        if hasattr(app, 'admindocuments') and app.admindocuments.eform:
            processed += 1
        else:
            not_processed += 1
    return { 'processed': processed, 'not_processed': not_processed }

def get_applications_with_multiple_ids(ids):
    ''' Get applications with multiple ids '''
    return Application.objects.filter(id__in=ids)

def get_applications(option=None):
    ''' Get all applications '''
    if option: return Application.objects.all().order_by(option)
    return Application.objects.all().order_by('-id')


def get_application_statuses():
    ''' Get all statuses of an application '''
    return ApplicationStatus.objects.all().order_by('-id')


def get_selected(app):
    ''' Get an application selected '''
    selected_app = app.applicationstatus_set.filter(assigned=ApplicationStatus.SELECTED)
    if selected_app.exists(): return selected_app
    return False

def get_offered(app):
    ''' Get an application offered '''
    offered_app = app.applicationstatus_set.filter(assigned=ApplicationStatus.OFFERED)
    if offered_app.exists(): return offered_app
    return False

def get_accepted(app):
    ''' Get an application accepted '''
    accepted_app = app.applicationstatus_set.filter(assigned=ApplicationStatus.ACCEPTED)
    if accepted_app.exists(): return accepted_app
    return False

def get_declined(app):
    ''' Get an application declined '''
    declined_app = app.applicationstatus_set.filter(assigned=ApplicationStatus.DECLINED)
    if declined_app.exists(): return declined_app
    return False


def get_applications_with_status_by_session_slug_job_slug(session_slug, job_slug):
    ''' Get selected applications by session_slug and job_slug '''
    apps = Application.objects.filter( Q(job__session__slug=session_slug) & Q(job__course__slug=job_slug) )
    for app in apps:
        app.selected = None
        selected = app.applicationstatus_set.filter(assigned=ApplicationStatus.SELECTED)
        if selected.exists(): app.selected = selected.first()

    return apps


def get_applications_with_multiple_ids_by_path(ids, path):
    ''' Get offered applications with multiple ids'''
    apps = get_applications_with_multiple_ids(ids)
    for app in apps:
        if path == 'Offered Applications':
            offered = app.applicationstatus_set.filter(assigned=ApplicationStatus.OFFERED)
            if offered.exists(): app.offered = offered.last()
        elif path == 'Declined Applications':
            declined = app.applicationstatus_set.filter(assigned=ApplicationStatus.DECLINED)
            if declined.exists(): app.declined = declined.last()
        elif path == 'Terminated Applications':
            accepted = app.applicationstatus_set.filter(assigned=ApplicationStatus.ACCEPTED)
            if accepted.exists(): app.accepted = accepted.last()

    return apps

def update_application_classification_note(app_id, data):
    ''' Update classification and note in an application '''
    app = Application.objects.filter(id=app_id).update(
        classification = data.get('classification'),
        note = data.get('note'),
        updated_at = datetime.now()
    )
    return True if app else False


def get_accepted_status(app):
    ''' Get an accepted status of an application'''
    return app.applicationstatus_set.filter(assigned=ApplicationStatus.ACCEPTED).last()

def update_application_instructor_preference(app_id, instructor_preference):
    ''' Update an instructor preference in an application '''
    app = Application.objects.filter(id=app_id).update(
        instructor_preference = instructor_preference,
        updated_at = datetime.now()
    )
    return get_object_or_404(Application, id=app_id) if app else False

def get_terminated_applications():
    ''' Update an application for the termination of an application '''
    return Application.objects.filter(is_terminated=True).order_by('-id')

def update_job_offer(post):
    ''' Update a classification and assigned hours in Selected Apps '''
    cls = get_classification( post.get('classification') )
    app = Application.objects.filter(id=post.get('application')).update(
        classification = cls,
        note = post.get('note'),
        updated_at = datetime.now()
    )
    status = ApplicationStatus.objects.filter(id=post.get('applicationstatus')).update(
        assigned_hours = post.get('assigned_hours')
    )
    return True if app and status else False


def bulk_update_admin_docs(data, user):
    ''' bulk update admin docs '''
    csv_reader = csv.reader(data, quotechar='"', delimiter=',')

    apps = get_applications()
    apps = apps.filter( Q(applicationstatus__assigned=ApplicationStatus.ACCEPTED) & Q(is_terminated=False) ).order_by('-id').distinct()
    accepted_ids = [ app.id for app in apps ]

    rows = []
    c = 0
    for row in csv_reader:
        # Check a number of rows
        if len(row) != 16:
            return False, 'An error occurred while reading table rows. Some columns are missing.'

        # header
        if c == 0:
            rows.append(row)
        else:
            if len(row[0]) == 0:
                for col in row:
                    if len(col) > 0:
                        msg = str(c) + 'th'
                        if c == 1: msg = '1st'
                        elif c == 2: msg = '2nd'
                        elif c == 3: msg = '3rd'
                        return False, 'An error occurred while reading table rows. Something went wrong in the {0} row. (e.g., ID is empty)'.format(msg)
            else:
                # check id if it's not in accepted apps
                id = int(row[0])
                if id not in accepted_ids:
                    return False, 'An error occurred while reading table rows. No application ID: {0} found in Accepted Applications.'.format(id)

                # check if it has an application
                try:
                    Application.objects.get(id=id)
                except Application.DoesNotExist:
                    return False, 'An error occurred while reading table rows. No application ID: {0} found.'.format(id)

                rows.append(row)
        c += 1

    if len(rows) == 0:
        return False, 'An error occurred while iterating table rows. Please check your data. Note that 1st row is a header.'
    elif len(rows) == 1:
        return False, 'An error occurred while iterating table rows. Please check your header or data fields. Note that 1st row is a header.'

    docs = []
    updates = set()
    for i in range(1, len(rows)):
        row = rows[i]
        id = trim(row[0])
        pin = trim(row[10])
        tasm = True if trim(row[11].lower()) == 'yes' else False
        eform = trim(row[12])
        speed_chart = trim(row[13])
        processing_note = trim(row[14])

        admin_docs = get_admin_docs(id)
        form = AdminDocumentsForm({ 'application': id, 'pin': pin, 'tasm': tasm, 'eform': eform, 'speed_chart': speed_chart, 'processing_note': processing_note }, instance=admin_docs)
        if form.is_valid() == False:
            errors = form.errors.get_json_data()
            return False, 'ID: ' + id + ' - ' + userApi.get_error_messages(errors)

        can_save = False
        obj = AdminDocuments.objects.filter(application_id=id)

        if obj.exists():
            admin_docs = obj.first()
            fields = []
            if trim(admin_docs.pin) != pin:
                admin_docs.pin = pin
                updates.add('pin')
                fields.append('PIN')

            if admin_docs.tasm != tasm:
                admin_docs.tasm = tasm
                updates.add('tasm')
                fields.append('TASM')

            if trim(admin_docs.eform) != eform:
                admin_docs.eform = eform
                updates.add('eform')
                fields.append('eForm')

            if trim(admin_docs.speed_chart) != speed_chart:
                admin_docs.speed_chart = speed_chart
                updates.add('speed_chart')
                fields.append('Speed Chart')

            if trim(admin_docs.processing_note) != processing_note:
                admin_docs.processing_note = processing_note
                updates.add('processing_note')
                fields.append('Processing Note')

            if len(fields) > 0:
                docs.append({ 'id': id, 'fields': fields, 'username': admin_docs.application.applicant.username })
                can_save = True

        else:
            fields = []
            if bool(pin):
                updates.add('pin')
                fields.append('PIN')
            if tasm == True:
                updates.add('tasm')
                fields.append('TASM')
            if bool(eform):
                updates.add('eform')
                fields.append('eForm')
            if bool(speed_chart):
                updates.add('speed_chart')
                fields.append('Speed Chart')
            if bool(processing_note):
                updates.add('processing_note')
                fields.append('Processing Note')

            app = get_application(id)
            if len(fields) > 0:
                docs.append({ 'id': id, 'fields': fields, 'username': app.applicant.username })
                can_save = True

        # Update
        if can_save:
            saved_admin_docs = form.save()
            if saved_admin_docs:
                saved_admin_docs_user = add_admin_docs_user(saved_admin_docs, user)
                if saved_admin_docs_user == False:
                    return False, 'An error occurred while saving admin docs user.'
            else:
                return False, 'An error occurred while saving admin docs.'

    if len(docs) > 0:
        msg = '<ul>'
        for doc in docs:
            msg += '<li><strong>ID: ' + doc['id'] + ' (CWL: ' + doc['username'] + ')</strong> - ' + ','.join(doc['fields']) + '</li>'
        msg += '</ul>'
        return True, msg

    return True, ''


def get_today_accepted_apps():
    ''' Get accepted application in today '''

    apps = ApplicationStatus.objects.filter( Q(assigned=ApplicationStatus.ACCEPTED) & Q(created_at=date.today()) )
    return apps if apps.exists() else None

# end applications


# admin documents

def get_admin_docs(app_id):
    ''' Get an admin docs '''
    admin_docs = AdminDocuments.objects.filter(application_id=app_id)
    if admin_docs.exists():
        return admin_docs.first()
    return None

def add_admin_docs_user(admin_docs, user):
    ''' Insert an user into admin docs '''
    admin_docs_user = AdminDocumentsUser.objects.create(document=admin_docs, user=user.get_full_name())
    return admin_docs_user if admin_docs_user else False


# end admin documents


# emails

def get_email(email_id):
    ''' Get an email '''
    return get_object_or_404(Email, id=email_id)

def get_emails():
    ''' Get emails '''
    return Email.objects.all()

def send_and_create_email(app, sender, receiver, title, message, type):
    ''' Send and create an email '''
    # Reference: https://docs.djangoproject.com/en/2.2/topics/email/
    #sent = send_mail(title, message, sender, [receiver], fail_silently=False)
    msg = EmailMultiAlternatives(title, message, sender, [receiver])
    msg.attach_alternative(message, "text/html")
    msg.send()

    created_email = Email.objects.create(
        application = app,
        sender = sender,
        receiver = receiver,
        title = title,
        message = message,
        type = type
    )
    return True if msg and created_email else False


# end emails




# ----- Terms -----

def get_terms():
    ''' Get all terms '''
    return Term.objects.all()

def get_term(term_id):
    ''' Get a term by id '''
    return get_object_or_404(Term, id=term_id)

def get_term_by_code(code):
    ''' Get a term by code '''
    return get_object_or_404(Term, code=code)

def delete_term(term_id):
    ''' Delete a term '''
    term = get_term(term_id)
    try:
        term.delete()
        return { 'status': True, 'term': term }
    except IntegrityError as e:
        return { 'status': False, 'error': e}


# Course Codes


def get_course_codes():
    ''' '''
    return CourseCode.objects.all()

def get_course_code(course_code_id):
    ''' '''
    return get_object_or_404(CourseCode, id=course_code_id)

def get_course_code_by_name(name):
    ''' '''
    return get_object_or_404(CourseCode, name=name)

def delete_course_code(course_code_id):
    ''' '''
    course_code = get_course_code(course_code_id)
    try:
        course_code.delete()
        return { 'status': True, 'course_code': course_code }
    except IntegrityError as e:
        return { 'status': False, 'error': e}



# Course numbers
def get_course_numbers():
    ''' '''
    return CourseNumber.objects.all()

def get_course_number(course_number_id):
    ''' '''
    return get_object_or_404(CourseNumber, id=course_number_id)

def get_course_number_by_name(name):
    ''' '''
    return get_object_or_404(CourseNumber, name=name)

def delete_course_number(course_number_id):
    ''' '''
    course_number = get_course_number(course_number_id)
    try:
        course_number.delete()
        return { 'status': True, 'course_number': course_number }
    except IntegrityError as e:
        return { 'status': False, 'error': e}


# Course codes
def get_course_sections():
    ''' '''
    return CourseSection.objects.all()

def get_course_section(course_section_id):
    ''' '''
    return get_object_or_404(CourseSection, id=course_section_id)

def get_course_section_by_name(name):
    ''' '''
    return get_object_or_404(CourseSection, name=name)

def delete_course_section(course_section_id):
    ''' '''
    course_section =get_course_section(course_section_id)
    try:
        course_section.delete()
        return { 'status': True, 'course_section': course_section }
    except IntegrityError as e:
        return { 'status': False, 'error': e}


# classifications

def get_classifications(option=None):
    ''' Get classifications '''
    if option == 'all':
        return Classification.objects.all()
    return Classification.objects.filter(is_active=True)

def get_classification(classification_id):
    ''' Get a classification by id '''
    return get_object_or_404(Classification, id=classification_id)

def get_classification_by_slug(slug):
    ''' Get a classification by slug '''
    return get_object_or_404(Classification, slug=slug)

def delete_classification(classification_id):
    ''' Delete a classification '''
    classification = get_classification(classification_id)
    classification.delete()
    return classification if classification else False

# Admin Emails


def get_admin_emails():
    ''' Get admin emails '''
    return AdminEmail.objects.all()

def get_admin_email(admin_email_id):
    ''' Get a admin email by id '''
    return get_object_or_404(AdminEmail, id=admin_email_id)

def get_admin_email_by_slug(slug):
    ''' Get a admin_email by slug '''
    return get_object_or_404(AdminEmail, slug=slug)

def delete_admin_email(admin_email_id):
    ''' Delete a admin_email '''
    admin_email = get_admin_email(admin_email_id)
    admin_email.delete()
    return admin_email if admin_email else False


# Landing Page
def get_landing_pages():
    ''' get landing page contents '''
    return LandingPage.objects.all()


def get_landing_page(landing_page_id):
    ''' Get a landing page by id '''
    return get_object_or_404(LandingPage, id=landing_page_id)


def delete_landing_page(landing_page_id):
    ''' Delete a landing page '''
    landing_page = get_landing_page(landing_page_id)
    landing_page.delete()
    return landing_page if landing_page else False

def get_visible_landing_page():
    return LandingPage.objects.filter(is_visible=True).order_by('created_at', 'updated_at').last()


# utils

def is_valid_float(num):
    try:
        n = float(num)
        return True
    except ValueError:
        return False

def is_valid_integer(num):
    n = float(num)
    return int(n) == math.ceil(n)

def trim(str):
    ''' Remove whitespaces '''
    return str.strip() if str != None and len(str) > 0 else ''
