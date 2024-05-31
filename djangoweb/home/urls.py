from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='homepage'),
    path('champion/', views.top_players, name='top players'),
    path('download/', views.download, name='download')
]
