from django.urls import path
from .views import SpellCheckMedicine, MedicineAPI

urlpatterns = [
    path('check/', SpellCheckMedicine.as_view(), name='spell-check-medicine'),
    path('data/', MedicineAPI.as_view(), name='medicine')
]