import os
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.forms.models import model_to_dict
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives

from administrators.models import *
from users.models import *
from users import api as userApi

from datetime import datetime



def valid_path(path):
    valid_list = ['administrators', 'human_resources', 'instructors', 'students', 'users']
    path_list = path.split('/')
    if path_list[1] in valid_list:
        return path_list[1]
    raise Http404

# Courses

def get_courses():
    ''' Get all courses '''
    return Course.objects.all()

def get_course(course_id):
    ''' Get a course '''
    return get_object_or_404(Course, id=course_id)

def get_course_by_slug(course_slug):
    ''' Get a course by slug '''
    return get_object_or_404(Course, slug=course_slug)

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


def get_session(session_id):
    ''' Get a session '''
    return get_object_or_404(Session, id=session_id)

def delete_session(session_id):
    ''' Delete a session '''
    session = get_session(session_id)
    session.delete()
    return session

def get_current_sessions():
    ''' Get current sessions '''
    sessions = []
    for session in Session.objects.all():
        if not session.is_archived:
            count = 0
            for job in session.job_set.all():
                if job.instructors.count() > 0:
                    count += 1
            session.num_instructors = count
            sessions.append(session)
    return sessions

def get_archived_sessions():
    ''' Get archived sessions '''
    sessions = []
    for session in Session.objects.all():
        if session.is_archived:
            count = 0
            for job in session.job_set.all():
                if job.instructors.count() > 0:
                    count += 1
            session.num_instructors = count
            sessions.append(session)
    return sessions

def get_session_by_slug(session_slug):
    ''' Get a session by slug '''
    return get_object_or_404(Session, slug=session_slug)

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

def get_visible_current_sessions():
    ''' Get visible current sessions with active jobs '''
    sessions = Session.objects.filter( Q(is_visible=True) & Q(is_archived=False) )

    for session in sessions:
        jobs = session.job_set.filter(is_active=True)
        if jobs.exists(): session.active_jobs = jobs

    return sessions

    """
    sessions = []
    for session in Session.objects.all():
        if session.is_visible and not session.is_archived:
            count = 0
            for job in session.job_set.all():
                if job.instructors.count() > 0:
                    count += 1
            session.num_instructors = count
            sessions.append(session)
    return sessions"""





def get_sessions():
    """ Get all sessions """
    return Session.objects.all()

def session_exists(session_id):
    """ Check a session exists """
    if Session.objects.filter(id=session_id).exists():
        return True
    return False

def get_sessions_by_year(year):
    """ Get sessions by year """
    return Session.objects.filter(year=year)

def get_not_visible_active_sessions():
    return Session.objects.filter(is_visible=False, is_archived=False)




# Jobs

def get_jobs():
    ''' Get all jobs '''
    return Job.objects.all()

def create_jobs(session, courses):
    ''' Create jobs in a session '''
    objs = [ Job(session=session, course=course) for course in courses ]
    jobs = Job.objects.bulk_create(objs)
    return True if jobs else None

def get_job_by_session_slug_job_slug(session_slug, job_slug):
    ''' Get a job by session_slug and job_slug '''
    return get_object_or_404(Job, Q(session__slug=session_slug) & Q(course__slug=job_slug) )

def get_jobs_with_applications_statistics():
    ''' get jobs with statistics of applications '''
    jobs = []
    for job in Job.objects.all():
        offered_app = 0
        accepted_app = 0
        declined_app = 0
        for app in job.application_set.all():
            if get_offered(app): offered_app += 1
            if get_accepted(app): accepted_app += 1
            if get_declined(app): declined_app += 1

        job.offered_applications = offered_app
        job.accepted_applications = accepted_app
        job.declined_applications = declined_app
        jobs.append(job)

    return jobs

def get_job_with_applications_statistics(session_slug, job_slug):
    ''' get a job with statistics of applications '''
    job = get_job_by_session_slug_job_slug(session_slug, job_slug)
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

