import os
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.db.models import Q
import base64

from users.models import *
from users.forms import *
from administrators.models import *
from administrators.forms import ROLES
from administrators import api as adminApi

from datetime import datetime, timedelta
from django.utils.timezone import get_current_timezone

import shutil
from PIL import Image
import random
import string


# for auth

def is_valid_user(user):
    ''' Check if an user is valid or not '''
    if user.is_anonymous or not user.is_authenticated:
        return False
    return True

def is_admin(user, option=None):
    ''' Check if an user is an Admin or Superadmin '''
    if option == 'dict':
        if 'Admin' in user['roles'] or 'Superadmin' in user['roles']: return True
    else:
        if 'Admin' in user.roles or 'Superadmin' in user.roles: return True

    return False

def get_user_roles(user):
    ''' Add roles into an user '''
    roles = []
    for role in user.profile.roles.all():
        if role.name == Role.SUPERADMIN:
            roles.append(Role.SUPERADMIN)
        elif role.name == Role.ADMIN:
            roles.append(Role.ADMIN)
        elif role.name == Role.HR:
            roles.append(Role.HR)
        elif role.name == Role.INSTRUCTOR:
            roles.append(Role.INSTRUCTOR)
        elif role.name == Role.STUDENT:
            roles.append(Role.STUDENT)
        elif role.name == Role.OBSERVER:
            roles.append(Role.OBSERVER)

    return roles

def loggedin_user(user):
    ''' Get a logged in user '''
    if is_valid_user(user) == False:
        raise PermissionDenied

    roles = []
    for role in user.profile.roles.all():
        if role.name == Role.SUPERADMIN:
            roles.append(Role.SUPERADMIN)
        elif role.name == Role.ADMIN:
            roles.append(Role.ADMIN)
        elif role.name == Role.HR:
            roles.append(Role.HR)
        elif role.name == Role.INSTRUCTOR:
            roles.append(Role.INSTRUCTOR)
        elif role.name == Role.STUDENT:
            roles.append(Role.STUDENT)
        elif role.name == Role.OBSERVER:
            roles.append(Role.OBSERVER)
    user.roles = roles

    return user

def has_auth_user_access(request):
    ''' Check if an authenticated user has access '''
    request.user.roles = request.session['loggedin_user']['roles']
    if is_valid_user(request.user) == False:
        raise PermissionDenied
    return request

def has_admin_access(request, role=None):
    ''' Check if an admin has access '''
    request.user.roles = request.session['loggedin_user']['roles']
    if is_admin(request.user) == False and role not in request.user.roles:
        raise PermissionDenied

    return request

def has_user_access(request, role):
    ''' Check if an user has access with a given role '''
    if request.user.is_impersonate:
        if is_admin(request.session['loggedin_user'], 'dict') == False:
            raise PermissionDenied
        request.user.roles = get_user_roles(request.user)
    else:
        request.user.roles = request.session['loggedin_user']['roles']

    if role not in request.user.roles:
        raise PermissionDenied

    return request

def has_users_view_access(request, role):
    ''' Check if users have access to the view of users '''
    request.user.roles = request.session['loggedin_user']['roles']

    custom_roles = []
    for r in request.session['loggedin_user']['roles']:
        if r == Role.SUPERADMIN:
            custom_roles.append('administrators')
        elif r == Role.ADMIN:
            custom_roles.append('administrators')
        elif r == Role.HR:
            custom_roles.append('administrators')
        elif r == Role.INSTRUCTOR:
            custom_roles.append('instructors')
        elif r == Role.STUDENT:
            custom_roles.append('students')

    if is_valid_user(request.user) == False or role not in custom_roles:
        raise PermissionDenied

    return request


# User


def get_user(data, by=None):
    ''' Get a user '''
    if by == 'username':
        return get_object_or_404(User, username=data)
    return get_object_or_404(User, id=data)

