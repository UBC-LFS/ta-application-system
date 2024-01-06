from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.core.exceptions import SuspiciousOperation

from users import api as userApi

class CustomRemoteUserBackend(ModelBackend):
    def authenticate(self, request, remote_user):
        if not remote_user:
            return
        
        first_name = get_data(request.META, 'first_name')
        last_name = get_data(request.META, 'last_name')
        email = get_data(request.META, 'email')
        username = get_data(request.META, 'username')
        employee_number = get_data(request.META, 'employee_number')
        student_number = get_data(request.META, 'student_number')

        data = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'username': username,
            'employee_number': employee_number,
            'student_number': student_number
        }

        if not username or userApi.contain_user_duplicated_info(data):
            raise SuspiciousOperation

        user = userApi.user_exists(data)
        if not user:
            user = userApi.create_user(data)
            
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
        

# Helper functions

def get_data(meta, field):
    data = settings.SHIB_ATTR_MAP[field]
    if data in meta:
        return meta[data]
    return None