def update_job_instructors(job, old_instructors, new_instructors):
    ''' Update instructors in a job '''
    job.instructors.remove( *old_instructors )
    job.instructors.add( *list(new_instructors) )
    return True if job else None

def get_available_jobs_to_apply(user, session_slug):
    ''' Get available jobs to apply '''
    jobs = Job.objects.filter( Q(session__slug=session_slug) & Q(is_active=True) )
    for job in jobs:
        job.app = None
        app = job.application_set.filter(applicant__id=user.id)
        if app.exists(): job.app = app.first()
    return jobs

def update_job_accumulated_ta_hours(session_slug, job_slug, ta_hours):
    ''' Update ta hours in a job '''
    job = get_job_by_session_slug_job_slug(session_slug, job_slug)
    new_hours = job.accumulated_ta_hours + float(ta_hours)
    job.accumulated_ta_hours = new_hours
    job.updated_at = datetime.now()
    saved = job.save(update_fields=['accumulated_ta_hours', 'updated_at'])
    return True if job else False

def get_recent_ten_job_details(course, year):
    ''' Get recent ten job '''
    return Job.objects.filter( Q(session__year__lte=year) & Q(course__code=course.code) & Q(course__number=course.number) ).order_by('-created_at')[:10]

def get_jobs_applied_by_student(user):
    ''' Get all jobs applied by a student '''
    return Job.objects.filter(application__applicant__id=user.id)


def get_jobs_applied_by_student1(user):
    ''' Get all jobs applied by a student '''
    jobs = []
    for job in get_jobs():
        if job.application_set.filter(applicant__id=user.id).exists():
            my_application = job.application_set.get(applicant__id=user.id)
            job.my_application = my_application
            jobs.append(job)
    return jobs

def create_application_status(app):
    ''' Create a status of an application '''
    app_status = ApplicationStatus.objects.create(application=app, assigned=ApplicationStatus.NONE, assigned_hours=0.0)
    return app_status if app_status else None


def has_applied_job(session_slug, job_slug, user):
    ''' Check if a user has applied for a job or not '''
    job = get_job_by_session_slug_job_slug(session_slug, job_slug)
    if job.application_set.filter(applicant__id=user.id).exists():
        return True
    return False

    """session = get_session_by_slug(session_slug)
    for job in session.job_set.all():
        if job.course.slug == job_slug:
            if job.application_set.filter(applicant__id=user.id).exists():
                return True
    return False"""


def delete_job_by_course_ids(session, course_ids):
    ''' Delete a job by course id '''
    result = Job.objects.filter(session_id=session.id, course_id__in=course_ids).delete()
    return True if result else None


# Applications

def get_application(app_id):
    ''' Get an application '''
    return get_object_or_404(Application, id=app_id)

def get_applications_with_multiple_ids(ids):
    ''' Get applications with multiple ids '''
    return Application.objects.filter(id__in=ids)


def get_application_by_slug(app_slug):
    ''' Get an application by slug '''
    return get_object_or_404(Application, slug=app_slug)

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


# important
def get_application_with_status_by_user(user, job, option):
    ''' Get an application with status '''
    filtered_app = Application.objects.filter( Q(applicant_id=user.id) & Q(job_id=job.id) )
    if filtered_app.exists():
        app = filtered_app.last()
        app.status = None
        status = app.applicationstatus_set.filter(assigned=option)
        if status.exists(): app.status = status.last()

        app.cancelled = None
        cancelled = app.applicationstatus_set.filter(assigned=ApplicationStatus.CANCELLED)
        if cancelled.exists(): app.cancelled = cancelled.last()

        return app
    '''if job.application_set.filter(applicant__id=user.id).exists():
        app = job.application_set.get(applicant__id=user.id)
        status = app.applicationstatus_set.filter(assigned=option).last()
        app.status = status

        app.cancelled = None
        cancelled = app.applicationstatus_set.filter(assigned=ApplicationStatus.CANCELLED)
        if cancelled.exists(): app.cancelled = cancelled.last()
        print(app.id)
        return app'''
    return None

