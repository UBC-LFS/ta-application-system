from django.conf import settings
from django.shortcuts import render
from django.urls import reverse, resolve
from django.http import HttpResponseRedirect
from urllib.parse import urlparse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied

from administrators import api as adminApi
from users.models import Role
from users.forms import AvatarForm
from users import api as userApi


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_user(request, username):
    ''' Display an user's details '''
    request = userApi.has_auth_user_access(request)
    adminApi.can_req_parameters_access(request, 'user-tab', ['next', 'p', 't'])

    next = adminApi.get_next(request)
    urlparse_next = urlparse(next)
    page = request.GET.get('p')
    tab = request.GET.get('t')

    user = userApi.get_user(username, 'username')
    user = userApi.add_avatar(user)
    user.is_student = userApi.user_has_role(user , Role.STUDENT)
    if user.is_student:
        userApi.add_resume(user)

    if tab == 'confidential':
        user = userApi.add_confidentiality_given_list(user, ['sin','study_permit'])

    return render(request, 'users/show_user.html', {
        'loggedin_user': request.user,
        'selected_user': user,
        'go_back': {
            'url': adminApi.get_next(request),
            'page': page
        },
        'tab_urls': {
            'basic': adminApi.build_url(request.path, next, page, 'basic'),
            'additional': adminApi.build_url(request.path, next, page, 'additional') if user.is_student else None,
            'confidential': adminApi.build_url(request.path, next, page, 'confidential') if user.is_student else None,
            'resume': adminApi.build_url(request.path, next, page, 'resume') if user.is_student else None
        },
        'role': resolve(urlparse_next.path).app_name,
        'current_tab': tab
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def upload_avatar(request):
    ''' Upload an Avatar '''
    next = urlparse(request.GET.get('next'))
    role = resolve(next.path).app_name
    request = userApi.has_users_view_access(request, role)

    if request.method == 'POST':
        if len(request.FILES) == 0:
            messages.error(request, 'An error occurred. Please select your profile photo, then try again.')
            return HttpResponseRedirect(request.get_full_path())

        form = AvatarForm(request.POST, request.FILES)
        if form.is_valid():
            avatar = form.save(commit=False)
            avatar.uploaded = request.FILES.get('uploaded')
            avatar.save()
            if avatar:
                messages.success(request, 'Success! Profile Photo uploaded.')
            else:
                messages.error(request, 'An error occurred while uploading an avatar.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return HttpResponseRedirect(request.get_full_path())

    return render(request, 'users/upload_avatar.html', {
        'loggedin_user': userApi.add_avatar(request.user),
        'role': role,
        'form': AvatarForm(initial={ 'user': request.user })
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_avatar(request):
    ''' delete an avatar '''
    next = urlparse(request.GET.get('next'))
    role = resolve(next.path).app_name
    request = userApi.has_users_view_access(request, role)

    if request.method == 'POST':
        username = request.POST.get('user')
        if userApi.delete_user_avatar(username):
            messages.success(request, 'Success! Profile Photo deleted.')
        else:
            messages.error(request, 'An error occurred.')

    return HttpResponseRedirect(reverse('users:upload_avatar') + '?next=' + request.GET.get('next'))
