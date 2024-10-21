from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('home', views.newhome, name='newhome'),
    path('create_resume', views.create_resume, name='create_resume'),
]