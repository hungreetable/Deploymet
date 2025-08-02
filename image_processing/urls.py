from django.urls import path
from image_processing.views import ImageProcessingAPI, PrescriptionAPI

urlpatterns = [
    path('', PrescriptionAPI.as_view(), name='prescription'),
    path('imageprocess/', ImageProcessingAPI.as_view(), name='imageprocess'),
]
