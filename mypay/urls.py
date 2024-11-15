from django.urls import path
from . import views

urlpatterns = [
    path('mypay/', views.mypay_view, name='mypay'),
    path('mypay/transaction/', views.mypay_transaction_form_view, name='mypay_transaction_form'),
]
