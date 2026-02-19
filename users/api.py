import os
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.db.models import Q
import base64

from ta_app import utils
from users.models import *
from users.forms import *
from administrators.models import *
from administrators.forms import ROLES
from administrators import api as adminApi

from datetime import datetime, timedelta
from django.utils.timezone import get_current_timezone

import random
import string


# for auth

def is_valid_user(user):
    ''' Check if an user is valid or not '''
    if user.is_anonymous or not user.is_authenticated:
        return False
    return True


def is_superadmin(user, option=None):
    ''' Check if an user is a Superadmin '''
    if option == 'dict':
        if 'Superadmin' in user['roles']: return True
    else:
        if 'Superadmin' in user.roles: return True
    return False


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
        if role.name == utils.SUPERADMIN:
            roles.append(utils.SUPERADMIN)
        elif role.name == utils.ADMIN:
            roles.append(utils.ADMIN)
        elif role.name == utils.HR:
            roles.append(utils.HR)
        elif role.name == utils.INSTRUCTOR:
            roles.append(utils.INSTRUCTOR)
        elif role.name == utils.STUDENT:
            roles.append(utils.STUDENT)
        elif role.name == utils.OBSERVER:
            roles.append(utils.OBSERVER)

    return roles

def loggedin_user(user):
    ''' Get a logged in user '''
    if is_valid_user(user) == False:
        raise PermissionDenied

    roles = []
    for role in user.profile.roles.all():
        if role.name == utils.SUPERADMIN:
            roles.append(utils.SUPERADMIN)
        elif role.name == utils.ADMIN:
            roles.append(utils.ADMIN)
        elif role.name == utils.HR:
            roles.append(utils.HR)
        elif role.name == utils.INSTRUCTOR:
            roles.append(utils.INSTRUCTOR)
        elif role.name == utils.STUDENT:
            roles.append(utils.STUDENT)
        elif role.name == utils.OBSERVER:
            roles.append(utils.OBSERVER)
    user.roles = roles

    return user

def has_auth_user_access(request):
    ''' Check if an authenticated user has access '''
    request.user.roles = request.session['loggedin_user']['roles']
    if is_valid_user(request.user) == False:
        raise PermissionDenied
    return request


def has_superadmin_access(request, role=None):
    ''' Check if a superadmin has access '''
    request.user.roles = request.session['loggedin_user']['roles']
    if not is_superadmin(request.user) and role not in request.user.roles:
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
        if r == utils.SUPERADMIN:
            custom_roles.append('administrators')
        elif r == utils.ADMIN:
            custom_roles.append('administrators')
        elif r == utils.HR:
            custom_roles.append('administrators')
        elif r == utils.INSTRUCTOR:
            custom_roles.append('instructors')
        elif r == utils.STUDENT:
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
    return User.objects.filter(profile__roles__name=utils.INSTRUCTOR).order_by('last_name', 'first_name')

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

    u = User.objects.filter(username=data['username'])
    if u.exists():
        user = u.first()

        # Update user information if it's None
        update_fields = []
        if not user.first_name and data['first_name']:
            user.first_name = data['first_name']
            update_fields.append('first_name')

        if not user.last_name and data['last_name']:
            user.last_name = data['last_name']
            update_fields.append('last_name')

        if not user.email and data['email']:
            user.email = data['email']
            update_fields.append('email')

        if len(update_fields) > 0:
            user.save(update_fields=update_fields)

        # To check if profile information exists or not
        if has_user_profile_created(user) == None:
            user_profile_form = UserProfileForm({
                'student_number': data['student_number'],
                'preferred_name': None,
                'roles': [ ROLES['Student'] ]
            })

            if user_profile_form.is_valid():
                profile = Profile.objects.create(
                    user_id=user.id,
                    student_number=data['student_number']
                )
                profile.roles.add( *user_profile_form.cleaned_data['roles'] )
        else:
            profile = get_profile(user)
            if profile.student_number is None:
                if data['student_number'] is not None:
                    profile.student_number = data['student_number']
                    profile.save(update_fields=['student_number'])
            else:
                if data['student_number'] is not None and profile.student_number != data['student_number']:
                    profile.student_number = data['student_number']
                    profile.save(update_fields=['student_number'])

        # To check if confidential information exists or not
        confi = has_user_confidentiality_created(user)
        if confi:
            if confi.employee_number:
                if data['employee_number']:
                    update_fields = []
                    if confi.employee_number != data['employee_number']:
                        confi.employee_number = data['employee_number']
                        update_fields.append('employee_number')
                    if confi.is_new_employee == True:
                        confi.is_new_employee = False
                        update_fields.append('is_new_employee')

                    if len(update_fields) > 0:
                        confi.save(update_fields=update_fields)
            else:
                if data['employee_number']:
                    Confidentiality.objects.filter(user_id=user.id).update(
                        is_new_employee = False,
                        employee_number = data['employee_number']
                    )
        else:
            if data['employee_number']:
                Confidentiality.objects.create(
                    user_id=user.id,
                    is_new_employee = False,
                    employee_number=data['employee_number'],
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )

        return User.objects.get(id=user.id)

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

    if data['student_number']:
        sn = Profile.objects.filter(student_number=data['student_number']).exclude(user__username=data['username'])
        if sn.exists():
            return True

    if data['employee_number']:
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

