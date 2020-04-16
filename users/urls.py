from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('profile/photo/upload/', views.upload_avatar, name='upload_avatar'),
    path('profile/photo/delete/', views.delete_avatar, name='delete_avatar'),
    path('profile/<str:username>/details/', views.show_user, name='show_user'),
]
