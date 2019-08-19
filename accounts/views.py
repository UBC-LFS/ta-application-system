from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as AuthLogin
from .forms import LocalLoginForm


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
                return redirect('home:index')

    return render(request, 'accounts/local_login.html', { 'form': LocalLoginForm() })