# Very important
def get_applications_with_status(user):
    '''  Get applications with all statuses and total accepted assgiend hours '''
    total_accepted_assigned_hours = {}

    apps = Application.objects.filter(applicant_id=user.id).order_by('-created_at').distinct()
    for app in apps:
        status = app.applicationstatus_set.all().last()

        app.applied = None
        applied = app.applicationstatus_set.filter(assigned=ApplicationStatus.NONE)
        if applied.exists(): app.applied = applied.first()

        if status.assigned == ApplicationStatus.OFFERED:
            app.offered = None

            offered = app.applicationstatus_set.filter(assigned=ApplicationStatus.OFFERED)
            if offered.exists(): app.offered = offered.last()

        elif status.assigned == ApplicationStatus.ACCEPTED:
            app.accepted = None

            accepted = app.applicationstatus_set.filter(assigned=ApplicationStatus.ACCEPTED)
            if accepted.exists(): app.accepted = accepted.last()

            year_term = '{0}-{1}'.format(app.job.session.year, app.job.session.term.code)
            if year_term in total_accepted_assigned_hours.keys():
                total_accepted_assigned_hours[year_term] += app.accepted.assigned_hours
            else:
                total_accepted_assigned_hours[year_term] = app.accepted.assigned_hours

        elif status.assigned == ApplicationStatus.DECLINED:
            app.declined = None
            declined = app.applicationstatus_set.filter(assigned=ApplicationStatus.DECLINED)
            if declined.exists(): app.declined = declined.last()

        elif status.assigned == ApplicationStatus.CANCELLED:
            app.cancelled = None
            cancelled = app.applicationstatus_set.filter(assigned=ApplicationStatus.CANCELLED)
            if cancelled.exists(): app.cancelled = cancelled.last()

        else:
            pass

    return apps, total_accepted_assigned_hours


# Very important
def get_applications_with_status_by_user(user, status, option=None):
    ''' Get applications of a student with status '''
    total_assigned_hours = {}

    apps = Application.objects.filter( Q(applicant_id=user.id) & Q(applicationstatus__assigned=status) ).distinct()

    for app in apps:
        if status == ApplicationStatus.NONE:
            app.applied = None
            applied = app.applicationstatus_set.filter(assigned=ApplicationStatus.NONE)
            if applied.exists(): app.applied = applied.last()

            app.selected = None
            if app.instructor_preference == Application.ACCEPTABLE or app.instructor_preference == Application.REQUESTED or app.instructor_preference == Application.CRITICAL_REQUESTED:
                app.selected = True

        elif status == ApplicationStatus.OFFERED:
            app.offered = None
            app.accepted = None
            app.declined = None

            offered = app.applicationstatus_set.filter(assigned=ApplicationStatus.OFFERED)
            if offered.exists():
                if option == 'first':
                    app.offered = offered.first()
                else:
                    app.offered = offered.last()

            accpeted = app.applicationstatus_set.filter(assigned=ApplicationStatus.ACCEPTED)
            if accpeted.exists():
                if option == 'first':
                    app.accepted = accpeted.first()
                else:
                    app.accepted = accpeted.last()

            declined = app.applicationstatus_set.filter(assigned=ApplicationStatus.DECLINED)
            if declined.exists():
                if option == 'first':
                    app.declined = declined.first()
                else:
                    app.declined = declined.last()

            year_term = '{0}-{1}'.format(app.job.session.year, app.job.session.term.code)
            if year_term in total_assigned_hours.keys():
                total_assigned_hours[year_term] += app.offered.assigned_hours
            else:
                total_assigned_hours[year_term] = app.offered.assigned_hours

        elif status == ApplicationStatus.ACCEPTED:
            app.accepted = None
            app.cancelled = None

            accepted = app.applicationstatus_set.filter(assigned=ApplicationStatus.ACCEPTED)
            if accepted.exists(): app.accepted = accepted.last()

            cancelled = app.applicationstatus_set.filter(assigned=ApplicationStatus.CANCELLED)
            if cancelled.exists(): app.cancelled = cancelled.last()

            year_term = '{0}-{1}'.format(app.job.session.year, app.job.session.term.code)
            if year_term in total_assigned_hours.keys():
                total_assigned_hours[year_term] += app.accepted.assigned_hours
            else:
                total_assigned_hours[year_term] = app.accepted.assigned_hours

        else:
            app.declined = None
            if option == 'declined only':
                status = app.applicationstatus_set.last()
                if status.assigned == ApplicationStatus.DECLINED:
                    app.declined = status
            else:
                app.declined = app.applicationstatus_set.filter(assigned=ApplicationStatus.DECLINED).last()

    return apps, total_assigned_hours

