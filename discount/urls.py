from django.urls import path
from . import views

urlpatterns = [
    path('discount/', views.discount_page, name='discount_page'),
]
