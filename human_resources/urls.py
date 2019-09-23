from django.urls import path
from . import views

app_name = 'human_resources'

urlpatterns = [
    path('', views.index, name='index'),
    path('users/confidentiality/', views.users_confidentiality, name='users_confidentiality')
]
