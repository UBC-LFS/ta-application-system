from django import template
from users import api as userApi
from administrators import api as adminApi
from administrators.models import ApplicationStatus
from ta_app import utils

register = template.Library()


@register.filter
def selected(app):
    return app.applicationstatus_set.filter(assigned=utils.SELECTED).last()


@register.filter
def resume(user):
    return userApi.add_resume(user).resume_filename


@register.filter
def preferred_candidate(user, year):
    return userApi.get_preferred_candidate(user, year)


@register.filter
def applicant_status_program(user):
    return userApi.get_applicant_status_program(user)


@register.filter
def gta(user):
    return userApi.get_gta_flag(user)
