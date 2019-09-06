import os
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User
from users.models import *

from datetime import datetime

# to be removed
from django.utils.crypto import get_random_string




# for auth

def is_valid_user(user):
    ''' Check if an user is valid or not '''
    if user.is_anonymous or not user.is_authenticated:
        return False
    return True

def is_admin(user):
    ''' Check if an user is an Admin or Superadmin '''
    if 'Admin' in user.roles or 'Superadmin' in user.roles:
        return True
    return False

def loggedin_user(user):
    ''' Get a logged in user '''
    if not is_valid_user(user): PermissionDenied

    roles = []
    for role in user.profile.roles.all():
        if role.name == Role.STUDENT:
            roles.append(Role.STUDENT)
        elif role.name == Role.INSTRUCTOR:
            roles.append(Role.INSTRUCTOR)
        elif role.name == Role.HR:
            roles.append(Role.HR)
        elif role.name == Role.ADMIN:
            roles.append(Role.ADMIN)
        elif role.name == Role.SUPERADMIN:
            roles.append(Role.SUPERADMIN)
    user.roles = roles
    return user


# Users
def get_user(user_id):
    """ Get a user by id """
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return None

def get_user_by_username(username):
    """ Get a user by username """
    return get_object_or_404(User, username=username)
    """try:
        return User.objects.get(username=username)
    except User.DoesNotExist:
        return None """

def get_users():
    """ Get all users """
    return User.objects.all().order_by('id')

def create_user(data):
    """ Create a user when receiving data from SAML """

    # TODO: Change a ubc number
    user = User.objects.create(
        first_name = data['first_name'],
        last_name = data['last_name'],
        email = data['email'],
        username = data['username'],
        password = '12'
    )
    if user:
        profile = create_profile(user)
        if profile:
            resume = create_user_resume(user)
            if resume:
                confidentiality = create_user_confidentiality(user)
                if confidentiality:
                    return user
    return False

def delete_user(user_id):
    """ Delete a user """
    try:
        user = User.objects.get(id=user_id)
        user.delete()
        return user
    except User.DoesNotExist:
        return None

def user_exists(user):
    """ Check username exists """
    if User.objects.filter(id=user.id).exists():
        return True
    return False

def profile_exists(user):
    """ Check user's profile exists """
    if Profile.objects.filter(user__id=user.id).exists():
        return True
    return False

def has_user_resume_created(user):
    try:
        return user.resume
    except Resume.DoesNotExist:
        return False


def resume_exists(user):
    """ Check user's resume exists """
    if Resume.objects.filter(user__id=user.id).exists():
        return True
    return False

def confidentiality_exists(user):
    """ Check user's confidentiality exists """
    if Confidentiality.objects.filter(user__id=user.id).exists():
        return True
    return False

def username_exists(username):
    """ Check username exists """
    if User.objects.filter(username=username).exists():
        return True
    return False

def profile_exists_by_username(username):
    """ Check user's profile exists """
    if Profile.objects.filter(user__username=username).exists():
        return True
    return False

def resume_exists_by_username(username):
    """ Check user's resume exists """
    if Resume.objects.filter(user__username=username).exists():
        return True
    return False

def confidentiality_exists_by_username(username):
    """ Check user's confidentiality exists """
    if Confidentiality.objects.filter(user__username=username).exists():
        return True
    return False

'''
def delete_users():
    """ Delete all users """
    users = User.objects.all().delete()
    return True if users else None
'''



# Profile CRUD

def get_instructors():
    instructors = []
    for profile in Profile.objects.all():
        if profile.roles.filter(slug='instructor').exists():
            instructors.append(profile.user)
    return instructors


def update_user_profile_roles(profile, old_roles, data):
    profile.roles.remove( *old_roles )
    new_roles = list( data.get('roles') )
    profile.roles.add( *new_roles )
    return True if profile else None


#checked
def update_user_profile(profile, old_roles, old_degrees, old_trainings, data):
    """ Update roles, degrees and trainings of a user profile """
    # Remove current roles, degrees and trainings
    profile.roles.remove( *old_roles )
    profile.degrees.remove( *old_degrees )
    profile.trainings.remove( *old_trainings )

    new_roles = list( data.get('roles') )
    new_degrees = list( data.get('degrees') )
    new_trainings = list( data.get('trainings') )

    # Add new roles, degrees and trainings
    profile.roles.add( *new_roles )
    profile.degrees.add( *new_degrees )
    profile.trainings.add( *new_trainings )

    return True if profile else None

#checked
def update_student_profile_degrees_trainings(profile, old_degrees, old_trainings, data):
    """ Update degrees and trainings of a student profile """
    # Remove current degrees and trainings
    profile.degrees.remove( *old_degrees )
    profile.trainings.remove( *old_trainings )

    new_degrees = list( data.get('degrees') )
    new_trainings = list( data.get('trainings') )

    # Add new degrees and trainings
    profile.degrees.add( *list(new_degrees) )
    profile.trainings.add( *list(new_trainings) )

    return True if profile else None


def get_profiles():
    return Profile.objects.all().order_by('id')

def create_profile(user, data):

    # TODO: modify ubc_number coming from SAML's data
    ubc_number = data.get('ubc_number', None)
    ubc_number = get_random_string(length=9)

    preferred_name = data.get('preferred_name')
    roles = data.getlist('roles')
    
    profile = Profile.objects.create(user_id=user.id, ubc_number=ubc_number, preferred_name=preferred_name)
    profile.roles.add( *roles )
    return True if profile else None

