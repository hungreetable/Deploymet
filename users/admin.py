from django.contrib import admin
from users.models import User, DoctorPersonalDetail, Patient, Receptionist


admin.site.register(User)

admin.site.register(DoctorPersonalDetail)

admin.site.register(Patient)

admin.site.register(Receptionist)