def check_two_querysets_equal(qs1, qs2):
    ''' Helper funtion: To check whether two querysets are equal or not '''
    if len(qs1) != len(qs2):
        return False

    d = dict()
    for qs in qs1:
        item = qs.name.lower()
        if item in d.keys(): d[item] += 1
        else: d[item] = 1

    for qs in qs2:
        item = qs.name.lower()
        if item in d.keys(): d[item] += 1
        else: d[item] = 1

    for k, v in d.items():
        if v != 2: return False
    return True


def update_student_profile_degrees_trainings(profile, old_degrees, old_trainings, data):
    ''' Update degrees and trainings of a student profile '''

    if check_two_querysets_equal( old_degrees, data.get('degrees') ) == False:
        profile.degrees.remove( *old_degrees ) # Remove current degrees
        new_degrees = list( data.get('degrees') )
        profile.degrees.add( *list(new_degrees) ) # Add new degrees

    if check_two_querysets_equal( old_trainings, data.get('trainings') ) == False:
        profile.trainings.remove( *old_trainings ) # Remove current trainings
        new_trainings = list( data.get('trainings') )
        profile.trainings.add( *list(new_trainings) ) # Add new trainings

    return True if profile.degrees and profile.trainings else False


def update_user_profile_roles(profile, old_roles, data):
    ''' Update roles of a user '''

    if check_two_querysets_equal( old_roles, data.get('roles') ) == False:
        profile.roles.remove( *old_roles ) # Remove current roles
        new_roles = list( data.get('roles') )
        profile.roles.add( *new_roles )  # Add new roles

    return True if profile.roles else False


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


def get_applicant_status_program(applicant):
    ''' Get current status and a program of an applicant '''

    programs = get_programs()
    valid_programs = [ program.slug for program in programs if program.slug.find('master-of') > -1 or program.slug.find('doctor-of-philosophy') > -1 ]

    highlight = ''
    current_status = ''

    if applicant.profile.faculty and applicant.profile.status and applicant.profile.program:
        if applicant.profile.status.slug == utils.UNDERGRADUATE:
            highlight = 'undergraduate'
            current_status = 'BSc'

        elif applicant.profile.status.slug == utils.MASTER:
            current_status = 'MSc'
            if applicant.profile.faculty.slug == utils.LFS_FACULTY and applicant.profile.program.slug in valid_programs:
                highlight = 'lfs-graduate'

        elif applicant.profile.status.slug == utils.PHD:
            current_status = 'PhD'
            if applicant.profile.faculty.slug == utils.LFS_FACULTY and applicant.profile.program.slug in valid_programs:
                highlight = 'lfs-graduate'

        if len(current_status) > 0 and applicant.profile.student_year:
            current_status += '.' + applicant.profile.student_year

    return {
        'highlight': highlight,
        'current_status': current_status
    }


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


