from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('local_login/', views.local_login, name='local_login'),
    path('login/', views.login, name='login')
]
