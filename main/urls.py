from django.urls import path, register_converter
from . import views
import uuid

class UUIDConverter:
    regex = '[0-9a-f-]{36}'

    def to_python(self, value):
        return uuid.UUID(value)

    def to_url(self, value):
        return str(value)
register_converter(UUIDConverter, 'uuid')

app_name = 'main'
 
urlpatterns = [
    path('home/', views.home_page, name='home_page'),
    path('subcategory/<str:id>/', views.subcategory_services_user, name='subcategory_services_user'),
    path('booking/', views.booking_view, name='booking'),
    path('worker/<str:worker_name>/', views.worker_profile, name='worker_profile'),
    path('add-testimonial/', views.add_testimonial, name='add_testimonial'),
    path('view-bookings/', views.view_booking, name='view_bookings'),
    path('delete-order/<uuid:pk>/', views.delete_order, name='delete-order'),
]
