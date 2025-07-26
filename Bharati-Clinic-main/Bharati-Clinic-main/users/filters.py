import django_filters
from users.models import User, DoctorPersonalDetail, Patient, Receptionist


class UserFilter(django_filters.FilterSet):
    id = django_filters.NumberFilter(field_name='id', lookup_expr='exact')
    email = django_filters.CharFilter(lookup_expr='startswith')

    class Meta:
        model = User
        fields = []


class DoctorPersonalDetailFilter(django_filters.FilterSet):
    first_name = django_filters.CharFilter(
        field_name="first_name", lookup_expr="icontains"
    )
    last_name = django_filters.CharFilter(
        field_name="last_name", lookup_expr="icontains"
    )
    specialty = django_filters.CharFilter(
        field_name="specialty", lookup_expr="icontains"
    )

    class Meta:
        model = DoctorPersonalDetail
        fields = ['first_name', 'last_name', 'specialty']

class PatientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name="first_name", lookup_expr='startswith'
    )

    class Meta:
        model = Patient
        fields = ['name']

class ReceptionistFilter(django_filters.FilterSet):
    first_name = django_filters.CharFilter(
        field_name="first_name", lookup_expr="icontains"
    )
    last_name = django_filters.CharFilter(
        field_name="last_name", lookup_expr="icontains"
    )
    specialty = django_filters.CharFilter(
        field_name="specialty", lookup_expr="icontains"
    )

    class Meta:
        model = Receptionist
        fields = ['first_name', 'last_name', 'specialty']