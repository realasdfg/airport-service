import django_filters

from airport.models import (
    City,
)


class CityFilter(django_filters.FilterSet):
    country = django_filters.CharFilter(lookup_expr="icontains")
    name = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = City
        fields = ("country", "name")
