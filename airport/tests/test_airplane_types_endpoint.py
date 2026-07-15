from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from airport.models import AirplaneType
from airport.serializers import AirplaneTypeSerializer

User = get_user_model()

URL = reverse("airport:airplanetype-list")


def detail_url(airplane_type_id):
    return reverse("airport:airplanetype-detail", args=[airplane_type_id])


def sample_airplane_type(**params):
    defaults = {"name": "Sample airplane type"}
    defaults.update(params)
    return AirplaneType.objects.create(**defaults)


class UnauthenticatedAirplaneTypesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client: APIClient = APIClient()

    def test_auth_required(self):
        res = self.client.get(URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedAirplaneTypesTests(TestCase):
    def setUp(self):
        self.client: APIClient = APIClient()
        self.user = get_user_model().objects.create_user(
            "user@user.com", "password"
        )
        self.client.force_authenticate(self.user)

    def test_airplane_type_list(self):
        sample_airplane_type()
        sample_airplane_type(name="Sample airplane type2")
        serializer = AirplaneTypeSerializer(AirplaneType.objects.all(),
                                            many=True)

        res = self.client.get(URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_airplane_type_list_filter_by_name(self):
        airplane_type1 = sample_airplane_type()
        airplane_type2 = sample_airplane_type(
            name="Sample airplane type2",
        )
        airplane_type3 = sample_airplane_type(
            name="Different airplane type",
        )
        serializer1 = AirplaneTypeSerializer(airplane_type1)
        serializer2 = AirplaneTypeSerializer(airplane_type2)
        serializer3 = AirplaneTypeSerializer(airplane_type3)

        res = self.client.get(URL, {"name": "sample"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer1.data, res.data["results"])
        self.assertIn(serializer2.data, res.data["results"])
        self.assertNotIn(serializer3.data, res.data["results"])

    def test_airplane_type_detail(self):
        airplane_type = sample_airplane_type()
        serializer = AirplaneTypeSerializer(airplane_type)

        res = self.client.get(detail_url(airplane_type.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_airplane_type_create_forbidden(self):
        res = self.client.post(URL, {"name": "Sample airplane type"})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_airplane_type_update_forbidden(self):
        airplane_type = sample_airplane_type()
        res = self.client.put(
            detail_url(airplane_type.id),
            {"name": "Changed airplane type"}
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_airplane_type_delete_forbidden(self):
        airplane_type = sample_airplane_type()
        res = self.client.delete(detail_url(airplane_type.id))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminAirplaneTypesTests(TestCase):
    def setUp(self):
        self.client: APIClient = APIClient()
        self.user = get_user_model().objects.create_superuser(
            "admin@user.com", "password"
        )
        self.client.force_authenticate(self.user)

    def test_airplane_type_create(self):
        data = {"name": "Sample airplane type"}
        res = self.client.post(URL, data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AirplaneType.objects.count(), 1)
        self.assertEqual(
            AirplaneType.objects.first().name,
            "Sample airplane type"
        )

    def test_airplane_type_update(self):
        airplane_type = sample_airplane_type()
        data = {"name": "Changed airplane type"}
        res = self.client.put(detail_url(airplane_type.id), data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(AirplaneType.objects.first().name, data["name"])

    def test_airplane_type_delete(self):
        airplane_type = sample_airplane_type()
        res = self.client.delete(detail_url(airplane_type.id))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(AirplaneType.objects.count(), 0)
