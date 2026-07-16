import os
import tempfile

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from airport.models import Airplane
from airport.serializers import (
    AirplaneListSerializer,
    AirplaneDetailSerializer
)
from airport.tests.test_airplane_types_endpoint import sample_airplane_type

User = get_user_model()

URL = reverse("airport:airplane-list")


def detail_url(airplane_id):
    return reverse("airport:airplane-detail", args=[airplane_id])


def image_upload_url(airplane_id):
    return reverse("airport:airplane-upload-image", args=[airplane_id])


def sample_airplane(airplane_type=None, **params):
    if not airplane_type:
        airplane_type = sample_airplane_type()
    defaults = {
        "name": "Sample airplane",
        "rows": 30,
        "seats_in_row": 6,
        "airplane_type": airplane_type,
    }
    defaults.update(params)

    return Airplane.objects.create(**defaults)


class UnauthenticatedAirplanesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client: APIClient = APIClient()

    def test_auth_required(self):
        res = self.client.get(URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedAirplanesTests(TestCase):
    def setUp(self):
        self.client: APIClient = APIClient()
        self.user = get_user_model().objects.create_user(
            "user@user.com", "password"
        )
        self.client.force_authenticate(self.user)

    def test_airplane_list(self):
        airplane_type = sample_airplane_type()
        sample_airplane(airplane_type)
        sample_airplane(
            airplane_type=airplane_type,
            name="Sample airplane2",
        )
        serializer = AirplaneListSerializer(Airplane.objects.all(), many=True)

        res = self.client.get(URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_airplane_list_filter_by_capacity(self):
        airplane_type = sample_airplane_type()
        airplane1 = sample_airplane(airplane_type, rows=10, seats_in_row=10)
        airplane2 = sample_airplane(airplane_type, rows=30, seats_in_row=10)
        airplane3 = sample_airplane(airplane_type, rows=50, seats_in_row=10)
        serializer1 = AirplaneListSerializer(airplane1)
        serializer2 = AirplaneListSerializer(airplane2)
        serializer3 = AirplaneListSerializer(airplane3)

        res = self.client.get(
            URL,
            {"capacity_min": "110", "capacity_max": "310"}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn(serializer1.data, res.data["results"])
        self.assertIn(serializer2.data, res.data["results"])
        self.assertNotIn(serializer3.data, res.data["results"])

    def test_airplane_list_filter_by_airplane_types_ids(self):
        airplane_type1 = sample_airplane_type()
        airplane_type2 = sample_airplane_type(name="Airplane type2")
        airplane_type3 = sample_airplane_type(name="Airplane type3")
        airplane1 = sample_airplane(airplane_type1)
        airplane2 = sample_airplane(airplane_type2)
        airplane3 = sample_airplane(airplane_type3)
        serializer1 = AirplaneListSerializer(airplane1)
        serializer2 = AirplaneListSerializer(airplane2)
        serializer3 = AirplaneListSerializer(airplane3)

        res = self.client.get(
            URL,
            {"airplane_types": f"{airplane_type1.id},{airplane_type2.id}"}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer1.data, res.data["results"])
        self.assertIn(serializer2.data, res.data["results"])
        self.assertNotIn(serializer3.data, res.data["results"])

    def test_airplane_list_filter_by_name(self):
        airplane_type = sample_airplane_type()
        airplane1 = sample_airplane(airplane_type)
        airplane2 = sample_airplane(airplane_type, name="Different airplane")
        serializer1 = AirplaneListSerializer(airplane1)
        serializer2 = AirplaneListSerializer(airplane2)

        res = self.client.get(URL, {"name": "sample"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer1.data, res.data["results"])
        self.assertNotIn(serializer2.data, res.data["results"])

    def test_airplane_detail(self):
        airplane = sample_airplane()
        serializer = AirplaneDetailSerializer(airplane)

        res = self.client.get(detail_url(airplane.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_airplane_create_forbidden(self):
        airplane_type = sample_airplane_type()
        data = {
            "name": "Sample airplane",
            "rows": 30,
            "seats_in_row": 6,
            "airplane_type": airplane_type.id,
        }
        res = self.client.post(URL, data)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_airplane_update_forbidden(self):
        airplane = sample_airplane()
        res = self.client.patch(
            detail_url(airplane.id),
            {"name": "Changed airplane"}
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_airplane_delete_forbidden(self):
        airplane = sample_airplane()
        res = self.client.delete(detail_url(airplane.id))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminAirplanesTests(TestCase):
    def setUp(self):
        self.client: APIClient = APIClient()
        self.user = get_user_model().objects.create_superuser(
            "admin@user.com", "password"
        )
        self.client.force_authenticate(self.user)

    def test_airplane_create(self):
        airplane_type = sample_airplane_type()
        data = {
            "name": "Sample airplane",
            "rows": 30,
            "seats_in_row": 6,
            "airplane_type": airplane_type.id,
        }
        res = self.client.post(URL, data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Airplane.objects.count(), 1)
        self.assertEqual(Airplane.objects.first().name, data["name"])
        self.assertEqual(Airplane.objects.first().rows, data["rows"])
        self.assertEqual(
            Airplane.objects.first().seats_in_row,
            data["seats_in_row"]
        )
        self.assertEqual(
            Airplane.objects.first().airplane_type,
            airplane_type
        )

    def test_airplane_update(self):
        airplane = sample_airplane()
        diff_airplane_type = sample_airplane_type(name="Airplane type2")
        data = {
            "name": "Changed airplane",
            "rows": 10,
            "seats_in_row": 5,
            "airplane_type": diff_airplane_type.id,
        }
        res = self.client.put(detail_url(airplane.id), data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(Airplane.objects.first().name, data["name"])
        self.assertEqual(Airplane.objects.first().rows, data["rows"])
        self.assertEqual(
            Airplane.objects.first().seats_in_row,
            data["seats_in_row"]
        )
        self.assertEqual(
            Airplane.objects.first().airplane_type,
            diff_airplane_type
        )

    def test_airplane_delete(self):
        airplane = sample_airplane()
        res = self.client.delete(detail_url(airplane.id))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Airplane.objects.count(), 0)


class AirplaneImageUploadTests(TestCase):
    def setUp(self):
        self.client: APIClient = APIClient()
        self.user = User.objects.create_superuser(
            "admin@example.com", "password"
        )
        self.client.force_authenticate(self.user)
        self.airplane_type = sample_airplane_type()
        self.airplane = sample_airplane(self.airplane_type)

    def tearDown(self):
        self.airplane.image.delete()

    def test_upload_image_to_airplane(self):
        url = image_upload_url(self.airplane.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(url, {"image": ntf}, format="multipart")
        self.airplane.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.airplane.image.path))

    def test_upload_image_bad_request(self):
        url = image_upload_url(self.airplane.id)
        res = self.client.post(
            url, {"image": "not image"}, format="multipart"
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_image_to_movie_list(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(
                URL,
                {
                    "name": "Airplane",
                    "rows": 30,
                    "seats_in_row": 6,
                    "airplane_type": self.airplane_type.id,
                    "image": ntf,
                },
                format="multipart",
            )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        airplane = Airplane.objects.get(name="Airplane")
        self.assertFalse(airplane.image)