def delete_user_resume(user_id):
    ''' Delete user's resume '''

    user = get_user(user_id)
    if has_user_resume_created(user) and bool(user.resume.uploaded):
        user.resume.delete()
        if not Resume.objects.filter(user__id=user.id).exists():
            dirpath = os.path.join( settings.MEDIA_ROOT, 'users', user.username, 'resume' )

            # Remove a resume directory
            if os.path.exists(dirpath) and os.path.isdir(dirpath) and len(os.listdir(dirpath)) == 0:
                os.rmdir(dirpath)

            if not os.path.exists(dirpath):
                return { 'status': 'success' }
            else:
                return { 'status': 'warning' }
        return {
            'status': 'error',
            'message': "The file of this resume hasn't been deleted"
        }
    return {
            'status': 'success',
            'message': 'No resume found'
        }


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


def delete_user_avatar(user_id):
    ''' Delete user's avatar '''

    user = get_user(user_id)
    if has_user_avatar_created(user) and bool(user.avatar.uploaded):
        user.avatar.delete()
        if not Avatar.objects.filter(user__id=user.id).exists():
            dirpath = os.path.join( settings.MEDIA_ROOT, 'users', user.username, 'avatar' )

            # Remove a avatar directory
            if os.path.exists(dirpath) and os.path.isdir(dirpath) and len(os.listdir(dirpath)) == 0:
                os.rmdir(dirpath)

            if not os.path.exists(dirpath):
                return { 'status': 'success' }
            else:
                return { 'status': 'warning', 'user': user.get_full_name() }
        return {
            'status': 'error',
            'message': "The file of this avatar hasn't been deleted"
        }
    return {
            'status': 'success',
            'message': 'No avatar found'
        }


# Confidentiality


def create_confidentiality(user):
    return Confidentiality.objects.create(
        user_id = user.id,
        created_at = datetime.now(),
        updated_at = datetime.now()
    )


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
                    if os.path.exists(dirpath) and os.path.isdir(dirpath) and len(os.listdir(dirpath)) == 0:
                        os.rmdir(dirpath)
                        return True
                else:
                    return False
            except OSError:
                print('SIN: OSError')
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
                    if os.path.exists(dirpath) and os.path.isdir(dirpath) and len(os.listdir(dirpath)) == 0:
                        os.rmdir(dirpath)
                        return True
                else:
                    return False
            except OSError:
                print('Study Permit: OSError')
        else:
            return False
    return True


# end Confidentiality


def create_expiry_date(year, month, day):
    if not bool(year) or not bool(month) or not bool(day): return False
    return datetime( int(year), int(month), int(day) )


def match_active_trainings(profile):
    ''' To check a user has required trainings clicked '''
    profile_trainings = [ tr.name for tr in profile.trainings.all() ]
    for tr in get_active_trainings():
        if tr.name not in profile_trainings:
            return False
    return True


def can_apply(user):
    ''' Check whether students can apply or not '''

    fields = [
        'status', 'student_year', 'has_graduated', 'graduation_date', 'faculty', 'program', 'degree_details',
        'training_details', 'lfs_ta_training', 'lfs_ta_training_details', 'ta_experience', 'ta_experience_details', 'qualifications'
    ]
    gta_fields = ['total_academic_years', 'total_terms', 'total_ta_hours']

    profile = has_user_profile_created(user)
    if profile and has_user_resume_created(user):
        if not is_undergraduate(user):
            fields += gta_fields

        for field in fields:
            value = getattr(user.profile, field)
            if value == None:
                return False

        if profile.degrees.count() > 0 and \
            profile.trainings.count() > 0 and match_active_trainings(profile) and \
            adminApi.trim(adminApi.strip_html_tags(profile.degree_details)) and \
            adminApi.trim(adminApi.strip_html_tags(profile.training_details)) and \
            adminApi.trim(adminApi.strip_html_tags(profile.lfs_ta_training_details)) and \
            adminApi.trim(adminApi.strip_html_tags(profile.ta_experience_details)) and \
            adminApi.trim(adminApi.strip_html_tags(profile.qualifications)):
            return True

    return False


def get_gta_flag(user):
    undergrad = is_undergraduate(user)
    profile = has_user_profile_created(user)
    if not undergrad and profile:
        years = profile.total_academic_years
        terms = profile.total_terms
        ta_hours = profile.total_ta_hours
        if years != None and terms != None and ta_hours != None:
            if terms < 5:
                return 'GTA 2'
            if years >= 2 and terms >= 5 and ta_hours >= 192:
                return 'GTA 1'
            return 'Review'
    return None


