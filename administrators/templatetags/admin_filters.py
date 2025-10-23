from django import template
from users import api as userApi
from administrators import api as adminApi
from administrators.models import ApplicationStatus
from django.utils.html import strip_tags

register = template.Library()


@register.filter
def applicant_accepted_apps(app):
    return adminApi.get_accepted_apps_in_applicant(app)