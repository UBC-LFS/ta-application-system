from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as AuthLogin
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.contrib import messages

from accounts.forms import LocalLoginForm
from users import api as userApi
from administrators import api as adminApi


def local_login(request):
    if request.method == 'POST':
        form = LocalLoginForm(request.POST)
        if form.is_valid():
            user = authenticate(username=request.POST['username'], password=request.POST['password'])
            if user:
                AuthLogin(request, user)
                roles = userApi.get_user_roles(user)
                if not roles:
                    messages.error(request, 'An error occurred. Users must have at least one role.')
                else:
                    request.session['loggedin_user'] = {
                        'id': user.id,
                        'username': user.username,
                        'roles': roles
                    }
                    redirect_to = adminApi.redirect_to_index_page(roles)
                    return HttpResponseRedirect(redirect_to)
            else:
                messages.error(request, 'An error occurred. Please check your username and password, then try again.')
        else:
            messages.error(request, 'An error occurred. Form is invalid. Please check your inputs.')

        return redirect('accounts:local_login')

    else:
        if 'loggedin_user' in request.session.keys():
            roles = request.session['loggedin_user']['roles']
            redirect_to = adminApi.redirect_to_index_page(roles)
            return HttpResponseRedirect(redirect_to)

    return render(request, 'accounts/local_login.html', {
        'form': LocalLoginForm()
    })


"""
def login(request):
    if 'loggedin_user' in request.session.keys():
        roles = request.session['loggedin_user']['roles']
        redirect_to = adminApi.redirect_to_index_page(roles)
        return HttpResponseRedirect(redirect_to)

    return render(request, 'accounts/login.html', {
        'landing_page': adminApi.get_visible_landing_page()
    })
"""

