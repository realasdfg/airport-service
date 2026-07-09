from rest_framework import serializers

from airport.models import (
    City,
    Airport,
    Route,
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


class RouteListSerializer(serializers.ModelSerializer):
    source = AirportListSerializer(read_only=True)
    destination = AirportListSerializer(read_only=True)

    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance",)
