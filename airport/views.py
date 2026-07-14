from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser

from airport.models import (
    City,
    Airport,
    Route,
    AirplaneType,
    Airplane,
    Position,
    Crew,
    Flight,
)
from airport.serializers import (
    CitySerializer,
    AirportSerializer,
    AirportListSerializer,
    AirportDetailSerializer,
    RouteSerializer,
    RouteListSerializer,
    AirplaneTypeSerializer,
    AirplaneSerializer,
    AirplaneListSerializer,
    AirplaneDetailSerializer,
    PositionSerializer,
    CrewSerializer,
    CrewListSerializer,
    CrewDetailSerializer,
    FlightSerializer,
    FlightListSerializer,
    FlightDetailSerializer,
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


class AirplaneTypeViewSet(viewsets.ModelViewSet):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer


class AirplaneViewSet(viewsets.ModelViewSet):
    queryset = Airplane.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return AirplaneListSerializer
        if self.action == "retrieve":
            return AirplaneDetailSerializer

        return AirplaneSerializer

    def get_queryset(self):
        queryset = self.queryset

        if self.action in ["list", "retrieve"]:
            queryset = queryset.select_related("airplane_type")

        return queryset


class PositionViewSet(viewsets.ModelViewSet):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    permission_classes = (IsAdminUser,)


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    permission_classes = (IsAdminUser,)

    def get_serializer_class(self):
        if self.action == "list":
            return CrewListSerializer
        if self.action == "retrieve":
            return CrewDetailSerializer

        return CrewSerializer

    def get_queryset(self):
        queryset = self.queryset

        if self.action in ["list", "retrieve"]:
            queryset = queryset.select_related("position")

        return queryset


class FlightViewSet(viewsets.ModelViewSet):
    queryset = Flight.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer
        if self.action == "retrieve":
            return FlightDetailSerializer

        return FlightSerializer

    def get_queryset(self):
        queryset = self.queryset

        if self.action == "list":
            queryset = (
                queryset
                .select_related(
                    "route__source",
                    "route__destination",
                    "airplane"
                )
                .prefetch_related("crew")
            )
        if self.action == "retrieve":
            queryset = (
                queryset
                .select_related(
                    "route__source__closest_big_city",
                    "route__destination__closest_big_city",
                    "airplane__airplane_type"
                )
                .prefetch_related("crew__position")
            )

        return queryset
