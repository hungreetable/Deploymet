from django.contrib import admin
from image_processing.models import PrescriptionRecord


class PrescriptionRecordAdmin(admin.ModelAdmin):
    list_display = ('patient_name', 'prescription_date')


admin.site.register(PrescriptionRecord, PrescriptionRecordAdmin)
