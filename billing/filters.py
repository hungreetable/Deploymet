import django_filters
from django.db.models import Q, Value
from datetime import datetime, timedelta
from .models import PatientCharge

class PatientChargeFilter(django_filters.FilterSet):
    patient_id = django_filters.NumberFilter(field_name='patient__id', lookup_expr='exact')
    patient_name = django_filters.CharFilter(method='filter_by_patient_name')
    prescription_record_id = django_filters.NumberFilter(field_name='prescriptionRecord__id', lookup_expr='exact')
    filter_response = django_filters.CharFilter(method='filter_by_date_range')
    type = django_filters.CharFilter(method='filter_type')
    from_date = django_filters.DateFilter(method='filter_by_from_date')
    to_date = django_filters.DateFilter(method='filter_by_to_date')

    class Meta:
        model = PatientCharge
        fields = ['patient_id','patient_name','prescription_record_id','type','from_date','to_date']
    
    def filter_type(self, queryset, name, value):
        if value in ["O", "N"]:
            return queryset.filter(prescriptionRecord__type=value)
        return queryset
    
    def filter_by_from_date(self, queryset, name, value):
        return queryset.filter(date_created__date__gte=value)

    def filter_by_to_date(self, queryset, name, value):
        return queryset.filter(date_created__date__lte=value)
    
    def filter_by_date_range(self, queryset, name, value):
        today = datetime.today().date()

        if value == "today":
            return queryset.filter(date_created__date=today)

        elif value == "week":
            from_date = today - timedelta(days=today.weekday())
            return queryset.filter(date_created__date__range=(from_date, today))

        elif value == "month":
            from_date = today.replace(day=1)
            return queryset.filter(date_created__date__range=(from_date, today))

        return queryset

    def filter_by_patient_name(self, queryset, name, value):
        parts = value.strip().split()
        parts = [part.lower() for part in parts]

        if len(parts) == 3:
            first, middle, last = parts
            return queryset.filter(
                Q(patient__first_name__iexact=first) &
                Q(patient__middle_name__iexact=middle) &
                Q(patient__last_name__iexact=last)
            )

        elif len(parts) == 2:
            first, last = parts
            return queryset.filter(
                Q(patient__first_name__iexact=first) &
                Q(patient__last_name__iexact=last)
            )

        elif len(parts) == 1:
            name = parts[0]
            return queryset.filter(
                Q(patient__first_name__icontains=name) |
                Q(patient__middle_name__icontains=name) |
                Q(patient__last_name__icontains=name)
            )

        return queryset
