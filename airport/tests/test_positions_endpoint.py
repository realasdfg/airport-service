from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from airport.models import Position
from airport.serializers import PositionSerializer

User = get_user_model()

URL = reverse("airport:position-list")


def detail_url(position_id):
    return reverse("airport:position-detail", args=[position_id])


def sample_position(**params):
    defaults = {"name": "Sample position"}
    defaults.update(params)
    return Position.objects.create(**defaults)


class UnauthenticatedPositionsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client: APIClient = APIClient()

    def test_auth_required(self):
        res = self.client.get(URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedPositionsTests(TestCase):
    def setUp(self):
        self.client: APIClient = APIClient()
        self.user = get_user_model().objects.create_user(
            "user@user.com", "password"
        )
        self.client.force_authenticate(self.user)

    def test_position_list_forbidden(self):
        res = self.client.get(URL)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_position_detail_forbidden(self):
        position = sample_position()
        res = self.client.get(detail_url(position.id))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_position_create_forbidden(self):
        res = self.client.post(URL, {"name": "Sample position"})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_position_update_forbidden(self):
        position = sample_position()
        res = self.client.put(
            detail_url(position.id),
            {"name": "Sample position"}
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_position_delete_forbidden(self):
        position = sample_position()
        res = self.client.delete(detail_url(position.id))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminPositionsTests(TestCase):
    def setUp(self):
        self.client: APIClient = APIClient()
        self.user = get_user_model().objects.create_superuser(
            "admin@user.com", "password"
        )
        self.client.force_authenticate(self.user)

    def test_position_list(self):
        sample_position()
        sample_position(name="Sample position2")
        serializer = PositionSerializer(Position.objects.all(), many=True)

        res = self.client.get(URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_position_list_filter_by_name(self):
        position1 = sample_position()
        position2 = sample_position(name="Sample position2")
        position3 = sample_position(name="Different position")
        serializer1 = PositionSerializer(position1)
        serializer2 = PositionSerializer(position2)
        serializer3 = PositionSerializer(position3)

        res = self.client.get(URL, {"name": "sample"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer1.data, res.data["results"])
        self.assertIn(serializer2.data, res.data["results"])
        self.assertNotIn(serializer3.data, res.data["results"])

    def test_position_detail(self):
        position = sample_position()
        serializer = PositionSerializer(position)

        res = self.client.get(detail_url(position.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_position_create(self):
        data = {"name": "Sample position"}
        res = self.client.post(URL, data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Position.objects.count(), 1)
        self.assertEqual(Position.objects.first().name, data["name"])

    def test_position_update(self):
        position = sample_position()
        data = {"name": "Changed position"}
        res = self.client.put(detail_url(position.id), data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(Position.objects.first().name, data["name"])

    def test_position_delete(self):
        position = sample_position()
        res = self.client.delete(detail_url(position.id))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Position.objects.count(), 0)
