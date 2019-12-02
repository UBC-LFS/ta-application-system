from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as AuthLogin
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from .forms import LocalLoginForm
from users import api as userApi

def login(request):
    ''' Login page '''
    if 'loggedin_user' in request.session.keys():
        roles = request.session['loggedin_user']['roles']
        if 'Admin' in roles or 'Superadmin' in roles:
            return redirect('administrators:index')
        elif 'HR' in roles:
            return redirect('human_resources:index')
        elif 'Instructor' in roles:
            return redirect('instructors:index')
        elif 'Student' in roles:
            return redirect('students:index')
        else:
            return redirect('students:index')

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
                request.session['loggedin_user'] = {
                    'id': user.id,
                    'username': user.username,
                    'roles': roles
                }
                if 'Admin' in roles or 'Superadmin' in roles:
                    return redirect('administrators:index')
                elif 'HR' in roles:
                    return redirect('human_resources:index')
                elif 'Instructor' in roles:
                    return redirect('instructors:index')
                elif 'Student' in roles:
                    return redirect('students:index')
                else:
                    return redirect('students:index')
            else:
                messages.error('An error occurred. Please check your username and password, then try again.')
        else:
            messages.error('An error occurred. Form is invalid. Please check your inputs.')
        return redirect('accounts:local_login')
        
    else:
        if 'loggedin_user' in request.session.keys():
            roles = request.session['loggedin_user']['roles']
            if 'Admin' in roles or 'Superadmin' in roles:
                return redirect('administrators:index')
            elif 'HR' in roles:
                return redirect('human_resources:index')
            elif 'Instructor' in roles:
                return redirect('instructors:index')
            elif 'Student' in roles:
                return redirect('students:index')
            else:
                return redirect('students:index')

    return render(request, 'accounts/local_login.html', {
        'form': LocalLoginForm()
    })
