from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from airport.models import (
    City,
    Airport,
    Route,
    AirplaneType,
    Airplane,
    Position,
    Crew,
    Flight,
    Ticket,
    Order,
)


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ("id", "name", "country", "latitude", "longitude")


class AirportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = (
            "id",
            "name",
            "iata_code",
            "closest_big_city",
            "latitude",
            "longitude"
        )


class AirportListSerializer(AirportSerializer):
    closest_big_city = serializers.StringRelatedField(
        read_only=True,
        source="closest_big_city.__str__",
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


class AirplaneImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airplane
        fields = ("id", "image",)


class AirplaneListSerializer(AirplaneSerializer):
    airplane_type = serializers.StringRelatedField(
        read_only=True,
        source="airplane_type.name",
    )

    class Meta:
        model = Airplane
        fields = (
            "id",
            "name",
            "rows",
            "seats_in_row",
            "airplane_type",
            "capacity",
            "image",
        )


class AirplaneDetailSerializer(AirplaneSerializer):
    airplane_type = AirplaneTypeSerializer(read_only=True)

    class Meta:
        model = Airplane
        fields = (
            "id",
            "name",
            "rows",
            "seats_in_row",
            "airplane_type",
            "capacity",
            "image",
        )


class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ("id", "name",)


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ("id", "first_name", "last_name", "position")


class CrewListSerializer(CrewSerializer):
    position = serializers.StringRelatedField(
        read_only=True,
        source="position.name",
    )


class CrewDetailSerializer(CrewSerializer):
    position = PositionSerializer(read_only=True)


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

    def validate(self, attrs):
        data = super(FlightSerializer, self).validate(attrs=attrs)
        Flight.validate_times(
            attrs["departure_time"],
            attrs["arrival_time"],
            ValidationError
        )
        return data


class FlightListSerializer(FlightSerializer):
    route_source_iata_code = serializers.StringRelatedField(
        read_only=True,
        source="route.source.iata_code"
    )
    route_destination_iata_code = serializers.StringRelatedField(
        read_only=True,
        source="route.destination.iata_code"
    )
    airplane_name = serializers.StringRelatedField(
        read_only=True,
        source="airplane.name"
    )
    airplane_capacity = serializers.IntegerField(
        read_only=True,
        source="airplane.capacity"
    )
    tickets_available = serializers.IntegerField(read_only=True)
    crew = serializers.SlugRelatedField(
        read_only=True,
        many=True,
        slug_field="full_name",
    )

    class Meta:
        model = Flight
        fields = (
            "id",
            "route_source_iata_code",
            "route_destination_iata_code",
            "airplane_name",
            "airplane_capacity",
            "tickets_available",
            "departure_time",
            "arrival_time",
            "crew",
        )


class TicketSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        data = super(TicketSerializer, self).validate(attrs=attrs)
        Ticket.validate_ticket(
            attrs["row"],
            attrs["seat"],
            attrs["flight"].airplane,
            ValidationError
        )
        return data

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "flight")


class TicketSeatsSerializer(TicketSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat")


class FlightDetailSerializer(FlightSerializer):
    route = RouteListSerializer(read_only=True)
    airplane = AirplaneListSerializer(read_only=True)
    crew = CrewListSerializer(read_only=True, many=True)
    taken_places = TicketSeatsSerializer(
        source="tickets", many=True, read_only=True
    )

    class Meta:
        model = Flight
        fields = (
            "id",
            "route",
            "airplane",
            "departure_time",
            "arrival_time",
            "crew",
            "taken_places",
        )


class TicketListSerializer(TicketSerializer):
    flight = FlightListSerializer(read_only=True)


class TicketDetailSerializer(TicketSerializer):
    flight = FlightDetailSerializer(read_only=True)


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, allow_empty=False)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)
            return order


class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)


class OrderDetailSerializer(OrderSerializer):
    tickets = TicketDetailSerializer(many=True, read_only=True)
