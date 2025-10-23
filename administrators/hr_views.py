import os
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.views.decorators.cache import cache_control
from django.core.exceptions import SuspiciousOperation
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import datetime

from ta_app import utils
from administrators import api as adminApi
from users.forms import UserForm, UserProfileForm, UserProfileEditForm, EmployeeNumberForm, EmployeeNumberEditForm, RoleForm
from users import api as userApi


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def all_users(request):
    ''' Display all users'''
    request = userApi.has_admin_access(request)

    first_name_q = request.GET.get('first_name')
    last_name_q = request.GET.get('last_name')
    preferred_name_q = request.GET.get('preferred_name')
    cwl_q = request.GET.get('cwl')
    student_number_q = request.GET.get('student_number')
    employee_number_q = request.GET.get('employee_number')

    user_list = userApi.get_users()
    if bool(first_name_q):
        user_list = user_list.filter(first_name__icontains=first_name_q)
    if bool(last_name_q):
        user_list = user_list.filter(last_name__icontains=last_name_q)
    if bool(preferred_name_q):
        user_list = user_list.filter(profile__preferred_name__icontains=preferred_name_q)
    if bool(cwl_q):
        user_list = user_list.filter(username__icontains=cwl_q)
    if bool(student_number_q):
        user_list = user_list.filter(profile__student_number__icontains=student_number_q)
    if bool(employee_number_q):
        user_list = user_list.filter(confidentiality__employee_number__icontains=employee_number_q)


    page = request.GET.get('page', 1)
    paginator = Paginator(user_list, utils.TABLE_PAGE_SIZE)

    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)

    return render(request, 'administrators/hr/all_users.html', {
        'loggedin_user': request.user,
        'users': users,
        'total_users': len(user_list),
        'new_next': adminApi.build_new_next(request)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def create_user(request):
    ''' Create a user '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        validation = userApi.validate_post(request.POST, ['first_name', 'last_name', 'email', 'username'])
        if len(validation) > 0:
            messages.error(request, 'An error occurred while saving an User Form. {0}: This field is required.'.format( ', '.join(validation) ))
            return redirect('administrators:create_user')

        user_form = UserForm(request.POST)
        user_profile_form = UserProfileForm(request.POST)

        if user_form.is_valid() and user_profile_form.is_valid():
            user = user_form.save(commit=False)
            user.set_password( userApi.password_generator() )
            user.save()

            profile = userApi.create_profile(user, user_profile_form.cleaned_data)

            errors = []
            if not user: errors.append('An error occurred while creating an user.')
            if not profile: errors.append('An error occurred while creating an user profile.')

            if len(errors) > 0:
                messages.error(request, 'An error occurred while saving an User Form. {0}'.format( ' '.join(errors) ))
                return redirect('administrators:create_user')

            confidentiality = userApi.has_user_confidentiality_created(user)

            data = {
                'user': user.id,
                'is_new_employee': False if request.POST.get('is_new_employee') == None else True,
                'employee_number': request.POST.get('employee_number')
            }
            employee_number_form = EmployeeNumberEditForm(data, instance=confidentiality)

            if employee_number_form.is_valid() == False:
                employee_number_errors = employee_number_form.errors.get_json_data()
                messages.error(request, 'An error occurred while creating an User Form. {0}'.format(employee_number_errors))

            employee_number = employee_number_form.save(commit=False)
            employee_number.created_at = datetime.now()
            employee_number.updated_at = datetime.now()
            employee_number.save()

            if not employee_number: errors.append('An error occurred while updating an employee number.')

            if len(errors) > 0:
                messages.error(request, 'An error occurred while saving an User Form. {0}'.format( ' '.join(errors) ))
                return redirect('administrators:create_user')

            messages.success(request, 'Success! {0} {1} (CWL: {2}) created'.format(user.first_name, user.last_name, user.username))
            return redirect('administrators:all_users')

        else:
            errors = []

            user_errors = user_form.errors.get_json_data()
            profile_errors = user_profile_form.errors.get_json_data()

            if user_errors: errors.append( userApi.get_error_messages(user_errors) )
            if profile_errors: errors.append( userApi.get_error_messages(profile_errors) )

            messages.error(request, 'An error occurred while creating an User Form. {0}'.format( ' '.join(errors) ))

        return redirect('administrators:create_user')

    return render(request, 'administrators/hr/create_user.html', {
        'loggedin_user': request.user,
        'users': userApi.get_users(),
        'user_form': UserForm(),
        'user_profile_form': UserProfileForm(),
        'employee_number_form': EmployeeNumberForm()
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_user(request, username):
    ''' Edit a user '''
    request = userApi.has_admin_access(request)
    adminApi.can_req_parameters_access(request, 'user', ['next', 'p'])

    user = userApi.get_user(username, 'username')
    confidentiality = userApi.has_user_confidentiality_created(user)

    # Create a confiential information if it's None
    if confidentiality == None:
        confidentiality = userApi.create_confidentiality(user)

    if request.method == 'POST':
        # Check whether a next url is valid or not
        adminApi.can_req_parameters_access(request, 'none', ['next'], 'POST')

        validation = userApi.validate_post(request.POST, ['first_name', 'last_name', 'email', 'username'])
        if len(validation) > 0:
            messages.error(request, 'An error occurred while updating an User Edit Form. {0}: This field is required.'.format( ', '.join(validation) ))
            return HttpResponseRedirect(request.get_full_path())


        profile_roles = user.profile.roles.all()

        user_form = UserForm(request.POST, instance=user)
        user_profile_edit_form = UserProfileEditForm(request.POST, instance=user.profile)
        employee_number_form = EmployeeNumberEditForm(request.POST, instance=confidentiality)

        old_username = user.username
        new_username = request.POST.get('username')
        if user_form.is_valid() and user_profile_edit_form.is_valid() and employee_number_form.is_valid():
            updated_user = user_form.save()

            # Update the new username in the path of items - avatar image, resume, sin and study permit
            if request.POST.get('username') != old_username:
                new_dirpath = os.path.join( settings.MEDIA_ROOT, 'users', new_username )
                if os.path.exists(new_dirpath) == False:
                    try:
                        os.mkdir(new_dirpath) # Create a new directory
                    except OSError:
                        SuspiciousOperation

                # Resume
                if userApi.has_user_resume_created(user) and bool(user.resume.uploaded):
                    resume_path = os.path.join( settings.MEDIA_ROOT, 'users', new_username, 'resume' )
                    if os.path.exists(resume_path) == False:
                        try:
                            os.mkdir(resume_path) # Create a new resume directory
                        except OSError:
                            SuspiciousOperation

                    if os.path.exists(resume_path) and os.path.isdir(resume_path):
                        file_path = user.resume.uploaded.name
                        filename = file_path.replace(old_username, new_username)

                        initial_path = user.resume.uploaded.path
                        new_path = os.path.join(settings.MEDIA_ROOT, filename)
                        os.rename(initial_path, new_path)

                        user.resume.uploaded = filename
                        user.resume.save(update_fields=['uploaded'])

                        # Remove an old resume directory
                        try:
                            os.rmdir( os.path.join( settings.MEDIA_ROOT, 'users', old_username, 'resume' ) )
                        except OSError:
                            SuspiciousOperation

                # Avatar
                if userApi.has_user_avatar_created(user) and bool(user.avatar.uploaded):
                    avatar_path = os.path.join( settings.MEDIA_ROOT, 'users', new_username, 'avatar' )
                    if os.path.exists(avatar_path) == False:
                        try:
                            os.mkdir(avatar_path) # Create a new avatar directory
                        except OSError:
                            SuspiciousOperation

                    if os.path.exists(avatar_path) and os.path.isdir(avatar_path):
                        file_path = user.avatar.uploaded.name
                        filename = file_path.replace(old_username, new_username)

                        initial_path = user.avatar.uploaded.path
                        new_path = os.path.join(settings.MEDIA_ROOT, filename)
                        os.rename(initial_path, new_path)

                        user.avatar.uploaded = filename
                        user.avatar.save(update_fields=['uploaded'])

                        # Remove an old avatar directory
                        try:
                            os.rmdir( os.path.join( settings.MEDIA_ROOT, 'users', old_username, 'avatar' ) )
                        except OSError:
                            SuspiciousOperation

                if userApi.has_user_confidentiality_created(user):
                    update_fields = []
                    if bool(user.confidentiality.sin):
                        sin_path = os.path.join( settings.MEDIA_ROOT, 'users', new_username, 'sin' )
                        if os.path.exists(sin_path) == False:
                            try:
                                os.mkdir(sin_path) # Create a new sin directory
                            except OSError:
                                SuspiciousOperation

                        if os.path.exists(sin_path) and os.path.isdir(sin_path):
                            file_path = user.confidentiality.sin.name
                            filename = file_path.replace(old_username, new_username)

                            initial_path = user.confidentiality.sin.path
                            new_path = os.path.join(settings.MEDIA_ROOT, filename)
                            os.rename(initial_path, new_path)

                            user.confidentiality.sin = filename

                            # Remove an old sin directory
                            try:
                                os.rmdir( os.path.join( settings.MEDIA_ROOT, 'users', old_username, 'sin' ) )
                            except OSError:
                                SuspiciousOperation

                            update_fields.append('sin')

                    if bool(user.confidentiality.study_permit):
                        study_permit_path = os.path.join( settings.MEDIA_ROOT, 'users', new_username, 'study_permit' )
                        if os.path.exists(study_permit_path) == False:
                            try:
                                os.mkdir(study_permit_path) # Create a new study_permit directory
                            except OSError:
                                SuspiciousOperation

                        if os.path.exists(study_permit_path) and os.path.isdir(study_permit_path):
                            file_path = user.confidentiality.study_permit.name
                            filename = file_path.replace(old_username, new_username)

                            initial_path = user.confidentiality.study_permit.path
                            new_path = os.path.join(settings.MEDIA_ROOT, filename)
                            os.rename(initial_path, new_path)

                            user.confidentiality.study_permit = filename

                            # Remove an old sin directory
                            try:
                                os.rmdir( os.path.join( settings.MEDIA_ROOT, 'users', old_username, 'study_permit' ) )
                            except OSError:
                                SuspiciousOperation

                            update_fields.append('study_permit')

                    if len(update_fields) > 0:
                        user.confidentiality.save(update_fields=update_fields)

                # If an old folder is empty, delete it
                old_dirpath = os.path.join( settings.MEDIA_ROOT, 'users', old_username )
                if os.path.exists(old_dirpath) and os.path.isdir(old_dirpath) and len( os.listdir(old_dirpath) ) == 0:
                    try:
                        os.rmdir(old_dirpath)
                    except OSError:
                        print("The folder hasn't been deleted")

            updated_profile = user_profile_edit_form.save(commit=False)
            updated_profile.updated_at = datetime.now()
            updated_profile.save()

            errors = []

            updated_employee_number = employee_number_form.save(commit=False)
            updated_employee_number.updated_at = datetime.now()
            updated_employee_number.is_new_employee = employee_number_form.cleaned_data['is_new_employee']
            updated_employee_number.employee_number = employee_number_form.cleaned_data['employee_number']
            updated_employee_number.save(update_fields=['is_new_employee', 'employee_number', 'updated_at'])

            if not updated_user: errors.append('USER')
            if not updated_profile: errors.append('PROFILE')
            if not updated_employee_number: errors.append('EMPLOYEE NUMBER')

            updated = userApi.update_user_profile_roles(updated_profile, profile_roles, user_profile_edit_form.cleaned_data)
            if not updated: errors.append(request, 'An error occurred while updating profile roles.')

            if len(errors) > 0:
                messages.error(request, 'An error occurred while updating an User Edit Form. {0}'.format( ' '.join(errors) ))
                return HttpResponseRedirect(request.get_full_path())

            messages.success(request, 'Success! User information of {0} (CWL: {1}) updated'.format(user.get_full_name(), user.username))
            return HttpResponseRedirect(request.POST.get('next'))
        else:
            errors = []

            user_errors = user_form.errors.get_json_data()
            profile_errors = user_profile_edit_form.errors.get_json_data()
            confid_errors = employee_number_form.errors.get_json_data()

            if user_errors: errors.append( userApi.get_error_messages(user_errors) )
            if profile_errors: errors.append( userApi.get_error_messages(profile_errors) )
            if confid_errors: errors.append( userApi.get_error_messages(confid_errors) )

            messages.error(request, 'An error occurred while updating an User Form. {0}'.format( ' '.join(errors) ))

        return HttpResponseRedirect(request.get_full_path())

    else:
        profile = userApi.has_user_profile_created(user)
        if profile == None:
            profile = userApi.create_profile_init(user)
            user = userApi.get_user(username, 'username')
            messages.warning(request, 'This user (CWL: {0}) does not have any profile. Users must have at least one role. Please choose a role.'.format(user.username))

    return render(request, 'administrators/hr/edit_user.html', {
        'loggedin_user': request.user,
        'user': userApi.add_avatar(user),
        'roles': userApi.get_roles(),
        'user_form': UserForm(data=None, instance=user),
        'user_profile_form': UserProfileEditForm(data=None, instance=user.profile),
        'employee_number_form': EmployeeNumberEditForm(data=None, instance=confidentiality),
        'next': adminApi.get_next(request)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET','POST'])
def delete_user_confirmation(request, username):
    ''' Delete a user '''
    request = userApi.has_admin_access(request)
    adminApi.can_req_parameters_access(request, 'user', ['next', 'p'])

    user = userApi.get_user(username, 'username')
    apps = []
    if request.method == 'POST':
        user = userApi.get_user( request.POST.get('user') )

        sin = userApi.delete_user_sin(user.username)
        study_permit = userApi.delete_user_study_permit(user.username)

        if userApi.has_user_confidentiality_created(user) != None and sin and study_permit:
            user.confidentiality.delete()

        if userApi.confidentiality_exists(user) == False:
            messages.success(request, "Success! {0} ({1})'s Confidential Information deleted".format(user.get_full_name(), user.username))
        else:
            messages.error(request, 'An error occurred while deleting the Confidential Information of the user - {0}.'.format(user.get_full_name()))

        return HttpResponseRedirect(request.POST.get('next'))

    else:
        user = userApi.add_confidentiality_given_list(user, ['sin','study_permit'])

    return render(request, 'administrators/hr/delete_user_confirmation.html', {
        'loggedin_user': request.user,
        'user': userApi.add_resume(user),
        'users': userApi.get_users(),
        'next': adminApi.get_next(request),
        'undergrad_status_id': userApi.get_undergraduate_status_id()
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def destroy_user_contents(request):
    ''' Destroy users who have no actions for 3 years '''
    request = userApi.has_admin_access(request)

    users = None
    target_date = None
    if request.method == 'POST':
        if len(request.POST.getlist('user')) < 1:
            messages.error(request, 'An error occurred. Please select any user(s) to be destroyed from the list below.')
            return redirect('administrators:destroy_user_contents')

        deleted_users = []
        count = 0
        for user_id in request.POST.getlist('user'):
            user = userApi.get_user(user_id)

            userApi.delete_user_sin(user.username)
            userApi.delete_user_study_permit(user.username)

            if userApi.has_user_confidentiality_created(user):
                user.confidentiality.delete()

            resume = userApi.delete_user_resume(user.id)
            avatar = userApi.delete_user_avatar(user.id)
            profile = userApi.trim_profile(user)

            dirpath = os.path.join( settings.MEDIA_ROOT, 'users', user.username )
            if os.path.exists(dirpath) and os.path.isdir(dirpath):
                os.rmdir(dirpath)

            if profile and resume['status'] == 'success' and avatar['status'] == 'success' and userApi.resume_exists(user) == False and userApi.confidentiality_exists(user) == False:
                deleted_users.append(user.get_full_name())
                count += 1

        if count == len(deleted_users):
            messages.success(request, 'Success! The contents of users ({0}) are destroyed completely'.format( ', '.join(deleted_users) ))
        elif len(deleted_users)> 0:
            messages.warning(request, 'Warning! The contents of users ({0}) are destroyed partially'.format( ', '.join(deleted_users) ))
        else:
            messages.error(request, 'An error occurred. Form is invalid. {0}')

        return redirect('administrators:destroy_user_contents')

    else:
        user_list, target_date = userApi.get_users('destroy')
        users = []
        for user in user_list:
            user = userApi.add_confidentiality_given_list(user, ['sin','study_permit'])
            user = userApi.add_resume(user)
            users.append(user)

    return render(request, 'administrators/hr/destroy_user_contents.html', {
        'loggedin_user': request.user,
        'users': users,
        'target_date': target_date,
        'undergrad_status_id': userApi.get_undergraduate_status_id()
    })


# Roles

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def roles(request):
    ''' Display all roles and create a role '''
    request = userApi.has_superadmin_access(request)

    if request.method == 'POST':
        form = RoleForm(request.POST)
        if form.is_valid():
            role = form.save()
            if role:
                messages.success(request, 'Success! {0} has been created'.format(role.name))
            else:
                messages.error(request, 'An error occurred while saving data.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return redirect('administrators:roles')

    return render(request, 'administrators/hr/roles.html', {
        'loggedin_user': request.user,
        'roles': userApi.get_roles(),
        'form': RoleForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_role(request, slug):
    ''' Edit a role '''
    request = userApi.has_superadmin_access(request)

    if request.method == 'POST':
        role = userApi.get_role_by_slug(slug)
        form = RoleForm(request.POST, instance=role)
        if form.is_valid():
            updated_role = form.save()
            if updated_role:
                messages.success(request, 'Success! {0} has been updated'.format(updated_role.name))
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))
    return redirect("administrators:roles")

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_role(request):
    ''' Delete a role '''
    request = userApi.has_superadmin_access(request)

    if request.method == 'POST':
        role_id = request.POST.get('role')
        deleted_role = userApi.delete_role(role_id)
        if deleted_role:
            messages.success(request, 'Success! {0} has been deleted'.format(deleted_role.name))
        else:
            messages.error(request, 'An error occurred.')
    return redirect("administrators:roles")
