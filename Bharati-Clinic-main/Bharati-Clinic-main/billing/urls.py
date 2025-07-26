from django.urls import path
from .views import BillingAPI

urlpatterns = [
    path('', BillingAPI.as_view(), name='prescription'),
]
