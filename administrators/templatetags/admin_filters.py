from django import template

from administrators import api as adminApi

register = template.Library()


@register.filter
def job_full_name(job):
    return adminApi.get_job_full_name(job)


@register.filter
def previous_job(course, year):
    job = course.job_set.filter(session__year=int(year)-1)
    return job.first() if job.exists() else None


@register.filter
def applicant_accepted_apps(app):
    return adminApi.get_accepted_apps_in_applicant(app)