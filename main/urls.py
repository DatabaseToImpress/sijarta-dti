from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.home_page, name='home_page'),
    path('subcategory/<int:id>/', views.subcategory_services_user, name='subcategory_services_user'),
    path('subcategory_worker/<int:id>/', views.subcategory_services_worker, name='subcategory_services_worker'),
    path('booking/', views.booking_view, name='booking'),
    path('worker/<str:worker_name>/', views.worker_profile, name='worker_profile'),
    path('worker/<str:worker_name>/', views.worker_profile, name='worker_profile'),
    path('add-testimonial/', views.add_testimonial, name='add_testimonial'),
    path('submit-testimonial/', views.submit_testimonial, name='submit_testimonial'),
]
