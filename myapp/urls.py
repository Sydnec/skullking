from myapp.views.home import *
from myapp.views.game import *
from myapp.views.logout import *
from myapp.views.room import *
from myapp.views.register import RegisterView

from django.urls import path, re_path
# from django.contrib import admin
from django.contrib.auth import views as auth_views

# app_name = 'myapp'
urlpatterns = [
    path('', home, name='home'),
    # path('admin/', admin.site.urls),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='myapp/login.html'), name='login'),
    path('login/', auth_views.LoginView.as_view(template_name='myapp/login.html'), name='login'),
    path('logout/', logout, name='logout'),
    path('register/', RegisterView.as_view(), name='register'),

    # Gestion des rooms
    path('room/', newroom, name='newroom'),
    path('room/<room_id>', display, name='room'),
    re_path(r'^room/(?P<room_id>[a-zA-Z0-9]{6})/$', display),  
    path('leave/<room_id>', leaveroom, name='leave'),
    re_path(r'^leave/(?P<room_id>[a-zA-Z0-9]{6})/$', leaveroom),

    # Gestion des appels websocket
    path('action/', game_action, name='action'),
]
