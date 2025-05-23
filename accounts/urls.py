from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('register/', views.register_landing, name='register'),
    path('register/user/', views.register_user, name='register_user'),
    path('register/worker/', views.register_worker, name='register_worker'),
    path('profileu/', views.profileu, name='profileu'),
    path('profilew/', views.profilew, name='profilew'),
    path('profileu/update/', views.profileUserUpdate, name='profileUserUpdate'),
    path('profilew/update/', views.profileWorkerUpdate, name='profileWorkerUpdate'),
]