def get_applications_with_status_by_session_slug_job_slug(session_slug, job_slug):
    ''' Get selected applications by session_slug and job_slug '''
    apps = Application.objects.filter( Q(job__session__slug=session_slug) & Q(job__course__slug=job_slug) )
    for app in apps:
        app.selected = None
        selected = app.applicationstatus_set.filter(assigned=ApplicationStatus.SELECTED)
        if selected.exists(): app.selected = selected.first()

    return apps

"""
def get_selected_applications():
    ''' Get applications selected by instructors '''
    #apps = Application.objects.filter( ~Q(instructor_preference=Application.NONE) & ~Q(instructor_preference=Application.NO_PREFERENCE) ).order_by('job')
    apps = Application.objects.filter(applicationstatus__assigned=ApplicationStatus.SELECTED).order_by('-id')
    for app in apps:
        app.resume_file = None
        if userApi.has_user_resume_created(app.applicant) and bool(app.applicant.resume.file):
            app.resume_file = os.path.basename(app.applicant.resume.file.name)

        app.selected = None
        selected = app.applicationstatus_set.filter(assigned=ApplicationStatus.SELECTED)
        if selected.exists(): app.selected = selected.first()

        app.offered = None
        offered = app.applicationstatus_set.filter(assigned=ApplicationStatus.OFFERED)
        if offered.exists(): app.offered = offered.last()

    return apps
"""

def get_applications_by_status(status):
    ''' Get applications by status '''
    apps = Application.objects.filter(applicationstatus__assigned=status).order_by('-id').distinct()
    for app in apps:
        found_status = app.applicationstatus_set.filter(assigned=status)

        if status == ApplicationStatus.SELECTED:
            app.resume_file = None
            if userApi.has_user_resume_created(app.applicant) and bool(app.applicant.resume.file):
                app.resume_file = os.path.basename(app.applicant.resume.file.name)

            app.selected = None
            selected = app.applicationstatus_set.filter(assigned=ApplicationStatus.SELECTED)
            if selected.exists(): app.selected = selected.first()

            app.offered = None
            offered = app.applicationstatus_set.filter(assigned=ApplicationStatus.OFFERED)
            if offered.exists(): app.offered = offered.last()

        elif status == ApplicationStatus.OFFERED:
            app.offered = None
            if found_status.exists(): app.offered = found_status.last()

        elif status == ApplicationStatus.ACCEPTED:
            app.accepted = None
            if found_status.exists(): app.accepted = found_status.last()

        elif status == ApplicationStatus.DECLINED:
            app.declined = None
            if found_status.exists(): app.declined = found_status.last()

    return apps

def get_offered_applications_with_multiple_ids(ids):
    ''' Get offered applications with multiple ids'''
    apps = get_applications_with_multiple_ids(ids)
    for app in apps:
        offered = app.applicationstatus_set.filter(assigned=ApplicationStatus.OFFERED)
        if offered.exists():
            app.offered = offered.last()
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
    """
    if sent and created_email:
        print( 'Email has sent to {0} and is created'.format(receiver) )
        return True
    elif sent and not created_email:
        print( 'Email has sent to {0} and is created'.format(receiver) )
        if created_email:
            print('The Email sent to {0} is created'.format(receiver))
        else:
            print('The Email sent to {0} is NOT created'.format(receiver))
    else:
        messages.error(request, 'Error! Failed to send an email to {0}'.format(receiver))
    return False"""

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

