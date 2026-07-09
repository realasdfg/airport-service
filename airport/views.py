from rest_framework import viewsets

from airport.models import (
    City,
    Airport,
    Route,
)
from airport.serializers import (
    CitySerializer,
    AirportSerializer,
    AirportListSerializer,
    AirportDetailSerializer,
    RouteSerializer,
    RouteListSerializer,
)


class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer


class AirportViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return AirportListSerializer
        if self.action == "retrieve":
            return AirportDetailSerializer

        return AirportSerializer

    def get_queryset(self):
        queryset = self.queryset

        if self.action in ["list", "retrieve"]:
            queryset = queryset.select_related("closest_big_city")

        return queryset


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return RouteListSerializer

        return RouteSerializer

    def get_queryset(self):
        queryset = self.queryset

        if self.action in ["list", "retrieve"]:
            queryset = queryset.select_related(
                "source__closest_big_city",
                "destination__closest_big_city"
            )

        return queryset
