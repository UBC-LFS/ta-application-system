from django import template
from administrators.models import ApplicationReset
from users import api as userApi
from ta_app import utils

register = template.Library()


@register.filter
def selected(app):
    if app.applicationstatus_set.last().assigned != utils.NONE:
        return app.applicationstatus_set.filter(assigned=utils.SELECTED).last()


@register.filter
def resume(user):
    return userApi.add_resume(user).resume_filename


@register.filter
def lfs_ta(user, year):
    return userApi.get_lfs_ta(user, year)


@register.filter
def lfs_grad_or_others(user):
    return userApi.get_lfs_grad_or_others(user)


@register.filter
def applicant_status_program(user):
    return userApi.get_applicant_status_program(user)


@register.filter
def gta(user):
    return userApi.get_gta_flag(user)
