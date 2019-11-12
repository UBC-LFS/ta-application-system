from django.urls import path
from . import views

app_name = 'human_resources'

urlpatterns = [
    path('', views.index, name='index'),
    path('users/<str:username>/confidentiality/', views.view_confidentiality, name='view_confidentiality'),
    path('users/<str:username>/details/', views.show_user, name='show_user'),
    path('users/all/', views.all_users, name='all_users')
]
