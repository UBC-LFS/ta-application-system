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
    ''' '''
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
    """ Get all sessions """
    return Session.objects.all()

def session_exists(session_id):
    """ Check a session exists """
    if Session.objects.filter(id=session_id).exists():
        return True
    return False

def get_session(session_id):
    """ Get a session """
    try:
        return Session.objects.get(id=session_id)
    except Session.DoesNotExist:
        return None

def get_session_by_slug(session_slug):
    ''' Get a session by slug '''
    return get_object_or_404(Session, slug=session_slug)

def get_sessions_by_year(year):
    """ Get sessions by year """
    return Session.objects.filter(year=year)

def get_current_sessions():
    ''' '''
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
    ''' '''
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

def get_active_sessions():
    return []

def get_inactive_sessions():
    return []

def get_visible_current_sessions():
    sessions = []
    for session in Session.objects.all():
        if session.is_visible and not session.is_archived:
            count = 0
            for job in session.job_set.all():
                if job.instructors.count() > 0:
                    count += 1
            session.num_instructors = count
            sessions.append(session)
    return sessions

def get_not_visible_active_sessions():
    return Session.objects.filter(is_visible=False, is_archived=False)



#checked
def delete_session(session_id):
    """ Delete a session """
    try:
        session = Session.objects.get(id=session_id)
        session.delete()
        return session
    except Session.DoesNotExist:
        return None

def update_session_jobs(session, courses):
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

        # if no difference, nothing updated
        if len(diff) == 0:
            return True

        deleted = delete_jobs_by_course_ids(session, diff)
        if deleted:
            new = list( set(new_course_ids) - set(intersection) )
            if len(new) > 0:
                courses = [ get_course(id) for id in new ]
                return create_jobs(session, courses)
            return True
        else:
            return None


# Jobs

def get_jobs():
    ''' Get all jobs '''
    return Job.objects.all()

def get_session_job_by_slug(session_slug, job_slug):
    ''' Get a job by session slug and job slug '''
    session = get_session_by_slug(session_slug)
    if session.job_set.filter(course__slug=job_slug).exists():
        return session.job_set.get(course__slug=job_slug)
    raise Http404

    """for job in session.job_set.all():
        if job.course.slug == job_slug:
            return job
    return None"""



# checked
def get_jobs_with_student_applied(session_slug, user):
    """ Get all jobs which a student applied to """
    session = get_session_by_slug(session_slug)
    jobs = []
    for job in session.job_set.all():
        job.has_applied = False
        if job.application_set.filter(applicant__id=user.id).exists():
            job.has_applied = True
        jobs.append(job)
    return jobs

def has_applied_job(session_slug, job_slug, user):
    """ Check if a user has applied for a job or not """
    session = get_session_by_slug(session_slug)
    for job in session.job_set.all():
        if job.course.slug == job_slug:
            if job.application_set.filter(applicant__id=user.id).exists():
                return True
    return False


def get_job_application_applied_by_student(user):
    jobs = []
    """
    for job in get_jobs():
        if job.application_set.filter(applicant__id=user.id).exists():
            jobs.append({
                'details': job,
                'application': application[0]
            })
    """
    return jobs


def get_jobs_applied_by_student(user):
    ''' Get all jobs applied by a student '''
    jobs = []
    for job in get_jobs():
        if job.application_set.filter(applicant__id=user.id).exists():
            my_application = job.application_set.get(applicant__id=user.id)
            job.my_application = my_application
            jobs.append(job)
    return jobs

#checked
def get_job_applied_by_student(user, session_slug, job_slug):
    """ Get a job applied by a student """
    jobs = get_jobs_applied_by_student(user)
    for job in jobs:
        if job.session.slug == session_slug and job.course.slug == job_slug:
            return job
    return None


def get_application_by_student_id_job(user_id, job):
    ''' '''
    if job.application_set.filter(applicant__id=user_id).exists():
        return job.application_set.get(applicant__id=user_id)
    return None

'''
def get_application_by_student_id_job(user_id, job):
    try:
        return job.applications.get(applicant__id=user_id)
    except Application.DoesNotExist:
        return None
'''

#checked
def get_application_by_student_job(user, job):
    try:
        return job.application_set.get(applicant__id=user.id)
    except Application.DoesNotExist:
        return None

'''
def get_application_by_student_job(user, job):
    try:
        return job.applications.get(applicant__id=user.id)
    except Application.DoesNotExist:
        return None
'''

def create_jobs(session, courses):
    objs = [ Job(session=session, course=course) for course in courses ]
    jobs = Job.objects.bulk_create(objs)
    return True if jobs else None

def delete_jobs_by_session_id(session):
    result = Job.objects.filter(session_id=session.id).delete()
    return True if result else None

def delete_jobs_by_course_ids(session, course_ids):
    result = Job.objects.filter(session_id=session.id, course_id__in=course_ids).delete()
    return True if result else None



