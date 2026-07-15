from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from airport.models import Route
from airport.serializers import RouteListSerializer
from airport.tests.test_airports_endpoint import sample_airport
from airport.tests.test_cities_endpoint import sample_city

User = get_user_model()

URL = reverse("airport:route-list")


def detail_url(route_id):
    return reverse("airport:route-detail", args=[route_id])


def sample_route(source=None, destination=None, **params):
    if not source:
        source = sample_airport()
    if not destination:
        destination = sample_airport(iata_code="BBB")
    defaults = {
        "source": source,
        "destination": destination,
    }
    defaults.update(params)

    return Route.objects.create(**defaults)


class UnauthenticatedRoutesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client: APIClient = APIClient()

    def test_auth_required(self):
        res = self.client.get(URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedRoutesTests(TestCase):
    def setUp(self):
        self.client: APIClient = APIClient()
        self.user = get_user_model().objects.create_user(
            "user@user.com", "password"
        )
        self.client.force_authenticate(self.user)

    def test_route_list(self):
        city = sample_city()
        airport1 = sample_airport(
            closest_big_city=city,
            name="Sample airport2",
            iata_code="CCC",
        )
        airport2 = sample_airport(
            closest_big_city=city,
            name="Sample airport2",
            iata_code="DDD",
        )
        sample_route()
        sample_route(source=airport2, destination=airport1)
        sample_route(source=airport1, destination=airport2)
        serializer = RouteListSerializer(Route.objects.all(), many=True)

        res = self.client.get(URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_route_list_filter_by_source(self):
        city = sample_city()
        airport1 = sample_airport(city, iata_code="CCC")
        airport2 = sample_airport(
            closest_big_city=city,
            name="Sample airport2",
            iata_code="DDD",
        )
        route1 = sample_route(source=airport1, destination=airport2)
        route2 = sample_route(source=airport2, destination=airport1)
        serializer1 = RouteListSerializer(route1)
        serializer2 = RouteListSerializer(route2)

        res = self.client.get(URL, {"source": airport1.id})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer1.data, res.data["results"])
        self.assertNotIn(serializer2.data, res.data["results"])

        res = self.client.get(URL, {"source_iata": airport1.iata_code})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer1.data, res.data["results"])
        self.assertNotIn(serializer2.data, res.data["results"])

    def test_route_detail(self):
        route = sample_route()
        serializer = RouteListSerializer(route)

        res = self.client.get(detail_url(route.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_route_create_forbidden(self):
        city = sample_city()
        source = sample_airport(closest_big_city=city)
        destination = sample_airport(closest_big_city=city, iata_code="BBB")
        data = {
            "source": source.id,
            "destination": destination.id,
        }
        res = self.client.post(URL, data)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_route_update_forbidden(self):
        route = sample_route()
        res = self.client.patch(
            detail_url(route.id),
            {"destination": 2}
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_route_delete_forbidden(self):
        route = sample_route()
        res = self.client.delete(detail_url(route.id))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminRoutesTests(TestCase):
    def setUp(self):
        self.client: APIClient = APIClient()
        self.user = get_user_model().objects.create_superuser(
            "admin@user.com", "password"
        )
        self.client.force_authenticate(self.user)

    def test_route_create(self):
        city = sample_city()
        source = sample_airport(closest_big_city=city)
        destination = sample_airport(closest_big_city=city, iata_code="BBB")
        data = {
            "source": source.id,
            "destination": destination.id,
        }
        res = self.client.post(URL, data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Route.objects.count(), 1)
        self.assertEqual(Route.objects.first().source, source)
        self.assertEqual(Route.objects.first().destination, destination)

    def test_route_update_not_allowed(self):
        route = sample_route()
        new_dest_airport = sample_airport(iata_code="CCC")
        res = self.client.patch(
            detail_url(route.id),
            {"destination": new_dest_airport.id}
        )
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_route_delete(self):
        route = sample_route()
        res = self.client.delete(detail_url(route.id))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Route.objects.count(), 0)