def terminate_application(app_id):
    ''' Update an application for the termination of an application '''
    app = get_object_or_404(Application, id=app_id)
    app.is_terminated = True
    app.updated_at = datetime.now()
    app.save(update_fields=['is_terminated'])
    return app





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
    term.delete()
    return term if term else False


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
    course_code.delete()
    return course_code if course_code else False



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
    course_number.delete()
    return course_number if course_number else False


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
    course_section.delete()
    return course_section if course_section else False



# ----- classifications -----

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

#-------------------------------------
"""

# to be removed
def get_session_job_by_slug(session_slug, job_slug):
    session = get_session_by_slug(session_slug)
    if session.job_set.filter(course__slug=job_slug).exists():
        return session.job_set.get(course__slug=job_slug)
    raise Http404

    '''for job in session.job_set.all():
        if job.course.slug == job_slug:
            return job
    return None'''



# to be removed
def get_jobs_with_student_applied(session_slug, user):
    session = get_session_by_slug(session_slug)
    jobs = []
    for job in session.job_set.all():
        job.has_applied = False
        if job.application_set.filter(applicant__id=user.id).exists():
            job.has_applied = True
        jobs.append(job)
    return jobs

def get_jobs_applied_by_user(user):
    return Job.objects.filter(application__applicant__id=user.id)

def get_job_application_applied_by_student(user):
    jobs = []
    '''
    for job in get_jobs():
        if job.application_set.filter(applicant__id=user.id).exists():
            jobs.append({
                'details': job,
                'application': application[0]
            })
    '''
    return jobs



def delete_jobs_by_session_id(session):
    result = Job.objects.filter(session_id=session.id).delete()
    return True if result else None



def get_applications_applied_by_student(user):
    ''' Get all applications applied by a student '''

    applications = []
    for job in get_jobs():
        for application in job.application_set.all():
            if application.applicant.id == user.id:
                applications.append(application)

    return applications


def get_course_list_with_student_applied(session_courses, user):
    courses = []
    for course in session_courses:
        course.has_applied = False
        for application in course.applications.all():
            if application.applicant.id == user.id:
                course.has_applied = True

        courses.append(course)

    return courses

def get_courses_including_applications_by_student(user):
    courses = []
    for course in get_courses():
        for application in course.applications.all():
            if application.applicant.id == user.id:
                courses.append(course)

    return courses



def get_courses_by_instructor(user):
    ''' Get courses of an instructor '''

    courses = []
    for course in Course.objects.all():
        for instructor in course.instructors.all():
            if instructor.id == user.id:
                courses.append(course)

    return courses

# Applications

def get_offered_applications_by_student(user):
    applications = []
    for app in get_applications_applied_by_student(user):
        ret = get_offered(app)
        if ret: applications.append(app)
    return applications


def get_applications_by_student(user):
    applications = get_applications()
    return applications.filter(applicant__id=user.id)

def temp():
    for job in Job.objects.all():
        for app in job.application_set.all():
            print(app.id, app.applicationstatus_set.all())



def get_user_job_application_statistics(username):
    num_apps = 0
    num_offered = 0
    num_accepted = 0
    num_declined = 0
    for job in Job.objects.all():
        has_applied_job = False
        if job.application_set.filter(applicant__username=username).exists():
            app = job.application_set.get(applicant__username=username)
            if get_offered(app): num_offered += 1
            if get_accepted(app): num_accepted += 1
            if get_declined(app): num_declined += 1
            num_apps += 1

    return {
        'num_apps': num_apps,
        'num_offered': num_offered,
        'num_accepted': num_accepted,
        'num_declined': num_declined
    }

def get_offered_jobs_by_student(user, student_jobs):
    ''' '''
    jobs = []
    summary = {}
    for job in student_jobs:
        for app in job.application_set.all():
            if app.applicant.id == user.id:
                if app.applicationstatus_set.filter(assigned=ApplicationStatus.OFFERED).exists():
                    status = app.applicationstatus_set.filter(assigned=ApplicationStatus.OFFERED).last()

                    accepted = None
                    declined = None
                    if app.applicationstatus_set.filter(assigned=ApplicationStatus.ACCEPTED).exists():
                        accepted = app.applicationstatus_set.filter(assigned=ApplicationStatus.ACCEPTED).last()
                    if app.applicationstatus_set.filter(assigned=ApplicationStatus.DECLINED).exists():
                        declined = app.applicationstatus_set.filter(assigned=ApplicationStatus.DECLINED).last()

                    jobs.append({
                        'year': job.session.year,
                        'term': job.session.term.code,
                        'course_code': job.course.code.name,
                        'course_number': job.course.number.name,
                        'course_section': job.course.section.name,
                        'assigned_status': 'Offered',
                        'assigned_hours': status.assigned_hours,
                        'assigned_created_at': status.created_at,
                        'session_slug': job.session.slug,
                        'job_slug': job.course.slug,
                        'accepted': accepted,
                        'declined': declined
                    })
                    year_term = '{0}-{1}'.format(job.session.year, job.session.term.code)
                    if year_term in summary.keys():
                        summary[year_term] += status.assigned_hours
                    else:
                        summary[year_term] = status.assigned_hours
    return jobs, summary

def get_accepted_jobs_by_student(user, student_jobs):
    jobs = []
    summary = {}
    for job in student_jobs:
        for app in job.application_set.all():
            if app.applicant.id == user.id:
                if app.applicationstatus_set.filter(assigned=ApplicationStatus.ACCEPTED).exists():
                    status = app.applicationstatus_set.filter(assigned=ApplicationStatus.ACCEPTED).last()
                    jobs.append({
                        'year': job.session.year,
                        'term': job.session.term.code,
                        'course_code': job.course.code.name,
                        'course_number': job.course.number.name,
                        'course_section': job.course.section.name,
                        'assigned_status': 'Accepted',
                        'assigned_hours': status.assigned_hours,
                        'assigned_created_at': status.created_at,
                        'session_slug': job.session.slug,
                        'job_slug': job.course.slug
                    })
                    year_term = '{0}-{1}'.format(job.session.year, job.session.term.code)
                    if year_term in summary.keys():
                        summary[year_term] += status.assigned_hours
                    else:
                        summary[year_term] = status.assigned_hours
    return jobs, summary


def get_declined_jobs_by_student(user, student_jobs):
    jobs = []
    for job in student_jobs:
        for app in job.application_set.all():
            if app.applicant.id == user.id:
                if app.applicationstatus_set.filter(assigned=ApplicationStatus.DECLINED).exists():
                    status = app.applicationstatus_set.get(assigned=ApplicationStatus.DECLINED)
                    jobs.append({
                        'year': job.session.year,
                        'term': job.session.term.code,
                        'course_code': job.course.code.name,
                        'course_number': job.course.number.name,
                        'course_section': job.course.section.name,
                        'assigned_status': 'Declined',
                        'assigned_hours': status.assigned_hours,
                        'assigned_created_at': status.created_at,
                        'session_slug': job.session.slug,
                        'job_slug': job.course.slug
                    })
    return jobs

def get_jobs_with_status_by_user(user, option):
    jobs = Job.objects.filter(application__applicant__id=user.id)
    pass

def get_offered_jobs_by_student2(user, student_jobs):
    jobs = {}
    for job in student_jobs:
        year = job.session.year
        term = job.session.term.code

        if year not in jobs.keys(): jobs[year] = []
        if len( jobs[year] ) > 0:
            for item in jobs[year]:
                if term not in item.keys():
                    jobs[year].append({
                        term: { 'jobs': [], 'total_hours': 0.0 }
                    })
        else:
            jobs[year].append({
                term: { 'jobs': [], 'total_hours': 0.0 }
            })
        #for app in job.applications.filter(applicant__id=user.id):
        for app in job.application_set.filter(applicant__id=user.id):
            for st in app.status.all():
                if st.assigned == ApplicationStatus.OFFERED:
                    for item in jobs[year]:
                        if term in item.keys():
                            item[term]['jobs'].append({
                                'job': '{0} {1} {2}'.format(job.course.code.name, job.course.number.name, job.course.section.name),
                                'assigned_hours': st.assigned_hours,
                                'created_at': st.created_at
                            })
                            item[term]['total_hours'] += st.assigned_hours

    return jobs

def get_accepted_jobs_by_student2(user, student_jobs):
    jobs = {}
    for job in student_jobs:
        year = job.session.year
        term = job.session.term.code

        if year not in jobs.keys(): jobs[year] = []
        if len( jobs[year] ) > 0:
            for item in jobs[year]:
                if term not in item.keys():
                    jobs[year].append({
                        term: { 'jobs': [], 'total_hours': 0.0 }
                    })
        else:
            jobs[year].append({
                term: { 'jobs': [], 'total_hours': 0.0 }
            })
        #for app in job.applications.filter(applicant__id=user.id):
        for app in job.application_set.filter(applicant__id=user.id):
            for st in app.status.all():
                if st.assigned == ApplicationStatus.ACCEPTED:
                    for item in jobs[year]:
                        if term in item.keys():
                            item[term]['jobs'].append({
                                'job': '{0} {1} {2}'.format(job.course.code.name, job.course.number.name, job.course.section.name),
                                'assigned_hours': st.assigned_hours,
                                'created_at': st.created_at
                            })
                            item[term]['total_hours'] += st.assigned_hours

    return jobs


def get_declined_jobs_by_student2(user, student_jobs):
    jobs = {}
    for job in student_jobs:
        year = job.session.year
        term = job.session.term.code

        if year not in jobs.keys(): jobs[year] = []
        if len( jobs[year] ) > 0:
            for item in jobs[year]:
                if term not in item.keys():
                    jobs[year].append({
                        term: { 'jobs': [] }
                    })
        else:
            jobs[year].append({
                term: { 'jobs': [] }
            })

        #for app in job.applications.filter(applicant__id=user.id):
        for app in job.application_set.filter(applicant__id=user.id):
            for st in app.status.all():
                if st.assigned == ApplicationStatus.DECLINED:
                    for item in jobs[year]:
                        if term in item.keys():
                            item[term]['jobs'].append({
                                'job': '{0} {1} {2}'.format(job.course.code.name, job.course.number.name, job.course.section.name),
                                'created_at': st.created_at
                            })

    return jobs


def get_accepted_jobs_by_student2(student_jobs):
    accepted_jobs = {}
    print("student_jobs ", student_jobs)
    for job in student_jobs:
        year = job.session.year
        term = job.session.term.code

        if year not in accepted_jobs.keys(): accepted_jobs[year] = {}
        if term not in accepted_jobs[year].keys(): accepted_jobs[year][term] = {
            'jobs': [],
            'total_hours': 0.0
        }

        #for app in job.applications.all():
        for app in job.application_set.all():
            for st in app.status.all():
                if st.assigned == ApplicationStatus.ACCEPTED:
                    accepted_jobs[year][term]['jobs'].append({
                        'job': '{0} {1} {2}'.format(job.course.code.name, job.course.number.name, job.course.section.name),
                        'assigned_hours': st.assigned_hours
                    })
                    accepted_jobs[year][term]['total_hours'] += st.assigned_hours

    return accepted_jobs

def get_offered_jobs():
    jobs = {}
    for job in Job.objects.all():
        year = job.session.year
        term = job.session.term.code
        print(year, term, job)
    return jobs


# ApplicationStatus
def get_statuses():
    return ApplicationStatus.objects.all()

def get_status(status_id):
    try:
        return ApplicationStatus.objects.get(id=status_id)
    except ApplicationStatus.DoesNotExist:
        return None

def delete_statuses():
    statuses = ApplicationStatus.objects.all().delete()
    return True if statuses else None

# to be removed
def get_jobs_of_instructor(user):
    jobs = []
    for job in get_jobs():
        found = job.instructors.filter(id=user.id)
        if found.count() > 0:
            jobs.append( job )
    return jobs

"""
