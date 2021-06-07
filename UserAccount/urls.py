from os import name
from . import views
from django.urls import path
from django.contrib import admin
from .views import Activate

urlpatterns = [
    path('',views.intro,name="intro"),
    path('login/', views.page_login, name="login"),
    path('signup/', views.sign_up, name="sign_up"),
    path('signup/emailcheck/', views.email_check, name="email_check"),
    path('signup_action/', views.signup_action, name="signup_action"),
    path('modifyData/', views.modify_data, name="modify_data"),
    path('mySigns/', views.saved_signs, name="saved_signs"),
    path('login_action/', views.login_action, name="login_action"),
    path('logout_action/', views.logout_action, name="logout_action"),
    path('activate/<str:uidb64>/<str:token>', Activate.as_view(), name="activate"),
    path('modifyData/pwCheck/', views.password_check, name="password_check"),
    path('modifyData/apply/', views.modify_action, name="modify_action"),
    path('modifyData/getFirstnameKr/', views.get_firstname_kr, name="get_firstname_kr"),
    path('modifyData/getLastnameKr/', views.get_lastname_kr, name="get_lastname_kr"),
    path('modifyData/getFirstnameEn/', views.get_firstname_en, name="get_firstname_en"),
    path('modifyData/getLastnameEn/', views.get_lastname_en, name="get_lastname_en"),
]