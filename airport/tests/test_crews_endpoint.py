from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from airport.models import Crew
from airport.serializers import CrewListSerializer, CrewDetailSerializer
from airport.tests.test_positions_endpoint import sample_position

User = get_user_model()

URL = reverse("airport:crew-list")


def detail_url(crew_id):
    return reverse("airport:crew-detail", args=[crew_id])


def sample_crew(position=None, **params):
    if not position:
        position = sample_position()
    defaults = {
        "first_name": "Sample First Name",
        "last_name": "Sample Last Name",
        "position": position,
    }
    defaults.update(params)

    return Crew.objects.create(**defaults)


class UnauthenticatedCrewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client: APIClient = APIClient()

    def test_auth_required(self):
        res = self.client.get(URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedCrewsTests(TestCase):
    def setUp(self):
        self.client: APIClient = APIClient()
        self.user = User.objects.create_user(
            "user@user.com", "password"
        )
        self.client.force_authenticate(self.user)

    def test_crew_list_forbidden(self):
        res = self.client.get(URL)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_crew_detail_forbidden(self):
        crew = sample_crew()
        res = self.client.get(detail_url(crew.id))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_crew_create_forbidden(self):
        position = sample_position()
        data = {
            "first_name": "Sample First Name",
            "last_name": "Sample Last Name",
            "position": position.id,
        }
        res = self.client.post(URL, data)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_crew_update_forbidden(self):
        crew = sample_crew()
        res = self.client.patch(
            detail_url(crew.id),
            {"first_name": "Changed First Name"}
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_crew_delete_forbidden(self):
        crew = sample_crew()
        res = self.client.delete(detail_url(crew.id))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminCrewsTests(TestCase):
    def setUp(self):
        self.client: APIClient = APIClient()
        self.user = User.objects.create_superuser(
            "admin@user.com", "password"
        )
        self.client.force_authenticate(self.user)

    def test_crew_list(self):
        pos = sample_position()
        sample_crew(pos)
        sample_crew(pos, first_name="Sample First Name2")
        serializer = CrewListSerializer(Crew.objects.all(), many=True)

        res = self.client.get(URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_crew_list_filter_by_first_name(self):
        pos = sample_position()
        crew1 = sample_crew(pos)
        crew2 = sample_crew(pos, first_name="Sample First Name2")
        crew3 = sample_crew(pos, first_name="Different First Name")
        serializer1 = CrewListSerializer(crew1)
        serializer2 = CrewListSerializer(crew2)
        serializer3 = CrewListSerializer(crew3)

        res = self.client.get(URL, {"first_name": "sample"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer1.data, res.data["results"])
        self.assertIn(serializer2.data, res.data["results"])
        self.assertNotIn(serializer3.data, res.data["results"])

    def test_crew_list_filter_by_iata_code(self):
        pos = sample_position()
        crew1 = sample_crew(pos)
        crew2 = sample_crew(pos, last_name="Sample Last Name2")
        crew3 = sample_crew(pos, last_name="Different Last Name")
        serializer1 = CrewListSerializer(crew1)
        serializer2 = CrewListSerializer(crew2)
        serializer3 = CrewListSerializer(crew3)

        res = self.client.get(URL, {"last_name": "sample"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer1.data, res.data["results"])
        self.assertIn(serializer2.data, res.data["results"])
        self.assertNotIn(serializer3.data, res.data["results"])

    def test_crew_list_filter_by_positions_ids(self):
        pos1 = sample_position(name="Sample position")
        pos2 = sample_position(name="Sample position2")
        pos3 = sample_position(name="Sample position3")
        crew1 = sample_crew(pos1)
        crew2 = sample_crew(pos2)
        crew3 = sample_crew(pos3)
        serializer1 = CrewListSerializer(crew1)
        serializer2 = CrewListSerializer(crew2)
        serializer3 = CrewListSerializer(crew3)

        res = self.client.get(URL, {"positions": f"{pos1.id},{pos2.id}"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer1.data, res.data["results"])
        self.assertIn(serializer2.data, res.data["results"])
        self.assertNotIn(serializer3.data, res.data["results"])

    def test_crew_detail(self):
        crew = sample_crew()
        serializer = CrewDetailSerializer(crew)

        res = self.client.get(detail_url(crew.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_crew_create(self):
        position = sample_position()
        data = {
            "first_name": "Sample First Name",
            "last_name": "Sample Last Name",
            "position": position.id,
        }
        res = self.client.post(URL, data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Crew.objects.count(), 1)
        self.assertEqual(Crew.objects.first().first_name, data["first_name"])
        self.assertEqual(Crew.objects.first().last_name, data["last_name"])
        self.assertEqual(Crew.objects.first().position, position)

    def test_crew_update(self):
        crew = sample_crew()
        new_position = sample_position(name="New Position")
        data = {
            "first_name": "Changed First Name",
            "last_name": "Changed Last Name",
            "position": new_position.id,
        }
        res = self.client.put(detail_url(crew.id), data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(Crew.objects.first().first_name, data["first_name"])
        self.assertEqual(Crew.objects.first().last_name, data["last_name"])
        self.assertEqual(Crew.objects.first().position, new_position)

    def test_crew_delete(self):
        crew = sample_crew()
        res = self.client.delete(detail_url(crew.id))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Crew.objects.count(), 0)
