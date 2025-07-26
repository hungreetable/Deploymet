from rest_framework import serializers
from image_processing.models import PrescriptionRecord


class PrescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionRecord
        fields = '__all__'