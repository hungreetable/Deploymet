from django.contrib import admin
from .models import MedicineData, MedicineType, GenericName


# Register your models here.
class GenericAdmin(admin.ModelAdmin):
    list_display = ('name',)


class MedicineTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)


class MedicineDataAdmin(admin.ModelAdmin):
    list_display = ('name', 'medicine_type', 'generic_name')


admin.site.register(MedicineData, MedicineDataAdmin)
admin.site.register(MedicineType, MedicineTypeAdmin)
admin.site.register(GenericName, GenericAdmin)
