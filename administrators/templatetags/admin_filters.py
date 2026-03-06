from django import template

from administrators.models import WorktagSetting
from administrators import api as adminApi

register = template.Library()


@register.filter
def course_name(course):
    return adminApi.get_course_name(course)


@register.filter
def job_name(job):
    return adminApi.get_job_name(job)


@register.filter
def previous_job(course, year):
    job = course.job_set.filter(session__year=int(year)-1)
    return job.first() if job.exists() else None


@register.filter
def worktag_setting(job):
    app_ids = [app.id for app in job.application_set.all()]
    if len(app_ids) > 0:
        return WorktagSetting.objects.filter(application_id__in=app_ids).order_by('-updated_at').first()


@register.filter
def applicant_accepted_apps(app):
    return adminApi.get_accepted_apps_in_applicant(app)
