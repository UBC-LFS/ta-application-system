from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('r/<str:role>/profile/photo/upload/', views.upload_avatar, name='upload_avatar'),
    path('r/<str:role>/profile/photo/delete/', views.delete_avatar, name='delete_avatar')
]
