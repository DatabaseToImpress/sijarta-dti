from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_page, name='home_page'),
    path('subcategory/<int:id>/', views.subcategory_services_user, name='subcategory_services_user'),
    path('booking/', views.booking_view, name='booking'),
    path('worker/<str:worker_name>/', views.worker_profile, name='worker_profile'),
]