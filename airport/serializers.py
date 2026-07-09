from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from airport.models import (
    City,
    Airport,
    Route,
    AirplaneType,
    Airplane,
    Crew,
    Flight,
)


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ("id", "name",)


class AirportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = ("id", "name", "closest_big_city",)


class AirportListSerializer(AirportSerializer):
    closest_big_city = serializers.StringRelatedField(
        read_only=True,
        source="closest_big_city.name",
    )


class AirportDetailSerializer(AirportSerializer):
    closest_big_city = CitySerializer(read_only=True)


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance",)

    def validate(self, attrs):
        data = super(RouteSerializer, self).validate(attrs=attrs)
        Route.validate_source_destination(
            attrs["source"],
            attrs["destination"],
            ValidationError
        )
        return data


class RouteListSerializer(serializers.ModelSerializer):
    source = AirportListSerializer(read_only=True)
    destination = AirportListSerializer(read_only=True)

    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance",)


class AirplaneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirplaneType
        fields = ("id", "name",)


class AirplaneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airplane
        fields = (
            "id",
            "name",
            "rows",
            "seats_in_row",
            "airplane_type",
            "capacity",
        )


class AirplaneListSerializer(AirplaneSerializer):
    airplane_type = serializers.StringRelatedField(
        read_only=True,
        source="airplane_type.name",
    )


class AirplaneDetailSerializer(AirplaneSerializer):
    airplane_type = AirplaneTypeSerializer(read_only=True)


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ("id", "first_name", "last_name",)


class FlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flight
        fields = (
            "id",
            "route",
            "airplane",
            "departure_time",
            "arrival_time",
            "crew",
        )


class FlightListSerializer(FlightSerializer):
    route = serializers.StringRelatedField(
        read_only=True,
        source="route.__str__"
    )
    airplane = serializers.StringRelatedField(
        read_only=True,
        source="airplane.name"
    )
    crew = serializers.SlugRelatedField(
        read_only=True,
        many=True,
        slug_field="full_name",
    )


class FlightDetailSerializer(FlightListSerializer):
    route = RouteListSerializer(read_only=True)
    airplane = AirplaneListSerializer(read_only=True)