def update_profile(user_id, data):
    profile = get_profile(user_id)
    if data.get('role'):
        profile.role = get_role(data['role'])

    if data.get('status'):
        profile.status = get_status(data['status'])

    if data.get('program'):
        profile.program = get_program(data['program'])

    if data.getlist('degrees'):
        profile.degrees.add( *data.getlist('degrees') )

    if data.getlist('trainings'):
        profile.trainings.add( *data.getlist('trainings') )

    profile.updated_at = datetime.now()
    profile.save(update_fields=['role', 'status', 'program', 'updated_at'])

    return True

def get_user_roles(user):
    if hasattr(user.profile, 'roles'):
        return [ role.name for role in user.profile.roles.all() ]
    else:
        return  None

"""
def file_exists(user, folder, file):
    exists = False
    dir_path = os.path.join(settings.MEDIA_ROOT, 'users', str(user.username), folder)
    for root, dirs, files in os.walk(dir_path):
        for filename in files:
            if filename == file:
                exists = True
    return exists
"""

def get_instructors():
    instructors = []
    for user in get_users():
        if user.profile.roles.filter(name='Instructor').exists():
            instructors.append(user)
    return instructors


def get_students():
    students = []
    for user in get_users():
        if user.profile.roles.filter(name='Student').exists():
            students.append(user)
    return students




def delete_existing_file(user, folder, file):
    """ Delete an existing file """
    deleted = False
    dir_path = os.path.join(settings.MEDIA_ROOT, 'users', str(user.username), folder)
    for root, dirs, files in os.walk(dir_path):
        for filename in files:
            if filename == file:
                os.remove(os.path.join(dir_path, filename))
                deleted = True
    return deleted

def delete_user_resume(username):
    user = get_user_by_username(username)
    file = os.path.basename(user.resume.file.name)
    user.resume.file = None
    user.resume.created_at = None
    user.resume.save(update_fields=['file', 'created_at'])

    # Delete an existing file
    deleted = delete_existing_file(user, 'resume', file)
    return True if user.resume and deleted else None


def delete_user_sin(username):
    user = get_user_by_username(username)
    file = os.path.basename(user.confidentiality.sin.name)
    user.confidentiality.sin = None
    user.confidentiality.sin_expiry_date = None
    user.confidentiality.save(update_fields=['sin', 'sin_expiry_date'])

    # Delete an existing file
    deleted = delete_existing_file(user, 'sin', file)
    return True if user.confidentiality and deleted else None


def delete_user_study_permit(username):
    user = get_user_by_username(username)
    file = os.path.basename(user.confidentiality.study_permit.name)
    user.confidentiality.study_permit = None
    user.confidentiality.study_permit_expiry_date = None
    user.confidentiality.save(update_fields=['study_permit', 'study_permit_expiry_date'])

    # Delete an existing file
    deleted = delete_existing_file(user, 'study_permit', file)
    return True if user.confidentiality and deleted else None


def create_user_resume(user):
    resume = Resume.objects.create(user_id=user.id)
    return True if resume else None


def create_user_confidentiality(user):
    confidentiality = Confidentiality.objects.create(user_id=user.id)
    return True if confidentiality else None


# Role
def get_roles():
    """ Get all roles """

    return Role.objects.all()

def get_role(role_id):
    """ Get a role """

    try:
        return Role.objects.get(id=role_id)
    except Role.DoesNotExist:
        return None

def delete_roles():
    """ Delete all roles """

    roles = Role.objects.all().delete()
    return True if roles else None


# Confidentiality

def has_user_confidentiality_created(user):
    try:
        return user.confidentiality
    except Confidentiality.DoesNotExist:
        return None



def get_confidentialities():
    return Confidentiality.objects.all()

def get_confidentiality(user):
    try:
        return Confidentiality.objects.get(user_id=user.id)
    except Confidentiality.DoesNotExist:
        return None

def create_confidentiality(user):
    confidentiality = Confidentiality.objects.create(user_id=user.id)
    return True if confidentiality else None


# Training

def get_trainings():
    return Training.objects.all()

def get_training(slug):
    try:
        return Training.objects.get(slug=slug)
    except Training.DoesNotExist:
        return None

def delete_training(training_id):
    try:
        training = Training.objects.get(id=training_id)
        training.delete()
        return training
    except Training.DoesNotExist:
        return None


# Program

def get_programs():
    return Program.objects.all()

def get_program(slug):
    try:
        return Program.objects.get(slug=slug)
    except Program.DoesNotExist:
        return None

def delete_program(program_id):
    try:
        program = Program.objects.get(id=program_id)
        program.delete()
        return program
    except Program.DoesNotExist:
        return None


# Degree

def get_degrees():
    return Degree.objects.all()

def get_degree(slug):
    try:
        return Degree.objects.get(slug=slug)
    except Degree.DoesNotExist:
        return None

def delete_degree(degree_id):
    try:
        degree = Degree.objects.get(id=degree_id)
        degree.delete()
        return degree
    except Degree.DoesNotExist:
        return None


# Role

def get_roles():
    return Role.objects.all()

def get_role(slug):
    try:
        return Role.objects.get(slug=slug)
    except Role.DoesNotExist:
        return None

def delete_role(role_id):
    try:
        role = Role.objects.get(id=role_id)
        role.delete()
        return role
    except Role.DoesNotExist:
        return None


# Status

def get_statuses():
    return Status.objects.all()

def get_status(slug):
    try:
        return Status.objects.get(slug=slug)
    except Status.DoesNotExist:
        return None

def delete_status(status_id):
    try:
        status = Status.objects.get(id=status_id)
        status.delete()
        return status
    except Status.DoesNotExist:
        return None



# to be removed


def get_profile(user):
    try:
        return Profile.objects.get(user_id=user.id)
    except Profile.DoesNotExist:
        return None
