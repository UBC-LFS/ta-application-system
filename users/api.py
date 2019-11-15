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
def get_user(input, by=None):
    ''' Get a user '''
    if by == 'username': return get_object_or_404(User, username=input)
    return get_object_or_404(User, id=input)

def user_exists(username):
    ''' Check user exists '''
    if User.objects.filter(username=username).exists(): return User.objects.get(username=username)
    return None


# Resume

def add_resume(user):
    ''' Add resume of an user '''
    if has_user_resume_created(user) and bool(user.resume.uploaded):
        user.resume_filename = os.path.basename(user.resume.uploaded.name)
    else:
        user.resume_filename = None
    return user


def delete_user_resume(input):
    ''' Delete user's resume '''
    user = get_user(input, 'username')

    if has_user_resume_created(user) and bool(user.resume.uploaded):
        user.resume.uploaded.delete()
        deleted = user.resume.delete()
        return True if deleted and not bool(user.resume.uploaded) else False
    return False


def user_has_role(user, role):
    if user.profile.roles.filter(name=role).exists(): return True
    return False


# Confidentiality

def add_confidentiality(user):
    ''' Add confidentiality of an user '''
    if has_user_confidentiality_created(user):

        if bool(user.confidentiality.sin):
            user.sin_decrypt_image = decrypt_image(user.username, user.confidentiality.sin, 'sin')
        else:
            user.sin_decrypt_image = None

        if bool(user.confidentiality.study_permit):
            user.study_permit_decrypt_image = decrypt_image(user.username, user.confidentiality.study_permit, 'study_permit')
        else:
            user.study_permit_decrypt_image = None

    return user


def add_confidentiality_all(user):
    ''' Add all confidentiality data of an user '''
    if has_user_confidentiality_created(user):

        if bool(user.confidentiality.sin):
            user.sin_decrypt_image = decrypt_image(user.username, user.confidentiality.sin, 'sin')
        else:
            user.sin_decrypt_image = None

        if bool(user.confidentiality.study_permit):
            user.study_permit_decrypt_image = decrypt_image(user.username, user.confidentiality.study_permit, 'study_permit')
        else:
            user.study_permit_decrypt_image = None

        if bool(user.confidentiality.union_correspondence):
            user.union_correspondence_filename = os.path.basename(user.confidentiality.union_correspondence.name)
        else:
            user.union_correspondence_filename = None

        if bool(user.confidentiality.compression_agreement):
            user.compression_agreement_filename = os.path.basename(user.confidentiality.compression_agreement.name)
        else:
            user.compression_agreement_filename = None

    return user


























# -----------------------------------------

def get_user_with_confidentiality(username, role=None):
    ''' Get a user with resume, sin and study permit by username '''

    user = get_user(username, 'username')

    if role == None and has_user_resume_created(user):
        if bool(user.resume.uploaded):
            user.resume_filename = os.path.basename(user.resume.uploaded.name)
        else:
            user.resume_filename = None

    if has_user_confidentiality_created(user):

        if bool(user.confidentiality.sin):
            user.sin_decrypt_image = decrypt_image(user.username, user.confidentiality.sin, 'sin')
        else:
            user.sin_decrypt_image = None

        if bool(user.confidentiality.study_permit):
            user.study_permit_decrypt_image = decrypt_image(user.username, user.confidentiality.study_permit, 'study_permit')
        else:
            user.study_permit_decrypt_image = None

        if role == 'administrator':
            if bool(user.confidentiality.union_correspondence):
                user.union_correspondence_filename = os.path.basename(user.confidentiality.union_correspondence.name)
            else:
                user.union_correspondence_filename = None

            if bool(user.confidentiality.compression_agreement):
                user.compression_agreement_filename = os.path.basename(user.confidentiality.compression_agreement.name)
            else:
                user.compression_agreement_filename = None

    return user




def get_user_by_username_with_statistics(username):
    ''' '''
    user = get_user(username, 'username')

    count = 0
    for job in user.job_set.all():
        count +=  job.application_set.count()

    user.total_applicants = count
    return user

