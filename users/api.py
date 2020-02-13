import os
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.db.models import Q

import shutil
from PIL import Image

from users.models import *
from users.forms import *
from administrators.forms import ROLES
from datetime import datetime, date, timedelta


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
    return roles

def loggedin_user(user):
    ''' Get a logged in user '''
    if not is_valid_user(user): PermissionDenied

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
    user.roles = roles

    return user


# User


def get_user(data, by=None):
    ''' Get a user '''
    if by == 'username':
        return get_object_or_404(User, username=data)
    return get_object_or_404(User, id=data)

def get_users(option=None):
    ''' Get all users '''
    if option == 'destroy':
        target_date = date.today() - timedelta(days=3*365)
        return User.objects.filter( Q(last_login__lt=target_date) & Q(profile__is_trimmed=False) ), target_date

    return User.objects.all().order_by('id')

def get_users_by_role(role):
    ''' Get users by role '''
    return User.objects.filter(profile__roles__name=role).order_by('last_name')

def user_exists(username):
    ''' Check user exists '''
    if User.objects.filter(username=username).exists():
        return User.objects.get(username=username)
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
        password=make_password(settings.USER_PASSWORD)
    )

    if user:
        confidentiality = False
        if employee_number is not None:
            confidentiality = Confidentiality.objects.create(
                user_id=user.id,
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

def delete_user(user_id):
    ''' Delete a user '''
    user = get_user(user_id)
    user.delete()
    return user


# end user


# Profile

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


def create_profile(user, data):
    ''' Create an user's profile '''
    student_number = None
    if data['student_number']:
        student_number = data['student_number']

    profile = Profile.objects.create(user_id=user.id, student_number=student_number, preferred_name=data['preferred_name'], is_trimmed=False)
    profile.roles.add( *data['roles'] )

    return profile if profile else False

def has_user_profile_created(user):
    ''' Check an user has a profile '''
    try:
        return user.profile
    except Profile.DoesNotExist:
        return None

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

def profile_exists_by_username(username):
    ''' Check user's profile exists '''
    profile = Profile.objects.filter(user__username=username)
    if profile.exists(): return profile
    return False

def profile_exists(user):
    """ Check user's profile exists """
    if Profile.objects.filter(user__id=user.id).exists():
        return True
    return False


def trim_profile(user):
    ''' Remove user's profile except student_number '''
    student_number = user.profile.student_number
    user.profile.delete()
    profile = Profile.objects.create(user_id=user.id, student_number=student_number, is_trimmed=True)
    return profile if profile else False


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
            os.rmdir( os.path.join( settings.MEDIA_ROOT, 'users', user.username, 'resume' ) )
            return True
        else:
            return False
    return True


def resume_exists(user):
    """ Check user's resume exists """
    if Resume.objects.filter(user__id=user.id).exists():
        return True
    return False


# end resume


# Confidentiality

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
            user.sin_decrypt_image = decrypt_image(user.username, user.confidentiality.sin, 'sin')
        else:
            user.sin_decrypt_image = None

        if bool(user.confidentiality.study_permit) and 'study_permit' in array:
            user.study_permit_decrypt_image = decrypt_image(user.username, user.confidentiality.study_permit, 'study_permit')
        else:
            user.study_permit_decrypt_image = None

    return user

def confidentiality_exists(user):
    """ Check user's confidentiality exists """
    if Confidentiality.objects.filter(user__id=user.id).exists():
        return True
    return False

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
                    os.rmdir( os.path.join(settings.MEDIA_ROOT, 'users', username, 'sin') )
                    return True
                else:
                    return False
            except OSError:
                print("OSError")
                return False
    return True


def delete_user_study_permit(username, option=None):
    ''' Delete user's study permit '''
    user = get_user(username, 'username')

    if has_user_confidentiality_created(user) and bool(user.confidentiality.study_permit):
        user.confidentiality.study_permit.close()
        #print('user.confidentiality.study_permit.closed ', user.confidentiality.study_permit.closed)
        if user.confidentiality.study_permit.closed:
            try:
                user.confidentiality.study_permit.delete(save=False)
                deleted = None
                if option == '1':
                    deleted = Confidentiality.objects.filter(user_id=user.id).update(study_permit=None, study_permit_expiry_date=None)
                else:
                    deleted = Confidentiality.objects.filter(user_id=user.id).update(study_permit=None)

                if deleted and not bool(user.confidentiality.study_permit):
                    os.rmdir( os.path.join( settings.MEDIA_ROOT, 'users', username, 'study_permit' ) )
                    return True
                else:
                    return False
            except OSError:
                print("OSError")
                return False
    return True


def add_personal_data_form(user):
    ''' Add personal data form of an user '''
    if has_user_confidentiality_created(user) and bool(user.confidentiality.personal_data_form):
        user.personal_data_form_filename = os.path.basename(user.confidentiality.personal_data_form.name)
    else:
        user.personal_data_form_filename = None
    return user


def delete_personal_data_form(data):
    ''' Delete user's personal data form '''
    user = get_user(data, 'username')

    if has_user_confidentiality_created(user) and bool(user.confidentiality.personal_data_form):
        user.confidentiality.personal_data_form.delete(save=False)
        deleted = Confidentiality.objects.filter(user_id=user.id).update(personal_data_form=None)
        print('delete_personal_data_form', deleted)
        if deleted and not bool(user.confidentiality.personal_data_form):
            os.rmdir( os.path.join( settings.MEDIA_ROOT, 'users', user.username, 'personal_data_form' ) )
            return True
        else:
            return False
    return True

# end Confidentiality


def destroy_profile_resume_confidentiality(user_id):
    ''' Trim user's profile, resume and confidentiality '''
    user = get_user(user_id)

    sin = delete_user_sin(user.username)
    study_permit = delete_user_study_permit(user.username)
    user.confidentiality.delete()

    resume = delete_user_resume(user)
    profile = trim_profile(user)
    print("sin", sin)
    print("study_permit", study_permit)
    print("resume", resume)
    print("profile", profile)
    return True if user and resume and sin and study_permit and profile else False


def create_expiry_date(year, month, day):
    if not bool(year) or not bool(month) or not bool(day): return False
    return datetime( int(year), int(month), int(day) )


# Confidentiality


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

def get_error_messages(errors):
    messages = ''
    for key in errors.keys():
        value = errors[key]
        messages += key.replace('_', ' ').upper() + ': ' + value[0]['message'] + ' '
    return messages.strip()
