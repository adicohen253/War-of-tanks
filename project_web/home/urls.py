from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='homepage'),
    path('sign-in/', views.sign_in, name='sign in')
]