def get_preferred_candidate(user, year):
    profile = has_user_profile_created(user)
    if profile and is_lfs_student(user) and not is_undergraduate(user) and adminApi.get_accepted_hours_from_previous_year(user, year) > 0:
        if is_master(user) and (1 <= int(profile.student_year) <= 2):
            return True
        if is_phd(user) and (1 <= int(profile.student_year) <= 5):
            return True
    return False


def confirm_profile_reminder(user, session):
   if not user or not session:
       return False
   return ProfileReminder.objects.filter(user=user, session=session).exists()


def valid_sin_international(user):
    confi = has_user_confidentiality_created(user)
    if confi and confi.nationality == utils.NATIONALITY['domestic']:
        return True

    return Confidentiality.objects.filter(
        user_id=user.id,
        nationality=utils.NATIONALITY['international'],
        sin__isnull=False,
    ).exists()


def get_confidential_info_expiry_status(user):
    confi = has_user_confidentiality_created(user)

    docs = []

    # Nationality == 1: International Student
    if confi and confi.nationality == utils.NATIONALITY['international']:
        sin = {
            'doc': 'SIN',
            'date': confi.sin_expiry_date
        }

        study_permit = {
            'doc': 'Study Permit',
            'date': confi.study_permit_expiry_date
        }

        if confi.sin_expiry_date:
            if confi.sin_expiry_date < utils.TODAY:
                sin['status'] = 'Expired'
                docs.append(sin)
            elif (confi.sin_expiry_date.year == utils.THIS_YEAR) and (confi.sin_expiry_date > utils.TODAY):
                sin['status'] = 'Will expire'
                docs.append(sin)
        else:
            sin['status'] = 'Missing'
            docs.append(sin)

        if confi.study_permit_expiry_date:
            if confi.study_permit_expiry_date < utils.TODAY:
                study_permit['status'] = 'Expired'
                docs.append(study_permit)
            elif (confi.study_permit_expiry_date.year == utils.THIS_YEAR) and (confi.study_permit_expiry_date > utils.TODAY):
                study_permit['status'] = 'Will expire'
                docs.append(study_permit)
        else:
            study_permit['status'] = 'Missing'
            docs.append(study_permit)

    return docs


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
    status = Status.objects.filter(slug__icontains='undergraduate-student')
    if status.exists():
        return status.first().id
    else:
        return None


def is_lfs_student(user):
    return Profile.objects.filter(user_id=user.id, faculty__slug=utils.LFS_FACULTY).exists()

def is_undergraduate(user):
    return Profile.objects.filter(user_id=user.id, status__slug=utils.UNDERGRADUATE).exists()

def is_master(user):
    return Profile.objects.filter(user_id=user.id, status__slug=utils.MASTER).exists()

def is_phd(user):
    return Profile.objects.filter(user_id=user.id, status__slug=utils.PHD).exists()




# faculties

def get_faculties():
    ''' Get all faculties '''
    return Faculty.objects.all()

def get_faculty(faculty_id):
    ''' Get a faculty by id '''
    return get_object_or_404(Faculty, id=faculty_id)

def get_faculty_by_slug(slug):
    ''' Get a faculty by code '''
    return get_object_or_404(Faculty, slug=slug)

def delete_faculty(faculty_id):
    ''' Delete a faculty '''
    faculty = get_faculty(faculty_id)
    faculty.delete()
    return faculty if faculty else False


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

def get_active_trainings():
    ''' Get active trainings '''
    return Training.objects.filter(is_active=True)

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


def get_alertemails():
    ''' Get all alertemails '''
    return AlertEmail.objects.all()


def get_lfs_grad_or_others(user):
    other_program = get_program_by_slug('other')

    lfs_grad_or_others = ''
    if profile_exists(user) and user.profile.status and user.profile.program:
        if (is_master(user) or is_phd(user)) and is_lfs_student(user) and user.profile.program.id != other_program.id:
            lfs_grad_or_others = 'LFS GRAD'
        else:
            lfs_grad_or_others = 'OTHERS'

    return lfs_grad_or_others


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


def display_error_messages(errors):
    messages = []
    for key, value in errors.items():
        for item in value:
            messages.append(item['message'])
    return ' '.join(messages)


def password_generator():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=50))


def trim(s):
    return None if not s or s.isspace() else s.strip()
