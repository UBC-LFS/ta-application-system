from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as AuthLogin
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from .forms import LocalLoginForm
from users import api as userApi

def login(request):
    """ Login page """
    return render(request, 'accounts/login.html')


def local_login(request):
    users = User.objects.all()
    if request.method == 'POST':
        form = LocalLoginForm(request.POST)
        if form.is_valid():
            user = User.objects.get(username=request.POST['username'])
            if user is not None and request.POST['password'] is not None:
                AuthLogin(request, user)
                loggedin_user = userApi.loggedin_user(user)
                if 'Admin' in loggedin_user.roles or 'Superadmin' in loggedin_user.roles:
                    return redirect('administrators:index')
                elif 'HR' in loggedin_user.roles:
                    return redirect('human_resources:index')
                elif 'Instructor' in loggedin_user.roles:
                    return redirect('instructors:index')
                elif 'Student' in loggedin_user.roles:
                    return redirect('students:index')

    return render(request, 'accounts/local_login.html', { 'form': LocalLoginForm() })
