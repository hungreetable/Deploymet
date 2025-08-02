from django.db import models
from users.models import Patient
from image_processing.models import PrescriptionRecord

# Create your models here.
class ClinicCharge(models.Model):
    """
    Model to store constant hospital service prices.
    """
    first_check_up_charge = models.PositiveIntegerField(default=400)
    follow_up_check_up_charge = models.PositiveIntegerField(default=300)
    one_month_late_check_up_charge = models.PositiveIntegerField(default=400)
    stress_test_charge = models.PositiveIntegerField(default=1900)
    ecg_test_charge = models.PositiveIntegerField(default=1500)
    morning_ect_injection_charge = models.PositiveIntegerField(default=2000)
    injection_in_back_charge = models.PositiveIntegerField(default=600)
    counselling_session_charge = models.PositiveIntegerField(default=1000)
    evening_first_check_up_charge = models.PositiveIntegerField(default=500)
    evening_follow_up_check_up_charge = models.PositiveIntegerField(default=400)
    special_appointment_check_up_charge = models.PositiveIntegerField(default=600)

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "clinic_charge"
        verbose_name = "Clinic Charge"
        verbose_name_plural = "Clinic Charges"

    def __str__(self):
        return f"Clinic Charges {self.pk}"

class PatientCharge(models.Model):
    """
    Model to store which services a patient has used (True/False).
    """

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="patient_charge",
        verbose_name="Patient"
    )

    prescriptionRecord = models.ForeignKey(
        PrescriptionRecord,
        on_delete=models.CASCADE,
        related_name="patient_charge",
        verbose_name="Prescription Record",
        null=True,
        blank=True
    )

    first_check_up = models.PositiveIntegerField(default=0)
    follow_up_check_up = models.PositiveIntegerField(default=0)
    one_month_late_check_up = models.PositiveIntegerField(default=0)
    stress_test = models.PositiveIntegerField(default=0)
    ecg_test = models.PositiveIntegerField(default=0)
    morning_ect_injection = models.PositiveIntegerField(default=0)
    injection_in_back = models.PositiveIntegerField(default=0)
    counselling_session = models.PositiveIntegerField(default=0)
    evening_first_check_up = models.PositiveIntegerField(default=0)
    evening_follow_up_check_up = models.PositiveIntegerField(default=0)
    special_appointment_check_up = models.PositiveIntegerField(default=0)

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "patient_charge"
        verbose_name = "Patient Charge"
        verbose_name_plural = "Patient Charges"

    def __str__(self):
        return f"PatientCharge for {self.patient.first_name}"