def update_job_instructors(job, old_instructors, new_instructors):
    job.instructors.remove( *old_instructors )
    job.instructors.add( *list(new_instructors) )
    return True if job else None


def update_job_ta_hours(session_slug, job_slug, ta_hours):
    job = get_session_job_by_slug(session_slug, job_slug)
    new_hours = job.ta_hours + float(ta_hours)
    job.ta_hours = new_hours
    saved = job.save(update_fields=['ta_hours'])
    print('saved ', saved)
    return True if job else False

def get_recent_ten_job_details(course):
    return Job.objects.filter( Q(course__code=course.code) & Q(course__number=course.number) ).order_by('-created_at')[:10]

def get_applications_applied_by_student(user):
    """ Get all applications applied by a student """

    applications = []
    for job in get_jobs():
        for application in job.application_set.all():
            if application.applicant.id == user.id:
                applications.append(application)

    return applications


def get_course_list_with_student_applied(session_courses, user):
    """ Get all courses which a student applied to """

    courses = []
    for course in session_courses:
        course.has_applied = False
        for application in course.applications.all():
            if application.applicant.id == user.id:
                course.has_applied = True

        courses.append(course)

    return courses

def get_courses_including_applications_by_student(user):
    """ Get all courses including a student's application """

    courses = []
    for course in get_courses():
        for application in course.applications.all():
            if application.applicant.id == user.id:
                courses.append(course)

    return courses



def get_courses_by_instructor(user):
    """ Get courses of an instructor """

    courses = []
    for course in Course.objects.all():
        for instructor in course.instructors.all():
            if instructor.id == user.id:
                courses.append(course)

    return courses








# Applications

def update_application_instructor_preference(application_id, instructor_preference):
    application = get_object_or_404(Application, id=application_id)
    application.instructor_preference = instructor_preference
    application.updated_at = datetime.now()
    application.save(update_fields=['instructor_preference', 'updated_at'])
    return application


def update_application_classification_note(application_id, data):
    classification = data.get('classification')
    note = data.get('note')
    try:
        application = get_application(application_id)
        application.classification = classification
        application.note = note
        application.save(update_fields=['classification', 'note'])
        return application
    except Application.DoesNotExist:
        return None


def get_applications(option=None):
    ''' Get all applications '''
    if not option:
        return Application.objects.all().order_by('id')
    return Application.objects.all().order_by(option)

def get_application_statuses():
    return ApplicationStatus.objects.all().order_by('-id')

def get_offered_applications_by_student(user):
    applications = []
    for app in get_applications_applied_by_student(user):
        ret = get_offered(app)
        if ret: applications.append(app)
    return applications

def get_selected_applications():
    applications = []
    for app in Application.objects.all():
        if app.instructor_preference != Application.NONE and app.instructor_preference != Application.NO_PREFERENCE:
            app.resume_file = None
            if userApi.has_user_resume_created(app.applicant) and app.applicant.resume.file != None:
                app.resume_file = os.path.basename(app.applicant.resume.file.name)

            app.has_offered = None
            for st in app.applicationstatus_set.all():
                if st.assigned == ApplicationStatus.OFFERED:
                    app.has_offered = st.assigned_hours
            applications.append(app)
    return applications

def get_offered_applications():
    applications = []
    for app in get_applications():
        offered = get_offered(app)
        if offered:
            applications.append(app)
    return applications


def get_accepted_applications():
    applications = []
    for app in get_applications():
        app.has_accepted = None

        for st in app.applicationstatus_set.all().order_by('id'):
            if st.assigned == ApplicationStatus.ACCEPTED:
                app.has_accepted = st.assigned_hours

        if app.has_accepted:
            applications.append(app)

    return applications

def get_accepted_status(app):
    for st in app.applicationstatus_set.all().order_by('-id'):
        if st.assigned == ApplicationStatus.ACCEPTED:
            return st
    return None

def get_declined_applications():
    applications = []
    for app in get_applications():
        declined = get_declined(app)
        if declined:
            applications.append(app)
    return applications

#checked
def get_application(app_id):
    ''' Get an application '''
    print('get_application ==== ', app_id)
    return get_object_or_404(Application, id=app_id)

def get_application_slug(app_slug):
    ''' Get an application '''
    return get_object_or_404(Application, slug=app_slug)

def get_applications_by_student(user):
    applications = get_applications()
    return applications.filter(applicant__id=user.id)

def temp():
    for job in Job.objects.all():
        for app in job.application_set.all():
            print(app.id, app.applicationstatus_set.all())

def get_jobs_with_applications_statistics():
    ''' '''
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

def get_offered(app):
    if app.applicationstatus_set.filter(assigned=ApplicationStatus.OFFERED).exists():
        return app.applicationstatus_set.get(assigned=ApplicationStatus.OFFERED)
    return False

