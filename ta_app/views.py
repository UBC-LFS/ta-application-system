from django.shortcuts import render

def index(request):
    return render(request, 'ta_app/index.html')
