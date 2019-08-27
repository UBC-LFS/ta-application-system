from django.urls import path
from . import views

app_name = 'human_resources'

urlpatterns = [
    path('', views.index, name='index')
]