def get_accepted(app):
    if app.applicationstatus_set.filter(assigned=ApplicationStatus.ACCEPTED).exists():
        return app.applicationstatus_set.get(assigned=ApplicationStatus.ACCEPTED)
    return False


def get_declined(app):
    if app.applicationstatus_set.filter(assigned=ApplicationStatus.DECLINED).exists():
        return app.applicationstatus_set.filter(assigned=ApplicationStatus.DECLINED)
    return False


def get_offered_jobs_by_student(user, student_jobs):
    ''' '''
    jobs = []
    summary = {}
    for job in student_jobs:
        for app in job.application_set.all():
            if app.applicant.id == user.id:
                if app.applicationstatus_set.filter(assigned=ApplicationStatus.OFFERED).exists():
                    status = app.applicationstatus_set.get(assigned=ApplicationStatus.OFFERED)

                    accepted = None
                    declined = None
                    if app.applicationstatus_set.filter(assigned=ApplicationStatus.ACCEPTED).exists():
                        accepted = app.applicationstatus_set.get(assigned=ApplicationStatus.ACCEPTED)
                    if app.applicationstatus_set.filter(assigned=ApplicationStatus.DECLINED).exists():
                        declined = app.applicationstatus_set.get(assigned=ApplicationStatus.DECLINED)

                    jobs.append({
                        'year': job.session.year,
                        'term': job.session.term.code,
                        'course_code': job.course.code.name,
                        'course_number': job.course.number.name,
                        'course_section': job.course.section.name,
                        'assigned_status': 'Offered',
                        'assigned_hours': status.assigned_hours,
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
                    status = app.applicationstatus_set.get(assigned=ApplicationStatus.ACCEPTED)
                    jobs.append({
                        'year': job.session.year,
                        'term': job.session.term.code,
                        'course_code': job.course.code.name,
                        'course_number': job.course.number.name,
                        'course_section': job.course.section.name,
                        'assigned_status': 'Accepted',
                        'assigned_hours': status.assigned_hours,
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
                        'session_slug': job.session.slug,
                        'job_slug': job.course.slug
                    })
    return jobs

def student_apply_job(app):
    app_status = ApplicationStatus.objects.create(application=app, assigned=ApplicationStatus.NONE, assigned_hours=0.0)
    return app_status if app_status else None



"""
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
"""


def get_offered_jobs():
    jobs = {}
    for job in Job.objects.all():
        year = job.session.year
        term = job.session.term.code
        print(year, term, job)
    return jobs



# Program
def get_program(program_id):
    """ Get a program """

    try:
        return Program.objects.get(id=program_id)
    except Program.DoesNotExist:
        return None







# Degree

def get_degree(degree_id):
    """ Get a degree """

    try:
        return Degree.objects.get(id=degree_id)
    except Degree.DoesNotExist:
        return None

def get_degrees():
    print("get_degrees")
    degrees = None
    try:
        degrees = Degree.objects.all().order_by('id')
        print("haha")
    except Degree.DoesNotExist:
        print("not ")
        degrees = None
    print("degrees ", degrees)
    return degrees

def get_degrees_list():
    print("get_degrees_list")
    print("here")
    try:
        return [ (degree.id, degree.name) for degree in get_degrees() ]
    except Degree.DoesNotExist:
        print("not ")
        return None


# Training
def get_training(training_id):
    try:
        return Training.objects.get(id=training_id)
    except Training.DoesNotExist:
        return None

def get_trainings():
    return Training.objects.all().order_by('id')

def get_trainings_list():
    print("get_trainings_list")
    try:
        return [ (training.id, training.name) for training in get_trainings() ]
    except Training.DoesNotExist:
        return None





# ApplicationStatus
def get_statuses():
    """ Get all statuses """

    return ApplicationStatus.objects.all()

def get_status(status_id):
    """ Get a status """

    try:
        return ApplicationStatus.objects.get(id=status_id)
    except ApplicationStatus.DoesNotExist:
        return None

def delete_statuses():
    """ Delete all statuses """

    statuses = ApplicationStatus.objects.all().delete()
    return True if statuses else None



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


def send_and_create_email(sender, receiver, title, message, type):
    # Reference: https://docs.djangoproject.com/en/2.2/topics/email/
    #sent = send_mail(title, message, sender, [receiver], fail_silently=False)
    msg = EmailMultiAlternatives(title, message, sender, [receiver])
    msg.attach_alternative(message, "text/html")
    msg.send()

    created_email = Email.objects.create(
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


def get_emails():
    return Email.objects.all()


# to be removed
def get_jobs_of_instructor(user):
    """ Get jobs of an instructor """
    jobs = []
    for job in get_jobs():
        found = job.instructors.filter(id=user.id)
        if found.count() > 0:
            jobs.append( job )
    return jobs
