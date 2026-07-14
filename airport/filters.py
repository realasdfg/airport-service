import django_filters

from airport.models import (
    City,
    Airport,
)


class NumberInFilter(django_filters.BaseInFilter, django_filters.NumberFilter):
    pass


class CityFilter(django_filters.FilterSet):
    country = django_filters.CharFilter(lookup_expr="icontains")
    name = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = City
        fields = ("country", "name")


class AirportFilter(django_filters.FilterSet):
    country = django_filters.CharFilter(
        field_name="closest_big_city__country",
        lookup_expr="icontains",
    )
    iata_code = django_filters.CharFilter(lookup_expr="icontains")
    name = django_filters.CharFilter(lookup_expr="icontains")
    cities = NumberInFilter(field_name="closest_big_city_id")

    class Meta:
        model = Airport
        fields = ("country", "iata_code", "name", "cities",)
