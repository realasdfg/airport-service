from rest_framework import viewsets

from airport.models import (
    City,
    Airport,
)
from airport.serializers import (
    CitySerializer,
    AirportSerializer,
    AirportListSerializer,
)


class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer


class AirportViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects.all()

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return AirportListSerializer

        return AirportSerializer

    def get_queryset(self):
        queryset = self.queryset
        if self.action in ["list", "retrieve"]:
            queryset = queryset.select_related("closest_big_city")
        return queryset
