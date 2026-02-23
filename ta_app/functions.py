from django.db.models import Q

from ta_app import utils


def redirect_index(roles):
    admin = roles.filter( Q(name=utils.SUPERADMIN) | Q(name=utils.ADMIN) | Q(name=utils.HR)).exists()
    instructor = roles.filter(name=utils.INSTRUCTOR).exists()
    observer = roles.filter(name=utils.OBSERVER).exists()

    if admin:
        return '/app/administrators/'
    elif instructor:
        return '/app/instructors/'
    elif observer:
        return '/app/observers/'

    return '/app/students/'


def is_superadmin(user):
    if hasattr(user, 'profile'):
        if user.profile.roles.exists() and user.profile.roles.filter(name=utils.SUPERADMIN):
            return True
    return False


def is_admin(user):
    if hasattr(user, 'profile'):
        if user.profile.roles.exists() and user.profile.roles.filter(name=utils.ADMIN):
            return True
    return False


def is_instructor(user):
    if hasattr(user, 'profile'):
        if user.profile.roles.exists() and user.profile.roles.filter(name=utils.INSTRUCTOR):
            return True
    return False


def is_hr(user):
    if hasattr(user, 'profile'):
        if user.profile.roles.exists() and user.profile.roles.filter(name=utils.HR):
            return True
    return False


def is_student(user):
    if hasattr(user, 'profile'):
        if user.profile.roles.exists() and user.profile.roles.filter(name=utils.STUDENT):
            return True
    return False


def is_observer(user):
    if hasattr(user, 'profile'):
        if user.profile.roles.exists() and user.profile.roles.filter(name=utils.OBSERVER):
            return True
    return False


def get_job_full_name(job):
    return '{0} {1} {2}'.format(job.course.code.name, job.course.number.name, job.course.section.name)