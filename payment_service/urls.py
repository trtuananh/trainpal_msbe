from django.urls import path
from . import views

app_name = 'payment_service'

urlpatterns = [
    path('payments/', views.get_payments, name="payments"),
    path('payment/<str:pk>/', views.get_payment, name="payment"),
    path('create-payment/', views.create_payment, name="create_payment"),
    path('momo-payment/', views.momo_payment, name="momo_payment"),
    path('momo-payment-callback/', views.momo_payment_callback, name="momo_payment_callback"),
    path('verify-payment/', views.verify_momo_payment, name="verify_payment"),
]
