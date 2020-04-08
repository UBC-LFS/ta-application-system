from django.conf import settings
from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied

from users.forms import AvatarForm
from users import api as userApi


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def upload_avatar(request, role):
    ''' Upload an Avatar '''
    request = userApi.has_users_view_access(request, role)

    if request.method == 'POST':
        if len(request.FILES) == 0:
            messages.error(request, 'An error occurred. Please select your profile photo, then try again.')
            return redirect('users:upload_avatar')

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

        return HttpResponseRedirect( reverse('users:upload_avatar', args=[role]) )

    return render(request, 'users/upload_avatar.html', {
        'loggedin_user': userApi.add_avatar(request.user),
        'role': role,
        'home_url': reverse('{0}:index'.format(role)),
        'form': AvatarForm(initial={ 'user': request.user })
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_avatar(request, role):
    ''' delete an avatar '''
    request = userApi.has_users_view_access(request, role)

    if request.method == 'POST':
        username = request.POST.get('user')
        if userApi.delete_user_avatar(username):
            messages.success(request, 'Success! Profile Photo deleted.')
        else:
            messages.error(request, 'An error occurred.')

    return HttpResponseRedirect( reverse('users:upload_avatar', args=[role]) )
