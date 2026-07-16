from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from airport.models import City
from airport.serializers import CitySerializer

User = get_user_model()

URL = reverse("airport:city-list")


def detail_url(city_id):
    return reverse("airport:city-detail", args=[city_id])


def sample_city(**params):
    defaults = {
        "name": "Sample city",
        "country": "Sample country",
        "latitude": "20.5555",
        "longitude": "20.5555",
    }
    defaults.update(params)

    return City.objects.create(**defaults)


class UnauthenticatedCitiesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client: APIClient = APIClient()

    def test_auth_required(self):
        res = self.client.get(URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedCitiesTests(TestCase):
    def setUp(self):
        self.client: APIClient = APIClient()
        self.user = User.objects.create_user(
            "user@user.com", "password"
        )
        self.client.force_authenticate(self.user)

    def test_city_list(self):
        sample_city()
        sample_city(
            name="Sample city2",
            country="Sample country2",
        )
        serializer = CitySerializer(City.objects.all(), many=True)

        res = self.client.get(URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_city_list_filter_by_name(self):
        city1 = sample_city()
        city2 = sample_city(
            name="Sample city2",
        )
        city3 = sample_city(
            name="Different city",
        )
        serializer1 = CitySerializer(city1)
        serializer2 = CitySerializer(city2)
        serializer3 = CitySerializer(city3)

        res = self.client.get(URL, {"name": "sample"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer1.data, res.data["results"])
        self.assertIn(serializer2.data, res.data["results"])
        self.assertNotIn(serializer3.data, res.data["results"])

    def test_city_list_filter_by_country(self):
        city1 = sample_city()
        city2 = sample_city(
            country="Sample country2",
        )
        city3 = sample_city(
            country="Different country",
        )
        serializer1 = CitySerializer(city1)
        serializer2 = CitySerializer(city2)
        serializer3 = CitySerializer(city3)

        res = self.client.get(URL, {"country": "sample"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer1.data, res.data["results"])
        self.assertIn(serializer2.data, res.data["results"])
        self.assertNotIn(serializer3.data, res.data["results"])

    def test_city_detail(self):
        city = sample_city()
        serializer = CitySerializer(city)

        res = self.client.get(detail_url(city.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_city_create_forbidden(self):
        res = self.client.post(
            URL,
            {"name": "Sample city",
             "country": "Sample country", }
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_city_update_forbidden(self):
        city = sample_city()
        res = self.client.put(
            detail_url(city.id),
            {"name": "Sample city",
             "country": "Sample country", }
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_city_delete_forbidden(self):
        city = sample_city()
        res = self.client.delete(detail_url(city.id))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminCitiesTests(TestCase):
    def setUp(self):
        self.client: APIClient = APIClient()
        self.user = User.objects.create_superuser(
            "admin@user.com", "password"
        )
        self.client.force_authenticate(self.user)

    def test_city_create(self):
        data = {
            "name": "Sample city",
            "country": "Sample country",
            "latitude": "20.5555",
            "longitude": "20.5555",
        }
        res = self.client.post(URL, data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(City.objects.count(), 1)
        self.assertEqual(City.objects.first().name, "Sample city")

    def test_city_update(self):
        city = sample_city()
        data = {
            "name": "Changed city",
            "country": "Changed country",
            "latitude": "50.5555",
            "longitude": "50.5555",
        }
        res = self.client.put(detail_url(city.id), data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(City.objects.first().name, "Changed city")
        self.assertEqual(City.objects.first().country, "Changed country")
        self.assertEqual(City.objects.first().latitude, Decimal("50.5555"))
        self.assertEqual(City.objects.first().longitude, Decimal("50.5555"))

    def test_city_delete(self):
        city = sample_city()
        res = self.client.delete(detail_url(city.id))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(City.objects.count(), 0)
