from django.db.models import F, Count
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from airport.filters import (
    CityFilter,
    AirportFilter,
    RouteFilter,
    AirplaneTypeFilter,
    AirplaneFilter,
    PositionFilter,
    CrewFilter,
    FlightFilter,
    OrderFilter,
)
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
from airport.serializers import (
    CitySerializer,
    AirportSerializer,
    AirportListSerializer,
    AirportDetailSerializer,
    RouteSerializer,
    RouteListSerializer,
    AirplaneTypeSerializer,
    AirplaneSerializer,
    AirplaneImageSerializer,
    AirplaneListSerializer,
    AirplaneDetailSerializer,
    PositionSerializer,
    CrewSerializer,
    CrewListSerializer,
    CrewDetailSerializer,
    FlightSerializer,
    FlightListSerializer,
    FlightDetailSerializer,
    OrderSerializer,
    OrderListSerializer,
    OrderDetailSerializer,
)


class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    filterset_class = CityFilter


class AirportViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects.all()
    filterset_class = AirportFilter

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
    filterset_class = RouteFilter

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
    filterset_class = AirplaneTypeFilter


class AirplaneViewSet(viewsets.ModelViewSet):
    queryset = Airplane.objects.all()
    filterset_class = AirplaneFilter

    def get_serializer_class(self):
        if self.action == "list":
            return AirplaneListSerializer
        if self.action == "retrieve":
            return AirplaneDetailSerializer
        if self.action == "upload_image":
            return AirplaneImageSerializer

        return AirplaneSerializer

    def get_queryset(self):
        queryset = self.queryset

        if self.action in ["list", "retrieve"]:
            queryset = queryset.select_related("airplane_type")

        return queryset

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
        permission_classes=[IsAdminUser],
    )
    def upload_image(self, request, pk=None):
        airplane = self.get_object()
        serializer = self.get_serializer(airplane, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PositionViewSet(viewsets.ModelViewSet):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    permission_classes = (IsAdminUser,)
    filterset_class = PositionFilter


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    permission_classes = (IsAdminUser,)
    filterset_class = CrewFilter

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
    filterset_class = FlightFilter

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer
        if self.action == "retrieve":
            return FlightDetailSerializer

        return FlightSerializer

    def get_queryset(self):
        queryset = self.queryset

        queryset = queryset.annotate(
            tickets_available=(
                    F("airplane__rows") * F("airplane__seats_in_row")
                    - Count("tickets")
            )
        )

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


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    GenericViewSet,
):
    queryset = Order.objects.all()
    permission_classes = (IsAuthenticated,)
    filterset_class = OrderFilter

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)

        if self.action == "list":
            queryset = queryset.prefetch_related(
                "tickets__flight__crew",
                "tickets__flight__airplane",
                "tickets__flight__route__source",
                "tickets__flight__route__destination",
            )

        if self.action == "retrieve":
            queryset = queryset.prefetch_related(
                "tickets__flight__crew__position",
                "tickets__flight__airplane__airplane_type",
                "tickets__flight__route__source__closest_big_city",
                "tickets__flight__route__destination__closest_big_city",
            )

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        if self.action == "retrieve":
            return OrderDetailSerializer

        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