"""
def get_users_with_data():
    ''' Get all users with resume, sin, and study permit '''
    users = User.objects.all()

    for user in users:
        if has_user_resume_created(user) and bool(user.resume.uploaded):
            user.resume_filename = os.path.basename(user.resume.uploaded.name)
        else:
            user.resume_filename = None

        if has_user_confidentiality_created(user) and bool(user.confidentiality.sin):
            user.sin_decrypt_image = decrypt_image(user.username, user.confidentiality.sin, 'sin')
        else:
            user.sin_decrypt_image = None

        if has_user_confidentiality_created(user) and bool(user.confidentiality.study_permit):
            user.study_permit_decrypt_image = decrypt_image(user.username, user.confidentiality.study_permit, 'study_permit')
        else:
            user.study_permit_decrypt_image = None

    return users
"""


def get_users(option=None):
    ''' Get all users '''
    if option == 'trim':
        target_date = date.today() - timedelta(days=3*365)
        return User.objects.filter( Q(last_login__lt=target_date) & Q(profile__is_trimmed=False) ), target_date

    return User.objects.all().order_by('id')



def create_user(data):
    ''' Create a user when receiving data from SAML '''
    user = User.objects.create(
        first_name = data['first_name'],
        last_name = data['last_name'],
        email = data['email'],
        username = data['username'],
        password = make_password(settings.USER_PASSWORD)
    )

    if user:
        user_profile_form = UserProfileForm({
            'student_number': None,
            'preferred_name': None,
            'roles': [ ROLES['Student'] ]
        })

        if user_profile_form.is_valid():
            profile = create_profile(user, user_profile_form.cleaned_data)
            if profile: return user

    return False

def create_profile(user, data):
    ''' Create an user's profile '''

    # TODO: modify student_number coming from SAML's data
    #student_number = data['student_number']
    student_number = None
    if data['student_number']:
        student_number = data['student_number']
    else:
        student_number = get_random_string(length=8)

    profile = Profile.objects.create(user_id=user.id, student_number=student_number, preferred_name=data['preferred_name'], is_trimmed=False)
    profile.roles.add( *data['roles'] )

    return profile if profile else False


def delete_user(user_id):
    ''' Delete a user '''
    user = get_user(user_id)
    user.delete()
    return user





def has_user_profile_created(user):
    ''' Check an user has a profile '''
    try:
        return user.profile
    except Profile.DoesNotExist:
        return None


def has_user_resume_created(user):
    ''' Check an user has a resume '''
    try:
        return user.resume
    except Resume.DoesNotExist:
        return None


def has_user_confidentiality_created(user):
    ''' Check an user has a confidentiality '''
    try:
        return user.confidentiality
    except Confidentiality.DoesNotExist:
        return None





def profile_exists_by_username(username):
    ''' Check user's profile exists '''
    profile = Profile.objects.filter(user__username=username)
    if profile.exists(): return profile
    return False



# -------------------------------------



# for testing



def profile_exists(user):
    """ Check user's profile exists """
    if Profile.objects.filter(user__id=user.id).exists():
        return True
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



# Profile

def get_users_by_role(role):
    ''' Get users by role '''
    return User.objects.filter(profile__roles__name=role).order_by('last_name')

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


def get_profiles():
    return Profile.objects.all().order_by('id')



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


def trim_profile(user):
    user.profile.preferred_name = None

    user.profile.qualifications = None
    user.profile.prior_employment = None
    user.profile.special_considerations = None

    user.profile.status = None
    user.profile.program = None
    user.profile.program_others = None
    user.profile.graduation_date = None

    user.profile.degrees = None
    user.profile.degree_details = None
    user.profile.trainings = None
    user.profile.training_details = None

    user.profile.lfs_ta_training = None
    user.profile.lfs_ta_training_details = None

    user.profile.ta_experience = None
    user.profile.ta_experience_details = None

    user.profile.is_trimmed = True
    user.profile.created_at = None
    user.profile.updated_at = None

    user.profile.save(update_fields=[
        'preferred_name', 'qualifications','prior_employment', 'special_considerations',
        'status', 'program', 'program_others', 'graduation_date',
        'degrees', 'degree_details', 'trainings', 'training_details',
        'lfs_ta_training', 'lfs_ta_training_details', 'ta_experience', 'ta_experience_details',
        'is_trimmed', 'created_at', 'updated_at'
    ])
    return user.profile if user.profile else None
