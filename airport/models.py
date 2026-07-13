from math import radians, sin, cos, sqrt, atan2

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Q, F


class CoordinatesMixin(models.Model):
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[
            MinValueValidator(-90),
            MaxValueValidator(90),
        ],
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[
            MinValueValidator(-180),
            MaxValueValidator(180),
        ],
    )

    class Meta:
        abstract = True


class City(CoordinatesMixin, models.Model):
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = "cities"

    def __str__(self):
        return (f"{self.name}, {self.country} "
                f"({self.latitude}, {self.longitude})")


class Airport(CoordinatesMixin, models.Model):
    name = models.CharField(max_length=255)
    iata_code = models.CharField(max_length=3, unique=True)
    closest_big_city = models.ForeignKey(
        City,
        on_delete=models.PROTECT,
        related_name="airports"
    )

    def __str__(self):
        return self.name


class Route(models.Model):
    source = models.ForeignKey(
        Airport,
        on_delete=models.CASCADE,
        related_name="routes_from"
    )
    destination = models.ForeignKey(
        Airport,
        on_delete=models.CASCADE,
        related_name="routes_to"
    )
    distance = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        editable=False
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source", "destination"],
                name="unique_source_destination_route"
            ),
            models.CheckConstraint(
                condition=~Q(source=F("destination")),
                name="source_not_equal_destination_route",
            ),
        ]

    @staticmethod
    def validate_source_destination(source, destination, error_to_raise):
        if source and destination and source == destination:
            raise error_to_raise(
                "Source and destination airports cannot be the same."
            )

    @staticmethod
    def calculate_distance(lat1, lon1, lat2, lon2):
        earth_r = 6371

        lat1, lon1 = radians(float(lat1)), radians(float(lon1))
        lat2, lon2 = radians(float(lat2)), radians(float(lon2))
        d_lat = lat2 - lat1
        d_lon = lon2 - lon1

        a = (sin(d_lat / 2) ** 2
             + cos(lat1) * cos(lat2) * sin(d_lon / 2) ** 2)
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return round(earth_r * c, 2)

    def save(self, *args, **kwargs):
        self.distance = self.calculate_distance(
            self.source.latitude,
            self.source.longitude,
            self.destination.latitude,
            self.destination.longitude,
        )
        super().save(*args, **kwargs)

    def clean(self):
        Route.validate_source_destination(
            self.source,
            self.destination,
            ValidationError
        )

    def __str__(self):
        return self.source.iata_code + " -> " + self.destination.iata_code


class AirplaneType(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Airplane(models.Model):
    name = models.CharField(max_length=255)
    rows = models.IntegerField()
    seats_in_row = models.IntegerField()
    airplane_type = models.ForeignKey(
        AirplaneType,
        on_delete=models.CASCADE,
        related_name="airplanes"
    )

    @property
    def capacity(self) -> int:
        return self.rows * self.seats_in_row

    def __str__(self):
        return self.name


class Crew(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.full_name


class Flight(models.Model):
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name="flights"
    )
    airplane = models.ForeignKey(
        Airplane,
        on_delete=models.CASCADE,
        related_name="flights"
    )
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    crew = models.ManyToManyField(Crew, related_name="flights")

    def __str__(self):
        return f"{self.route} - {self.airplane}"


class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} - {self.created_at}"


class Ticket(models.Model):
    row = models.IntegerField()
    seat = models.IntegerField()
    flight = models.ForeignKey(
        Flight,
        on_delete=models.CASCADE,
        related_name="tickets"
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="tickets"
    )

    def __str__(self):
        return (
            f"{self.flight} (row: {self.row}, seat: {self.seat})"
        )

    class Meta:
        unique_together = ("flight", "row", "seat")
        ordering = ["row", "seat"]
