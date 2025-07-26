import django_filters
from .models import MedicineData, MedicineType, GenericName

class MedicineDataFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name="name",lookup_expr='startswith')
    generic_name = django_filters.CharFilter(field_name="generic_name__name", lookup_expr="icontains")
    medicine_type = django_filters.CharFilter(field_name="medicine_type__name", lookup_expr="icontains")

    class Meta:
        model = MedicineData
        fields = ["name", "generic_name", "medicine_type"]

class GenericNameFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name="name", lookup_expr='startswith')

    class Meta:
        model = GenericName
        fields = ["name"]

class MedicineTypeFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name="name", lookup_expr='startswith')

    class Meta:
        model = MedicineType
        fields = ["name"]
