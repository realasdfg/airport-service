from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from airport.models import Airport
from airport.serializers import AirportListSerializer, AirportDetailSerializer
from airport.tests.test_cities_endpoint import sample_city

User = get_user_model()

URL = reverse("airport:airport-list")


def detail_url(airport_id):
    return reverse("airport:airport-detail", args=[airport_id])


def sample_airport(closest_big_city=None, **params):
    if not closest_big_city:
        closest_big_city = sample_city()
    defaults = {
        "name": "Sample airport",
        "iata_code": "AAA",
        "closest_big_city": closest_big_city,
        "latitude": "20.5555",
        "longitude": "20.5555",
    }
    defaults.update(params)

    return Airport.objects.create(**defaults)


class UnauthenticatedAirportsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client: APIClient = APIClient()

    def test_auth_required(self):
        res = self.client.get(URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedAirportsTests(TestCase):
    def setUp(self):
        self.client: APIClient = APIClient()
        self.user = User.objects.create_user(
            "user@user.com", "password"
        )
        self.client.force_authenticate(self.user)

    def test_airport_list(self):
        city = sample_city()
        sample_airport(city)
        sample_airport(
            closest_big_city=city,
            name="Sample airport2",
            iata_code="BBB",
        )
        serializer = AirportListSerializer(Airport.objects.all(), many=True)

        res = self.client.get(URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_airport_list_filter_by_country(self):
        city1 = sample_city()
        city2 = sample_city(country="Different country")
        airport1 = sample_airport(city1)
        airport2 = sample_airport(closest_big_city=city1, iata_code="BBB")
        airport3 = sample_airport(closest_big_city=city2, iata_code="CCC")
        serializer1 = AirportListSerializer(airport1)
        serializer2 = AirportListSerializer(airport2)
        serializer3 = AirportListSerializer(airport3)

        res = self.client.get(URL, {"country": "sample"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer1.data, res.data["results"])
        self.assertIn(serializer2.data, res.data["results"])
        self.assertNotIn(serializer3.data, res.data["results"])

    def test_airport_list_filter_by_iata_code(self):
        city = sample_city()
        airport1 = sample_airport(city)
        airport2 = sample_airport(closest_big_city=city, iata_code="BBB")
        serializer1 = AirportListSerializer(airport1)
        serializer2 = AirportListSerializer(airport2)

        res = self.client.get(URL, {"iata_code": "aaa"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer1.data, res.data["results"])
        self.assertNotIn(serializer2.data, res.data["results"])

    def test_airport_list_filter_by_name(self):
        city = sample_city()
        airport1 = sample_airport(city)
        airport2 = sample_airport(
            closest_big_city=city,
            iata_code="BBB",
            name="Different airport",
        )
        serializer1 = AirportListSerializer(airport1)
        serializer2 = AirportListSerializer(airport2)

        res = self.client.get(URL, {"name": "sample"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer1.data, res.data["results"])
        self.assertNotIn(serializer2.data, res.data["results"])

    def test_airport_list_filter_by_cities_ids(self):
        city1 = sample_city()
        city2 = sample_city()
        city3 = sample_city()
        airport1 = sample_airport(city1)
        airport2 = sample_airport(closest_big_city=city2, iata_code="BBB")
        airport3 = sample_airport(closest_big_city=city3, iata_code="CCC")
        serializer1 = AirportListSerializer(airport1)
        serializer2 = AirportListSerializer(airport2)
        serializer3 = AirportListSerializer(airport3)

        res = self.client.get(URL, {"cities": f"{city1.id},{city2.id}"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer1.data, res.data["results"])
        self.assertIn(serializer2.data, res.data["results"])
        self.assertNotIn(serializer3.data, res.data["results"])

    def test_airport_detail(self):
        airport = sample_airport()
        serializer = AirportDetailSerializer(airport)

        res = self.client.get(detail_url(airport.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_airport_create_forbidden(self):
        city = sample_city()
        data = {
            "name": "Sample airport",
            "iata_code": "AAA",
            "closest_big_city": city.id,
            "latitude": "20.5555",
            "longitude": "20.5555",
        }
        res = self.client.post(URL, data)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_airport_update_forbidden(self):
        airport = sample_airport()
        res = self.client.patch(
            detail_url(airport.id),
            {"name": "Changed airport"}
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_airport_delete_forbidden(self):
        airport = sample_airport()
        res = self.client.delete(detail_url(airport.id))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminAirportsTests(TestCase):
    def setUp(self):
        self.client: APIClient = APIClient()
        self.user = User.objects.create_superuser(
            "admin@user.com", "password"
        )
        self.client.force_authenticate(self.user)

    def test_airport_create(self):
        city = sample_city()
        data = {
            "name": "Sample airport",
            "iata_code": "AAA",
            "closest_big_city": city.id,
            "latitude": "20.5555",
            "longitude": "20.5555",
        }
        res = self.client.post(URL, data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Airport.objects.count(), 1)
        self.assertEqual(Airport.objects.first().name, "Sample airport")

    def test_airport_update(self):
        airport = sample_airport()
        city = sample_city()
        data = {
            "name": "Changed airport",
            "iata_code": "BBB",
            "closest_big_city": city.id,
            "latitude": "50.5555",
            "longitude": "50.5555",
        }
        res = self.client.put(detail_url(airport.id), data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(Airport.objects.first().name, "Changed airport")
        self.assertEqual(Airport.objects.first().iata_code, "BBB")
        self.assertEqual(Airport.objects.first().closest_big_city, city)
        self.assertEqual(Airport.objects.first().latitude, Decimal("50.5555"))
        self.assertEqual(Airport.objects.first().longitude, Decimal("50.5555"))

    def test_airport_delete(self):
        airport = sample_airport()
        res = self.client.delete(detail_url(airport.id))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Airport.objects.count(), 0)
