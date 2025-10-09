from django import template
from users import api as userApi
from administrators import api as adminApi
from administrators.models import ApplicationStatus

register = template.Library()


@register.filter
def selected(app):
    return app.applicationstatus_set.filter(assigned=ApplicationStatus.SELECTED).last()


@register.filter
def resume(user):
    usre = userApi.add_resume(user)
    return user.resume_filename


@register.filter
def preferred_ta(user):
    return userApi.get_preferred_ta(user)


@register.filter
def potential_preferred_ta(user):
    return userApi.get_potential_preferred_ta(user)


@register.filter
def applicant_status_program(user):
    return userApi.get_applicant_status_program(user)


@register.filter
def applicant_accepted_apps(app):
    return adminApi.get_accepted_apps_in_applicant(app)