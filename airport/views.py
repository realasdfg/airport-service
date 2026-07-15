from django.db.models import F, Count
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
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

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "name",
                type=OpenApiTypes.STR,
                description="Filter by city name (ex. ?name=Kyiv)",
            ),
            OpenApiParameter(
                "country",
                type=OpenApiTypes.STR,
                description="Filter by country (ex. ?country=Ukraine)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


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

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "cities",
                type={"type": "list", "items": {"type": "number"}},
                description="Filter by cities ids (ex. ?cities=2,5,6)",
            ),
            OpenApiParameter(
                "country",
                type=OpenApiTypes.STR,
                description="Filter by airport country (ex. ?country=Ukraine)",
            ),
            OpenApiParameter(
                "iata_code",
                type=OpenApiTypes.STR,
                description="Filter by airport IATA code (ex. ?iata_code=KBP)",
            ),
            OpenApiParameter(
                "name",
                type=OpenApiTypes.STR,
                description="Filter by airport name (ex. ?name=Boryspil)",
            ),

        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class RouteViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
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

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "destination",
                type=OpenApiTypes.INT,
                description="Filter by destination airport id "
                            "(ex. ?destination=1)",
            ),
            OpenApiParameter(
                "destination_iata",
                type=OpenApiTypes.STR,
                description="Filter by destination airport IATA code "
                            "(ex. ?destination_iata=KBP)",
            ),
            OpenApiParameter(
                "source",
                type=OpenApiTypes.INT,
                description="Filter by source airport id (ex. ?source=1)",
            ),
            OpenApiParameter(
                "source_iata",
                type=OpenApiTypes.STR,
                description="Filter by source airport IATA code "
                            "(ex. ?source_iata=KBP)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class AirplaneTypeViewSet(viewsets.ModelViewSet):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer
    filterset_class = AirplaneTypeFilter

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "name",
                type=OpenApiTypes.STR,
                description="Filter by airplane type name "
                            "(ex. ?name=regional)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


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

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "airplane_types",
                type={"type": "list", "items": {"type": "number"}},
                description="Filter by AirplaneTypes ids "
                            "(ex. ?airplane_types=2,5,6)",
            ),
            OpenApiParameter(
                "capacity_max",
                type=OpenApiTypes.INT,
                description="Filter by max airplane capacity "
                            "(ex. ?capacity_max=150)",
            ),
            OpenApiParameter(
                "capacity_min",
                type=OpenApiTypes.INT,
                description="Filter by min airplane capacity "
                            "(ex. ?capacity_min=150)",
            ),
            OpenApiParameter(
                "name",
                type=OpenApiTypes.STR,
                description="Filter by airplane name (ex. ?name=boeing)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class PositionViewSet(viewsets.ModelViewSet):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    permission_classes = (IsAdminUser,)
    filterset_class = PositionFilter

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "name",
                type=OpenApiTypes.STR,
                description="Filter by crew position name "
                            "(ex. ?name=commander)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


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

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "positions",
                type={"type": "list", "items": {"type": "number"}},
                description="Filter by positions ids (ex. ?positions=2,5,6)",
            ),
            OpenApiParameter(
                "first_name",
                type=OpenApiTypes.STR,
                description="Filter by first name (ex. ?first_name=Bob)",
            ),
            OpenApiParameter(
                "last_name",
                type=OpenApiTypes.STR,
                description="Filter by last name (ex. ?last_name=Big)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


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

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "crews",
                type={"type": "list", "items": {"type": "number"}},
                description="Filter by crews ids (ex. ?crews=2,5,6)",
            ),
            OpenApiParameter(
                "route",
                type=OpenApiTypes.INT,
                description="Filter by route id (ex. ?route=1)",
            ),
            OpenApiParameter(
                "has_available_tickets",
                type=OpenApiTypes.BOOL,
                description="Filter by has available tickets "
                            "(ex. ?has_available_tickets=true)",
            ),
            OpenApiParameter(
                "arrival_time_after",
                type=OpenApiTypes.DATETIME,
                description="Filter by after arrival datetime "
                            "in ISO format (ex. ?arrival_time_after="
                            "2026-07-15T03:20:00Z)",
            ),
            OpenApiParameter(
                "arrival_time_before",
                type=OpenApiTypes.DATETIME,
                description="Filter by before arrival datetime "
                            "in ISO format (ex. ?arrival_time_before="
                            "2026-07-15T03:20:00Z)",
            ),
            OpenApiParameter(
                "departure_time_after",
                type=OpenApiTypes.DATETIME,
                description="Filter by after departure datetime "
                            "in ISO format (ex. ?departure_time_after="
                            "2026-07-15T03:20:00Z)",
            ),
            OpenApiParameter(
                "departure_time_before",
                type=OpenApiTypes.DATETIME,
                description="Filter by before departure datetime "
                            "in ISO format (ex. ?departure_time_before="
                            "2026-07-15T03:20:00Z)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


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

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "created_after",
                type=OpenApiTypes.DATETIME,
                description="Filter by after order created "
                            "datetime in ISO format "
                            "(ex. ?created_after=2026-07-15T03:20:00Z)",
            ),
            OpenApiParameter(
                "created_before",
                type=OpenApiTypes.DATETIME,
                description="Filter by before order created "
                            "datetime in ISO format "
                            "(ex. ?created_before=2026-07-15T03:20:00Z)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
