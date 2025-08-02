from rest_framework import serializers
from .models import MedicineData, MedicineType, GenericName

class MedicineTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicineType
        fields = "__all__"

class GenericNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = GenericName
        fields = "__all__"


class CustomMedicineTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicineType
        fields = ['id', 'name']

class CustomGenericNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = GenericName
        fields = ['id', 'name']


class MedicineDataSerializer(serializers.ModelSerializer):
    medicine_type = CustomMedicineTypeSerializer(read_only=True)
    generic_name = CustomGenericNameSerializer(read_only=True)

    class Meta:
        model = MedicineData
        fields = ['id', 'name', 'price', 'quantity', 'medicine_type', 'generic_name', 'date_created', 'date_updated']