from django.urls import path
from . import views

app_name = 'main'
 
urlpatterns = [
    path('home/', views.home_page, name='home_page'),
    path('subcategory/<str:id>/', views.subcategory_services_user, name='subcategory_services_user'),
    path('booking/', views.booking_view, name='booking'),
    path('worker/<str:worker_name>/', views.worker_profile, name='worker_profile'),
    path('add-testimonial/', views.add_testimonial, name='add_testimonial'),
    path('view-bookings/', views.view_booking, name='view_bookings'),
]
