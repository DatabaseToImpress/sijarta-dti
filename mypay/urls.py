from django.urls import path
from . import views

urlpatterns = [
    path('mypay/', views.mypay_view, name='mypay'),
    path('mypay/transaction/', views.mypay_transaction,name='mypay_transaction'),
    path('servicejob/', views.service_job, name='servicejob'),
    path('servicejob/status', views.service_job_status, name='servicejobstatus'),
    path('servicejob/update-status/', views.update_order_status, name='update_order_status'),
    path('accept-order', views.accept_order, name='accept_order'),
]
