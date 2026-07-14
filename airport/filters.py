import django_filters
from django.db.models import F

from airport.models import (
    City,
    Airport,
    Route,
    AirplaneType,
    Airplane,
    Position,
    Crew,
    Flight,
    Order,
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


class RouteFilter(django_filters.FilterSet):
    source = django_filters.NumberFilter()
    destination = django_filters.NumberFilter()
    source_iata = django_filters.CharFilter(
        field_name="source__iata_code",
        lookup_expr="icontains",
    )
    destination_iata = django_filters.CharFilter(
        field_name="destination__iata_code",
        lookup_expr="icontains",
    )

    class Meta:
        model = Route
        fields = ("source", "destination", "source_iata", "destination_iata",)


class AirplaneTypeFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = AirplaneType
        fields = ("name",)


class AirplaneFilter(django_filters.FilterSet):
    capacity_min = django_filters.NumberFilter(method="filter_capacity_min")
    capacity_max = django_filters.NumberFilter(method="filter_capacity_max")
    airplane_types = NumberInFilter(
        field_name="airplane_type__id",
    )
    name = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Airplane
        fields = ("capacity_min", "capacity_max", "airplane_types", "name",)

    @staticmethod
    def filter_capacity_min(queryset, name, value):
        return queryset.annotate(
            total_capacity=F("rows") * F("seats_in_row")
        ).filter(total_capacity__gte=value)

    @staticmethod
    def filter_capacity_max(queryset, name, value):
        return queryset.annotate(
            total_capacity=F("rows") * F("seats_in_row")
        ).filter(total_capacity__lte=value)


class PositionFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Position
        fields = ("name",)


class CrewFilter(django_filters.FilterSet):
    first_name = django_filters.CharFilter(lookup_expr="icontains")
    last_name = django_filters.CharFilter(lookup_expr="icontains")
    positions = NumberInFilter(
        field_name="position__id",
    )

    class Meta:
        model = Crew
        fields = ("first_name", "last_name", "positions",)


class FlightFilter(django_filters.FilterSet):
    crews = NumberInFilter(field_name="crew__id")
    has_available_tickets = django_filters.BooleanFilter(
        method="filter_has_available_tickets"
    )
    departure_time = django_filters.IsoDateTimeFromToRangeFilter(
        field_name="departure_time",
    )
    arrival_time = django_filters.IsoDateTimeFromToRangeFilter(
        field_name="arrival_time",
    )
    route = RouteFilter()

    class Meta:
        model = Flight
        fields = (
            "crews",
            "has_available_tickets",
            "departure_time",
            "arrival_time",
            "route",
        )

    @staticmethod
    def filter_has_available_tickets(queryset, name, value):
        if value:
            return queryset.filter(tickets_available__gt=0)
        return queryset.filter(tickets_available__lte=0)


class OrderFilter(django_filters.FilterSet):
    created = django_filters.IsoDateTimeFromToRangeFilter(
        field_name="created_at",
    )

    class Meta:
        model = Order
        fields = ("created",)
