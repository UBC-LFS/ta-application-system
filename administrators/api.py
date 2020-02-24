import os
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.forms.models import model_to_dict
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.db import IntegrityError

from administrators.models import *
from users.models import *
from users import api as userApi

from datetime import datetime


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

    instructor.total_applicants = count
    return instructor


def update_job_instructors(job, old_instructors, new_instructors):
    ''' Update instructors in a job '''
    job.instructors.remove( *old_instructors )
    job.instructors.add( *list(new_instructors) )
    return True if job else None

def update_job_accumulated_ta_hours(session_slug, job_slug, ta_hours):
    ''' Update ta hours in a job '''
    job = get_job_by_session_slug_job_slug(session_slug, job_slug)

    new_hours = job.accumulated_ta_hours + ta_hours
    job.accumulated_ta_hours = new_hours
    job.updated_at = datetime.now()

    saved = job.save(update_fields=['accumulated_ta_hours', 'updated_at'])
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
            cancelled = app.applicationstatus_set.filter(assigned=ApplicationStatus.CANCELLED)
            if app.is_terminated == False or cancelled.exists() == False:
                if accepted.exists():
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
        if path == 'offered':
            offered = app.applicationstatus_set.filter(assigned=ApplicationStatus.OFFERED)
            if offered.exists(): app.offered = offered.last()
        elif path == 'declined':
            declined = app.applicationstatus_set.filter(assigned=ApplicationStatus.DECLINED)
            if declined.exists(): app.declined = declined.last()
        elif path == 'terminated':
            accepted = app.applicationstatus_set.filter(assigned=ApplicationStatus.ACCEPTED)
            if accepted.exists(): app.accepted = accepted.last()

    return apps

def update_application_classification_note(app_id, data):
    ''' Update classification and note in an application '''
    classification = data.get('classification')
    note = data.get('note')

    app = get_application(app_id)
    app.classification = classification
    app.note = note
    app.save(update_fields=['classification', 'note'])
    return app


def get_accepted_status(app):
    ''' Get an accepted status of an application'''
    return app.applicationstatus_set.filter(assigned=ApplicationStatus.ACCEPTED).last()

def update_application_instructor_preference(app_id, instructor_preference):
    ''' Update an instructor preference in an application '''
    app = get_object_or_404(Application, id=app_id)
    app.instructor_preference = instructor_preference
    app.updated_at = datetime.now()
    app.save(update_fields=['instructor_preference', 'updated_at'])
    return app

def get_terminated_applications():
    ''' Update an application for the termination of an application '''
    return Application.objects.filter(is_terminated=True)


# end applications


# admin documents

def get_admin_docs(app_id):
    ''' Get am admin docs '''
    admin_docs = AdminDocuments.objects.filter(application_id=app_id)
    if admin_docs.exists():
        return admin_docs.first()
    return None


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


# utils

def is_valid_float(num):
    try:
        n = float(num)
        return True
    except ValueError:
        return False
