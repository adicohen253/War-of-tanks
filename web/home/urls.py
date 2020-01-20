from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='homepage'),
    path('champion-table', views.top_players, name='top players'),
    path('download/', views.download, name='download')
]
