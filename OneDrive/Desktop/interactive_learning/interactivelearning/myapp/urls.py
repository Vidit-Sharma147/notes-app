from django.urls import path
from . import views

urlpatterns = [
    path('', views.main, name='main'),          # http://localhost:8000/
    path('login/', views.login, name='login'),  # http://localhost:8000/login/
    path('login/', views.login_page, name='login'),
   
    path('mainlogin/', views.mainlogin_page, name='mainlogin'),
    path('main/', views.main_page, name='main'),

]
