from django.contrib import admin
from .models import PatientCharge, ClinicCharge
# Register your models here.

admin.site.register(ClinicCharge)
admin.site.register(PatientCharge)