"""


def trim_profile(user):
    ''' Remove user's profile except student_number '''
    student_number = user.profile.student_number
    user.profile.delete()
    profile = Profile.objects.create(user_id=user.id, student_number=student_number, is_trimmed=True)
    return profile if profile else False

def trim_profile_resume_confidentiality(user_id):
    ''' Trim user's profile, resume and confidentiality '''
    user = get_user(user_id)

    sin = delete_user_sin(user.username)
    study_permit = delete_user_study_permit(user.username)
    user.confidentiality.delete()

    resume = delete_user_resume(user)
    profile = trim_profile(user)

    return True if user and resume and sin and study_permit and profile else False




def delete_user_sin(username):
    ''' Delete user's SIN '''
    user = get_user(username, 'username')

    if has_user_confidentiality_created(user) and bool(user.confidentiality.sin):
        user.confidentiality.sin.close()
        print('user.confidentiality.sin.closed ', user.confidentiality.sin.closed)
        if user.confidentiality.sin.closed:
            try:
                user.confidentiality.sin.delete(save=False)
                deleted = Confidentiality.objects.filter(user_id=user.id).update(sin=None, sin_expiry_date=None)
                return True if deleted and not bool(user.confidentiality.sin) else False
            except OSError:
                return False
    return False


def delete_user_study_permit(user):
    ''' Delete user's study permit '''
    if not isinstance(user, User): user = get_user(username, 'username')

    if has_user_confidentiality_created(user) and bool(user.confidentiality.study_permit):
        user.confidentiality.study_permit.close()
        print('user.confidentiality.study_permit.closed ', user.confidentiality.study_permit.closed)
        if user.confidentiality.study_permit.closed:
            try:
                user.confidentiality.study_permit.delete(save=False)
                deleted = Confidentiality.objects.filter(user_id=user.id).update(study_permit=None, study_permit_expiry_date=None)
                return True if deleted and not bool(user.confidentiality.study_permit) else False
            except OSError:
                return False
    return False

def delete_union_correspondence(username):
    ''' Delete union_correspondence '''
    user = get_user(username, 'username')

    if has_user_confidentiality_created(user) and bool(user.confidentiality.union_correspondence):
        user.confidentiality.union_correspondence.close()
        if user.confidentiality.union_correspondence.closed:

            try:
                user.confidentiality.union_correspondence.delete(save=False)
                deleted = Confidentiality.objects.filter(user_id=user.id).update(union_correspondence=None)
                return True if deleted and not bool(user.confidentiality.union_correspondence) else False
            except OSError:
                return False
    return False

def delete_compression_agreement(username):
    ''' Delete compression_agreement '''
    user = get_user(username, 'username')

    if has_user_confidentiality_created(user) and bool(user.confidentiality.compression_agreement):
        user.confidentiality.compression_agreement.close()
        if user.confidentiality.compression_agreement.closed:

            try:
                user.confidentiality.compression_agreement.delete(save=False)
                deleted = Confidentiality.objects.filter(user_id=user.id).update(compression_agreement=None)
                return True if deleted and not bool(user.confidentiality.compression_agreement) else False
            except OSError:
                return False
    return False


def create_user_resume(user):
    resume = Resume.objects.create(user_id=user.id)
    return True if resume else None



def create_expiry_date(year, month, day):
    print('create_expiry_date ', year, month, day, bool(year))
    if not bool(year) or not bool(month) or not bool(day): return False
    return datetime( int(year), int(month), int(day) )


# Confidentiality




def create_user_confidentiality(user):
    confidentiality = Confidentiality.objects.create(user_id=user.id)
    return True if confidentiality else None

def create_confidentiality(user):
    confidentiality = Confidentiality.objects.create(user_id=user.id)
    return True if confidentiality else None



def get_confidentialities():
    return Confidentiality.objects.all()

def get_confidentiality(user):
    try:
        return Confidentiality.objects.get(user_id=user.id)
    except Confidentiality.DoesNotExist:
        return None




def updated_confidentiality(user, post, files, data):
    ''' Update user's confidentiality '''
    print('updated_confidentiality-----------')
    update_fields = []
    sin_expiry_date = create_expiry_date(post['sin_expiry_date_year'], post['sin_expiry_date_month'], post['sin_expiry_date_day'])
    study_permit_expiry_date = create_expiry_date(post['study_permit_expiry_date_year'], post['study_permit_expiry_date_month'], post['study_permit_expiry_date_day'])

    print(data['is_international'])
    print(data['employee_number'])
    print(data['sin_expiry_date'])
    print(data['study_permit_expiry_date'])

    if data['is_international'] and data['is_international'] != user.confidentiality.is_international:
        user.confidentiality.is_international = data['is_international']
        update_fields.append('is_international')

    if data['employee_number'] and data['employee_number'] != user.confidentiality.employee_number:
        user.confidentiality.employee_number = data['employee_number']
        update_fields.append('employee_number')

    print('user.confidentiality.sin_expiry_date ', user.confidentiality.sin_expiry_date)
    print(data['sin_expiry_date'] != user.confidentiality.sin_expiry_date)
    if data['sin_expiry_date'] and data['sin_expiry_date'] != user.confidentiality.sin_expiry_date:
        user.confidentiality.sin_expiry_date = data['sin_expiry_date']
        update_fields.append('sin_expiry_date')

    print('user.confidentiality.study_permit_expiry_date ', user.confidentiality.study_permit_expiry_date)
    print(data['study_permit_expiry_date'] != user.confidentiality.study_permit_expiry_date)
    if data['study_permit_expiry_date'] and data['study_permit_expiry_date'] != user.confidentiality.study_permit_expiry_date:
        user.confidentiality.study_permit_expiry_date = data['study_permit_expiry_date']
        update_fields.append('study_permit_expiry_date')

    if data['sin']:
            user.confidentiality.sin = data['sin']
            update_fields.append('sin')

    if data['study_permit']:
        user.confidentiality.study_permit = data['study_permit']
        update_fields.append('study_permit')


    print('update_fields 1 ', update_fields)

    if len(update_fields) > 0:
        if not data['is_international']:
            user.confidentiality.sin_expiry_date = None
            if 'sin_expiry_date' not in update_fields:
                update_fields.append('sin_expiry_date')

            user.confidentiality.study_permit_expiry_date = None
            if 'study_permit_expiry_date' not in update_fields:
                update_fields.append('study_permit_expiry_date')

        print('update_fields 2 ', update_fields)
        user.confidentiality.save(update_fields=update_fields)

    return True






# ----- Roles -----

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


"""
def delete_roles():
    roles = Role.objects.all().delete()
    return True if roles else None
"""



# ----- Statuses -----

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



# ----- programs -----

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


# ----- Degrees -----

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


# ----- trainings -----

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





# to be removed --------------


def get_profile(user):
    try:
        return Profile.objects.get(user_id=user.id)
    except Profile.DoesNotExist:
        return None


"""
def delete_existing_file(user, folder, file):
    ''' Delete an existing file '''
    deleted = False

    for root, dirs, files in os.walk(dir_path):
        for filename in files:
            if filename == file and os.path.isfile( os.path.join(dir_path, filename) ):

                os.remove( os.path.join(dir_path, filename) )
                os.rmdir(dir_path)

                #print( decrypted_file )
                #print( 'decrypted_file ', os.path.join(dir_path, decrypted_file['filename']) )
                #print( type(decrypted_file['filename']) )

                #print( filename )
                #os.remove(os.path.join(dir_path, filename))

                deleted = True

    return deleted
"""
