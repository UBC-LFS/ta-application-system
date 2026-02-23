from django.core.exceptions import PermissionDenied
from ta_app import functions as func


def access_superadmin(view_func):
    def wrap(request, *args, **kwargs):
        if func.is_superadmin(request.user):
            return view_func(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return wrap


def access_admin(view_func):
    def wrap(request, *args, **kwargs):
        if func.is_superadmin(request.user) or func.is_admin(request.user):
            return view_func(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return wrap


def access_admin_or_hr(view_func):
    def wrap(request, *args, **kwargs):
        if func.is_superadmin(request.user) or func.is_admin(request.user) or func.is_hr(request.user):
            return view_func(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return wrap


def access_hr(view_func):
    def wrap(request, *args, **kwargs):
        if func.is_hr(request.user):
            return view_func(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return wrap


def access_instructor(view_func):
    def wrap(request, *args, **kwargs):
        if func.is_instructor(request.user):
            return view_func(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return wrap


def access_student(view_func):
    def wrap(request, *args, **kwargs):
        if func.is_student(request.user):
            return view_func(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return wrap


def access_observer(view_func):
    def wrap(request, *args, **kwargs):
        if func.is_observer(request.user):
            return view_func(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return wrap