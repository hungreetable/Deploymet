from rest_framework import serializers
from .models import ClinicCharge, PatientCharge
class ClinicChargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicCharge
        fields = '__all__'


class PatientChargeSerializer(serializers.ModelSerializer):

    total_cost = serializers.IntegerField(read_only=True)
    patient_name = serializers.SerializerMethodField()
    prescription_type = serializers.SerializerMethodField()
    follow_up_date = serializers.SerializerMethodField()

    class Meta:
        model = PatientCharge
        fields = '__all__'
        read_only_fields = ['total_cost']
    
    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.middle_name or ''} {obj.patient.last_name}".strip()

    def get_prescription_type(self, obj):
        return obj.prescriptionRecord.type if obj.prescriptionRecord else None
    
    def get_follow_up_date(self, obj):
        return obj.prescriptionRecord.follow_up_date if obj.prescriptionRecord else None

