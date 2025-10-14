from django import template
from users import api as userApi
from administrators import api as adminApi
from administrators.models import ApplicationStatus
from django.utils.html import strip_tags

register = template.Library()

