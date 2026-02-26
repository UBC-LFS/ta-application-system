from django import template

from administrators import api as adminApi

register = template.Library()


@register.filter
def course_name(course):
    print(course)
    return adminApi.get_course_name(course)


@register.filter
def job_name(job):
    return adminApi.get_job_name(job)


@register.filter
def num_jobs(session):
    count = 0
    for job in session.job_set.all():
        if job.course.is_active: 
            count += 1
    return count


@register.filter
def num_instructors(session):
    count = 0
    for job in session.job_set.all():
        if job.course.is_active and job.instructors.count() > 0: 
            count += 1
    return count


@register.filter
def previous_job(course, year):
    job = course.job_set.filter(session__year=int(year)-1)
    return job.first() if job.exists() else None


@register.filter
def applicant_accepted_apps(app):
    return adminApi.get_accepted_apps_in_applicant(app)