from rest_framework import serializers

from airport.models import (
    City,
    Airport,
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
    closest_big_city = CitySerializer(read_only=True)
