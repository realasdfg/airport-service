from datetime import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from airport.models import Flight
from airport.serializers import FlightListSerializer, FlightDetailSerializer
from airport.tests.test_airplane_types_endpoint import sample_airplane_type
from airport.tests.test_airplanes_endpoint import sample_airplane
from airport.tests.test_crews_endpoint import sample_crew
from airport.tests.test_positions_endpoint import sample_position
from airport.tests.test_routes_endpoint import sample_route
from airport.views import FlightViewSet

User = get_user_model()

URL = reverse("airport:flight-list")


def detail_url(flight_id):
    return reverse("airport:flight-detail", args=[flight_id])


def sample_flight(airplane=None, crews=None, route=None, **params):
    if not airplane:
        airplane = sample_airplane()
    if not route:
        route = sample_route()

    defaults = {
        "route": route,
        "airplane": airplane,
        "departure_time": "2026-07-16T15:30Z",
        "arrival_time": "2026-07-16T17:00Z",
    }
    defaults.update(params)
    flight = Flight.objects.create(**defaults)

    if not crews:
        pos = sample_position()
        crews = [sample_crew(pos), sample_crew(pos)]
    flight.crew.add(*crews)
    return flight


class UnauthenticatedFlightsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client: APIClient = APIClient()

    def test_auth_required(self):
        res = self.client.get(URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedFlightsTests(TestCase):
    def setUp(self):
        self.client: APIClient = APIClient()
        self.user = User.objects.create_user(
            "user@user.com", "password"
        )
        self.client.force_authenticate(self.user)

        view = FlightViewSet()
        view.action = "list"
        self.flight_list_qs = view.get_queryset()
        view.action = "retrieve"
        self.flight_retrieve_qs = view.get_queryset()

    def test_flight_list(self):
        airplane = sample_airplane()
        pos = sample_position()
        crews = [sample_crew(pos), sample_crew(pos)]
        sample_flight(airplane, crews)
        sample_flight(airplane, crews)

        serializer = FlightListSerializer(self.flight_list_qs, many=True)
        res = self.client.get(URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_flight_list_filter_by_departure_and_arrival_times(self):
        airplane = sample_airplane()
        pos = sample_position()
        crews = [sample_crew(pos), sample_crew(pos)]
        flight1 = sample_flight(airplane, crews,
                                departure_time="2026-07-18T15:30Z",
                                arrival_time="2026-07-18T17:00Z")
        flight2 = sample_flight(airplane, crews,
                                departure_time="2026-07-20T15:30Z",
                                arrival_time="2026-07-20T17:00Z")
        flight3 = sample_flight(airplane, crews,
                                departure_time="2026-07-22T15:30Z",
                                arrival_time="2026-07-22T17:00Z")
        serializer1 = FlightListSerializer(self.flight_list_qs.get(pk=flight1.pk))
        serializer2 = FlightListSerializer(self.flight_list_qs.get(pk=flight2.pk))
        serializer3 = FlightListSerializer(self.flight_list_qs.get(pk=flight3.pk))

        res = self.client.get(
            URL,
            {
                "departure_time_before": "2026-07-21",
                "departure_time_after": "2026-07-19",
            }
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn(serializer1.data, res.data["results"])
        self.assertIn(serializer2.data, res.data["results"])
        self.assertNotIn(serializer3.data, res.data["results"])

        res = self.client.get(
            URL,
            {
                "arrival_time_before": "2026-07-21",
                "arrival_time_after": "2026-07-19",
            }
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn(serializer1.data, res.data["results"])
        self.assertIn(serializer2.data, res.data["results"])
        self.assertNotIn(serializer3.data, res.data["results"])

    def test_flight_list_filter_by_route_id(self):
        airplane = sample_airplane()
        pos = sample_position()
        crews = [sample_crew(pos), sample_crew(pos)]
        route1 = sample_route()
        flight1 = sample_flight(airplane, crews, route1)
        flight2 = sample_flight(airplane, crews)
        serializer1 = FlightListSerializer(self.flight_list_qs.get(pk=flight1.pk))
        serializer2 = FlightListSerializer(self.flight_list_qs.get(pk=flight2.pk))

        res = self.client.get(URL, {"route": route1.id})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer1.data, res.data["results"])
        self.assertNotIn(serializer2.data, res.data["results"])

    def test_flight_list_filter_by_crews_ids(self):
        airplane = sample_airplane()
        pos = sample_position()
        crew1 = sample_crew(pos)
        crew2 = sample_crew(pos)
        crew3 = sample_crew(pos)
        flight1 = sample_flight(airplane, [crew1])
        flight2 = sample_flight(airplane, [crew2])
        flight3 = sample_flight(airplane, [crew3])
        serializer1 = FlightListSerializer(self.flight_list_qs.get(pk=flight1.pk))
        serializer2 = FlightListSerializer(self.flight_list_qs.get(pk=flight2.pk))
        serializer3 = FlightListSerializer(self.flight_list_qs.get(pk=flight3.pk))

        res = self.client.get(URL, {"crews": f"{crew1.id},{crew2.id}"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer1.data, res.data["results"])
        self.assertIn(serializer2.data, res.data["results"])
        self.assertNotIn(serializer3.data, res.data["results"])

    def test_flight_list_filter_by_has_available_tickets(self):
        airplane_type = sample_airplane_type()
        airplane1 = sample_airplane(airplane_type)
        airplane2 = sample_airplane(airplane_type, rows=0, seats_in_row=0)
        pos = sample_position()
        crews = [sample_crew(pos), sample_crew(pos)]
        flight1 = sample_flight(airplane1, crews)
        flight2 = sample_flight(airplane2, crews)
        serializer1 = FlightListSerializer(self.flight_list_qs.get(pk=flight1.pk))
        serializer2 = FlightListSerializer(self.flight_list_qs.get(pk=flight2.pk))

        res = self.client.get(URL, {"has_available_tickets": "false"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn(serializer1.data, res.data["results"])
        self.assertIn(serializer2.data, res.data["results"])

        res = self.client.get(URL, {"has_available_tickets": "true"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer1.data, res.data["results"])
        self.assertNotIn(serializer2.data, res.data["results"])

    def test_flight_detail(self):
        flight = sample_flight()
        serializer = FlightDetailSerializer(
            self.flight_retrieve_qs.get(pk=flight.pk)
        )

        res = self.client.get(detail_url(flight.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_flight_create_forbidden(self):
        airplane = sample_airplane()
        route = sample_route()
        data = {
            "route": route.id,
            "airplane": airplane.id,
            "departure_time": "2026-07-16T15:30Z",
            "arrival_time": "2026-07-16T17:00Z",
        }
        res = self.client.post(URL, data)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_flight_update_forbidden(self):
        flight = sample_flight()
        res = self.client.patch(
            detail_url(flight.id),
            {"departure_time": "2027-10-10T15:30Z"}
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_flight_delete_forbidden(self):
        flight = sample_flight()
        res = self.client.delete(detail_url(flight.id))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminFlightsTests(TestCase):
    def setUp(self):
        self.client: APIClient = APIClient()
        self.user = User.objects.create_superuser(
            "admin@user.com", "password"
        )
        self.client.force_authenticate(self.user)

    def test_flight_create(self):
        airplane = sample_airplane()
        route = sample_route()
        pos = sample_position()
        crew1 = sample_crew(pos)
        crew2 = sample_crew(pos)
        data = {
            "route": route.id,
            "airplane": airplane.id,
            "departure_time": "2026-07-16T15:30Z",
            "arrival_time": "2026-07-16T17:00Z",
            "crew": [crew1.id, crew2.id],
        }
        res = self.client.post(URL, data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Flight.objects.count(), 1)
        self.assertEqual(Flight.objects.first().route, route)
        self.assertEqual(Flight.objects.first().airplane, airplane)
        self.assertEqual(
            Flight.objects.first().departure_time,
            datetime.fromisoformat(data["departure_time"])
        )
        self.assertEqual(
            Flight.objects.first().arrival_time,
            datetime.fromisoformat(data["arrival_time"])
        )
        self.assertEqual(
            list(Flight.objects.first().crew.all()),
            [crew1, crew2]
        )

    def test_flight_delete(self):
        flight = sample_flight()
        res = self.client.delete(detail_url(flight.id))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Flight.objects.count(), 0)
