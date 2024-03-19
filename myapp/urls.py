from myapp.views.home import home
from myapp.views.logout import logout
from myapp.views.room import newroom
from myapp.views.register import RegisterView

from django.urls import path
# from django.contrib import admin
from django.contrib.auth import views as auth_views

# app_name = 'myapp'
urlpatterns = [
    path('', home, name='home'),
    # path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='myapp/login.html'), name='login'),
    path('logout/', logout, name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('room/', newroom, name='room'),
]
