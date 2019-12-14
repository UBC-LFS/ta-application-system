from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as AuthLogin
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.contrib import messages
from accounts.forms import LocalLoginForm
from users import api as userApi


def redirect_to_index_page(roles):
    ''' Redirect to an index page given roles '''
    if 'Admin' in roles or 'Superadmin' in roles or 'HR' in roles:
        return '/administrators/'
    elif 'Instructor' in roles:
        return '/instructors/'
    elif 'Student' in roles:
        return '/students/'

    return '/students/'


def login(request):
    ''' Login page '''
    if 'loggedin_user' in request.session.keys():
        roles = request.session['loggedin_user']['roles']
        redirect_to = redirect_to_index_page(roles)
        return HttpResponseRedirect(redirect_to)

    return render(request, 'accounts/login.html')


def local_login(request):
    ''' Local login '''
    if request.method == 'POST':
        form = LocalLoginForm(request.POST)
        if form.is_valid():
            user = authenticate(username=request.POST['username'], password=request.POST['password'])
            if user is not None:
                AuthLogin(request, user)
                roles = userApi.get_user_roles(user)
                if roles == None:
                    messages.error(request, 'An error occurred. Users must have at least one role.')
                else:
                    request.session['loggedin_user'] = {
                        'id': user.id,
                        'username': user.username,
                        'roles': roles
                    }
                    redirect_to = redirect_to_index_page(roles)
                    return HttpResponseRedirect(redirect_to)
            else:
                messages.error(request, 'An error occurred. Please check your username and password, then try again.')
        else:
            messages.error(request, 'An error occurred. Form is invalid. Please check your inputs.')

        return redirect('accounts:local_login')

    else:
        if 'loggedin_user' in request.session.keys():
            roles = request.session['loggedin_user']['roles']
            redirect_to = redirect_to_index_page(roles)
            return HttpResponseRedirect(redirect_to)

    return render(request, 'accounts/local_login.html', {
        'form': LocalLoginForm()
    })