def get_users(option=None):
    ''' Get all users '''
    if option == 'destroy':
        target_date = datetime.now(tz=get_current_timezone()) - timedelta(days=3*365)
        return User.objects.filter( Q(last_login__lt=target_date) & Q(profile__is_trimmed=False) ), target_date.strftime('%Y-%m-%d')

    return User.objects.all().order_by('last_name', 'first_name')

def get_instructors():
    ''' Get instructors '''
    return User.objects.filter(profile__roles__name=Role.INSTRUCTOR).order_by('last_name', 'first_name')

def get_users_by_role(role):
    ''' Get users by role '''
    return User.objects.filter(profile__roles__name=role).order_by('last_name', 'first_name')


def user_exists_username(username):
    ''' Check user exists '''
    if User.objects.filter(username=username).exists():
        return User.objects.get(username=username)
    return None

def user_exists(data):
    ''' Check user exists '''

    user = User.objects.filter(username=data['username'])
    if user.exists():
        u = user.first()
        if has_user_profile_created(u) == None:
            user_profile_form = UserProfileForm({
                'student_number': data['student_number'],
                'preferred_name': None,
                'roles': [ ROLES['Student'] ]
            })

            if user_profile_form.is_valid():
                profile = Profile.objects.create(user_id=u.id, student_number=data['student_number'])
                profile.roles.add( *user_profile_form.cleaned_data['roles'] )
        else:
            profile = get_profile(u)
            if profile.student_number is None:
                if data['student_number'] is not None:
                    profile.student_number = data['student_number']
                    profile.save(update_fields=['student_number'])
            else:
                if data['student_number'] is not None and profile.student_number != data['student_number']:
                    profile.student_number = data['student_number']
                    profile.save(update_fields=['student_number'])

        confi = has_user_confidentiality_created(u)
        if confi == None:
            if data['employee_number'] is not None:
                Confidentiality.objects.create(
                    user_id=u.id,
                    employee_number=data['employee_number'],
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
        else:
            if confi.employee_number == None:
                if data['employee_number'] is not None:
                    Confidentiality.objects.filter(user_id=u.id).update(
                        is_new_employee = False,
                        employee_number = data['employee_number']
                    )
            else:
                if data['employee_number'] is not None:
                    update_fields = []
                    if confi.employee_number != data['employee_number']:
                        confi.employee_number = data['employee_number']
                        update_fields.append('employee_number')
                    if confi.is_new_employee == True:
                        confi.is_new_employee = False
                        update_fields.append('is_new_employee')

                    if len(update_fields) > 0:
                        confi.save(update_fields=update_fields)

        return User.objects.get(id=u.id)

    return None


def create_user(data):
    ''' Create a user when receiving data from SAML '''
    first_name = data['first_name']
    last_name = data['last_name']
    email = data['email']
    username = data['username']
    employee_number = data['employee_number']
    student_number = data['student_number']

    user = User.objects.create(
        first_name=first_name,
        last_name=last_name,
        email=email,
        username=username,
        password=make_password( password_generator() )
    )
    if user:
        is_new_employee = True if employee_number == None else False

        confidentiality = Confidentiality.objects.create(
            user_id=user.id,
            is_new_employee=is_new_employee,
            employee_number=employee_number,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        user_profile_form = UserProfileForm({
            'student_number': student_number,
            'preferred_name': None,
            'roles': [ ROLES['Student'] ]
        })
        if user_profile_form.is_valid():
            profile = create_profile(user, user_profile_form.cleaned_data)
            if profile and confidentiality:
                return user

    return False


def contain_user_duplicated_info(data):
    ''' Chceck whether student numbers, employee numbers exist in DB '''

    if data['student_number'] != None:
        sn = Profile.objects.filter(student_number=data['student_number']).exclude(user__username=data['username'])
        if sn.exists():
            return True

    if data['employee_number'] != None:
        en = Confidentiality.objects.filter(employee_number=data['employee_number']).exclude(user__username=data['username'])
        if en.exists():
            return True

    return False


# end user


# Profile


def profile_exists(user):
    ''' Check user's profile exists '''
    if Profile.objects.filter(user__id=user.id).exists():
        return True
    return False

def profile_exists_by_username(username):
    ''' Check user's profile exists '''
    profile = Profile.objects.filter(user__username=username)
    if profile.exists(): return profile
    return False

def has_user_profile_created(user):
    ''' Check an user has a profile '''
    try:
        return user.profile
    except Profile.DoesNotExist:
        return None


def create_profile_init(user):
    return Profile.objects.create(user_id=user.id)


def create_profile(user, data):
    ''' Create an user's profile '''

    student_number = None
    if data['student_number']:
        student_number = data['student_number']

    profile = Profile.objects.create(user_id=user.id, student_number=student_number, preferred_name=data['preferred_name'], is_trimmed=False)
    profile.roles.add( *data['roles'] )

    return profile if profile else False

def get_profile(user):
    try:
        return Profile.objects.get(user_id=user.id)
    except Profile.DoesNotExist:
        return None


def update_student_profile_degrees_trainings(profile, old_degrees, old_trainings, data):
    ''' Update degrees and trainings of a student profile '''

    # Remove current degrees and trainings
    profile.degrees.remove( *old_degrees )
    profile.trainings.remove( *old_trainings )

    new_degrees = list( data.get('degrees') )
    new_trainings = list( data.get('trainings') )

    # Add new degrees and trainings
    profile.degrees.add( *list(new_degrees) )
    profile.trainings.add( *list(new_trainings) )

    return True if profile else None


def update_user_profile_roles(profile, old_roles, data):
    profile.roles.remove( *old_roles )
    new_roles = list( data.get('roles') )
    profile.roles.add( *new_roles )
    return True if profile else False


def get_user_roles(user):
    if has_user_profile_created(user) and hasattr(user.profile, 'roles'):
        return [ role.name for role in user.profile.roles.all() ]
    return  None


def user_has_role(user, role):
    if user.profile.roles.filter(name=role).exists(): return True
    return False


def trim_profile(user):
    ''' Remove user's profile except student_number '''
    profile = has_user_profile_created(user)
    degrees = profile.degrees.all()
    trainings = profile.trainings.all()
    if profile:
        profile.preferred_name = None
        profile.qualifications = None
        profile.prior_employment = None
        profile.special_considerations = None
        profile.status = None
        profile.program = None
        profile.program_others = None
        profile.graduation_date = None
        profile.degree_details = None
        profile.training_details = None
        profile.lfs_ta_training = None
        profile.lfs_ta_training_details = None
        profile.ta_experience = None
        profile.ta_experience_details = None
        profile.is_trimmed = True

        profile.degrees.remove( *degrees )
        profile.trainings.remove( *trainings )

        updated_fields = [
            'preferred_name', 'qualifications', 'prior_employment',
            'special_considerations', 'status', 'program', 'program_others',
            'graduation_date', 'degree_details', 'training_details',
            'lfs_ta_training', 'lfs_ta_training_details', 'ta_experience',
            'ta_experience_details', 'is_trimmed'
        ]
        profile.save(update_fields=updated_fields)

        return True
    return False


# end profile


# Resume

def has_user_resume_created(user):
    ''' Check an user has a resume '''
    try:
        return user.resume
    except Resume.DoesNotExist:
        return None

def add_resume(user):
    ''' Add resume of an user '''
    if has_user_resume_created(user) and bool(user.resume.uploaded):
        user.resume_filename = os.path.basename(user.resume.uploaded.name)
    else:
        user.resume_filename = None
    return user


def delete_user_resume(data):
    ''' Delete user's resume '''
    user = get_user(data, 'username')

    if has_user_resume_created(user) and bool(user.resume.uploaded):
        user.resume.uploaded.delete()
        deleted = user.resume.delete()
        if deleted and not bool(user.resume.uploaded):
            dirpath = os.path.join( settings.MEDIA_ROOT, 'users', user.username, 'resume' )
            if os.path.exists(dirpath) and os.path.isdir(dirpath):
                os.rmdir(dirpath)
                return True
        else:
            return False
    return True


def resume_exists(user):
    ''' Check user's resume exists '''
    if Resume.objects.filter(user__id=user.id).exists():
        return True
    return False


# Avatar

def has_user_avatar_created(user):
    ''' Check an user has an avatar '''
    try:
        return user.avatar
    except Avatar.DoesNotExist:
        return None


def add_avatar(user):
    ''' Add avatar of an user '''
    if has_user_avatar_created(user) and bool(user.avatar.uploaded):
        user.avatar_filename = os.path.basename(user.avatar.uploaded.name)
        content = None
        with user.avatar.uploaded.open() as f:
            content = f.read()
        url = 'data:image/jpg;base64,' + base64.b64encode(content).decode('utf-8')

        user.avatar_file = {
            'filename': os.path.basename(user.avatar.uploaded.name),
            'url': url,
            'created_at': user.avatar.created_at
        }
    else:
        user.avatar_file = None
    return user


def delete_user_avatar(data):
    ''' Delete user's resume '''
    user = get_user(data, 'username')

    if has_user_avatar_created(user) and bool(user.avatar.uploaded):
        user.avatar.uploaded.delete()
        deleted = user.avatar.delete()
        if deleted and not bool(user.avatar.uploaded):
            dirpath = os.path.join( settings.MEDIA_ROOT, 'users', user.username, 'avatar' )
            if os.path.exists(dirpath) and os.path.isdir(dirpath):
                os.rmdir(dirpath)
                return True
        else:
            return False
    return True


# Confidentiality


def create_confidentiality(user):
    return Confidentiality.objects.create(user_id=user.id, created_at=datetime.now(), updated_at=datetime.now())


def confidentiality_exists(user):
    ''' Check user's confidentiality exists '''
    if Confidentiality.objects.filter(user__id=user.id).exists():
        return True
    return False


def has_user_confidentiality_created(user):
    ''' Check an user has a confidentiality '''
    try:
        return user.confidentiality
    except Confidentiality.DoesNotExist:
        return None


def add_confidentiality_given_list(user, array):
    ''' Add confidentiality of an user '''

    if has_user_confidentiality_created(user):
        if bool(user.confidentiality.sin) and 'sin' in array:
            user.sin_decrypt_image = decrypt_image(user.confidentiality.sin)
        else:
            user.sin_decrypt_image = None

        if bool(user.confidentiality.study_permit) and 'study_permit' in array:
            user.study_permit_decrypt_image = decrypt_image(user.confidentiality.study_permit)
        else:
            user.study_permit_decrypt_image = None

    return user


def add_confidentiality_validation(user):
    ''' Add confidentiality validation into apps '''
    confidentiality = has_user_confidentiality_created(user)

    message = ''
    if confidentiality != None:
        errors = ''

        if bool(confidentiality.employee_number) == False and confidentiality.is_new_employee == False:
            errors += '<li>Employee Number</li>'
        if bool(confidentiality.date_of_birth) == False:
            errors += '<li>Date of Birth</li>'
        if bool(confidentiality.sin) == False:
            errors += '<li>SIN</li>'

        # if international students are 1; otherwise, 0
        if confidentiality.nationality == '1':
            today = datetime.now()
            if bool(confidentiality.sin_expiry_date) == False or confidentiality.sin_expiry_date < today.date():
                errors += '<li>SIN Expiry Date</li>'
            if bool(confidentiality.study_permit) == False:
                errors += '<li>Study Permit</li>'
            if bool(confidentiality.study_permit_expiry_date) == False or confidentiality.study_permit_expiry_date < today.date():
                errors += '<li>Study Permit Expiry Date</li>'

        if len(errors) > 0:
            message = 'Please check the following information, and update required documents. <ul>{0}</ul>'.format(errors)
    else:
        message = "You haven't completed it yet. Please upload required documents."

    return {
        'status': True if len(message) == 0 else False,
        'message': message
    }


def delete_confidential_information(data):
    ''' Delete your confidential information '''

    username = data.get('user')
    date_of_birth = data.get('date_of_birth')
    employee_number = data.get('employee_number')
    sin = data.get('sin')
    sin_expiry_date = data.get('sin_expiry_date')
    study_permit = data.get('study_permit')
    study_permit_expiry_date = data.get('study_permit_expiry_date')

    user = get_user(username, 'username')
    confidentiality = Confidentiality.objects.filter(user_id=user.id)

    errors = []
    if date_of_birth is not None:
        if confidentiality.update(date_of_birth=None) == False:
            errors.append('Date of Birth')

    if employee_number is not None:
        if confidentiality.update(employee_number=None) == False:
            errors.append('Employee Number')

    if sin is not None:
        if sin_expiry_date is not None:
            if delete_user_sin(username, '1') == False:
                errors.append('SIN and SIN expiry date')
        else:
            if delete_user_sin(username) == False:
                errors.append('SIN')
    else:
        if sin_expiry_date is not None:
            if confidentiality.update(sin_expiry_date=None) == False:
                errors.append('SIN Expiry Date')

    if study_permit is not None:
        if study_permit_expiry_date is not None:
            if delete_user_study_permit(username, '1') == False:
                errors.append('Study Permit and Study Permit Expiry Date')
        else:
            if delete_user_study_permit(username) == False:
                errors.append('Study Permit')
    else:
        if study_permit_expiry_date is not None:
            if confidentiality.update(study_permit_expiry_date=None) == False:
                errors.append('Study Permit Expiry Date')

    return True if len(errors) == 0 else ', '.join(errors)


def delete_user_sin(username, option=None):
    ''' Delete user's SIN '''
    user = get_user(username, 'username')

    if has_user_confidentiality_created(user) and bool(user.confidentiality.sin):
        user.confidentiality.sin.close()
        if user.confidentiality.sin.closed:
            try:
                user.confidentiality.sin.delete(save=False)
                if option == '1':
                    deleted = Confidentiality.objects.filter(user_id=user.id).update(sin=None, sin_expiry_date=None)
                else:
                    deleted = Confidentiality.objects.filter(user_id=user.id).update(sin=None)

                if deleted and not bool(user.confidentiality.sin):
                    dirpath = os.path.join(settings.MEDIA_ROOT, 'users', username, 'sin')
                    if os.path.exists(dirpath) and os.path.isdir(dirpath):
                        os.rmdir(dirpath)
                        return True
                else:
                    return False
            except OSError:
                print('sin OSError')
                return False
        else:
            return False
    return True


def delete_user_study_permit(username, option=None):
    ''' Delete user's study permit '''
    user = get_user(username, 'username')

    if has_user_confidentiality_created(user) and bool(user.confidentiality.study_permit):
        user.confidentiality.study_permit.close()
        if user.confidentiality.study_permit.closed:
            try:
                user.confidentiality.study_permit.delete(save=False)
                deleted = None
                if option == '1':
                    deleted = Confidentiality.objects.filter(user_id=user.id).update(study_permit=None, study_permit_expiry_date=None)
                else:
                    deleted = Confidentiality.objects.filter(user_id=user.id).update(study_permit=None)

                if deleted and not bool(user.confidentiality.study_permit):
                    dirpath = os.path.join(settings.MEDIA_ROOT, 'users', username, 'study_permit')
                    if os.path.exists(dirpath) and os.path.isdir(dirpath):
                        os.rmdir(dirpath)
                        return True
                else:
                    return False
            except OSError:
                print('study permit OSError')
                return False
        else:
            return False
    return True


# end Confidentiality


def create_expiry_date(year, month, day):
    if not bool(year) or not bool(month) or not bool(day): return False
    return datetime( int(year), int(month), int(day) )


def can_apply(user):
    ''' Check whether students can apply or not '''
    profile = has_user_profile_created(user)
    trainings = get_trainings()

    if has_user_resume_created(user) is not None and profile is not None:
        if profile.graduation_date is not None and profile.status is not None and profile.program is not None and \
            profile.degree_details is not None and profile.training_details is not None and profile.lfs_ta_training is not None and \
            profile.lfs_ta_training_details is not None and profile.ta_experience is not None and \
            profile.ta_experience_details is not None and profile.qualifications is not None and profile.trainings.count() == len(trainings) and profile.degrees.count() > 0:
            if len(profile.degree_details) > 0 and len(profile.training_details) > 0 and \
                len(profile.lfs_ta_training_details) > 0 and len(profile.ta_experience_details) > 0 and \
                len(profile.qualifications) > 0:
                return True
    return False

# Roles

def get_roles():
    ''' Get all roles '''
    return Role.objects.all()

def get_role(role_id):
    ''' Get a role by id '''
    return get_object_or_404(Role, id=role_id)

def get_role_by_slug(slug):
    ''' Get a role by code '''
    return get_object_or_404(Role, slug=slug)

def delete_role(role_id):
    ''' Delete a role '''
    role = get_role(role_id)
    role.delete()
    return role if role else False





# Statuses

def get_statuses():
    ''' Get all statuses '''
    return Status.objects.all()

def get_status(status_id):
    ''' Get a status by id '''
    return get_object_or_404(Status, id=status_id)

def get_status_by_slug(slug):
    ''' Get a status by code '''
    return get_object_or_404(Status, slug=slug)

def delete_status(status_id):
    ''' Delete a status '''
    status = get_status(status_id)
    status.delete()
    return status if status else False

def get_undergraduate_status_id():
    status = Status.objects.filter(name__icontains='undergraduate')
    if status.exists():
        return status.first().id
    else:
        return None

# programs

def get_programs():
    ''' Get all programs '''
    return Program.objects.all()

def get_program(program_id):
    ''' Get a program by id '''
    return get_object_or_404(Program, id=program_id)

def get_program_by_slug(slug):
    ''' Get a program by code '''
    return get_object_or_404(Program, slug=slug)

def delete_program(program_id):
    ''' Delete a program '''
    program = get_program(program_id)
    program.delete()
    return program if program else False

def get_program_others_id():
    ''' Get id of others in program '''
    program = Program.objects.filter(name__icontains='other')
    if program.exists():
        return program.first().id
    else:
        return None

# Degrees

def get_degrees():
    ''' Get all degrees '''
    return Degree.objects.all()

def get_degree(degree_id):
    ''' Get a degree by id '''
    return get_object_or_404(Degree, id=degree_id)

def get_degree_by_slug(slug):
    ''' Get a degree by code '''
    return get_object_or_404(Degree, slug=slug)

def delete_degree(degree_id):
    ''' Delete a degree '''
    degree = get_degree(degree_id)
    degree.delete()
    return degree if degree else False


# trainings

def get_trainings():
    ''' Get all trainings '''
    return Training.objects.all()

def get_training(training_id):
    ''' Get a training by id '''
    return get_object_or_404(Training, id=training_id)

def get_training_by_slug(slug):
    ''' Get a training by code '''
    return get_object_or_404(Training, slug=slug)

def delete_training(training_id):
    ''' Delete a training '''
    training = get_training(training_id)
    training.delete()
    return training if training else False




# Helper methods
def validate_post(post, list):
    errors = []
    for field in list:
        if post.get(field) == None:
            errors.append(field.upper().replace('_', ' '))
    return errors

def get_error_messages(errors):
    messages = ''
    for key in errors.keys():
        value = errors[key]
        messages += key.replace('_', ' ').upper() + ': ' + value[0]['message'] + ' '
    return messages.strip()

def password_generator():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=50))
