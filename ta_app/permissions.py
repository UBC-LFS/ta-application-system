from django.core.exceptions import PermissionDenied
from users import api as userApi


def access_superadmin(view_func):
    def wrap(request, *args, **kwargs):
        if userApi.is_superadmin(request.user):
            return view_func(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return wrap


def access_admin(view_func):
    def wrap(request, *args, **kwargs):
        if userApi.is_superadmin(request.user) or userApi.is_admin(request.user):
            return view_func(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return wrap
