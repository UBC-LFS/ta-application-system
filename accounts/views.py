from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as AuthLogin
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from .forms import LocalLoginForm
from users import api as userApi

def login(request):
    ''' Login page '''
    return render(request, 'accounts/login.html')


def local_login(request):
    users = User.objects.all()
    if request.method == 'POST':
        form = LocalLoginForm(request.POST)
        if form.is_valid():
            user = userApi.user_exists(request.POST['username'])
            if user is not None and request.POST['password'] is not None:
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

    return render(request, 'accounts/local_login.html', { 'form': LocalLoginForm() })
