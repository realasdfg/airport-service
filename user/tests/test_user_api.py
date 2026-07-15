from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from user.serializers import UserSerializer

User = get_user_model()


class UnauthenticatedUserTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_user_create(self):
        url = reverse("user:register")
        data = {
            "email": "user@example.com",
            "password": "qwertyqwerty",
        }
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.first().email, data["email"])

    def test_user_create_with_bad_password(self):
        url = reverse("user:register")
        data = {
            "email": "user@example.com",
            "password": "qwer",
        }
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)

    def test_user_me_detail_401_error(self):
        res = self.client.get(reverse("user:manage_user"))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedUserTests(TestCase):
    def setUp(self):
        self.client: APIClient = APIClient()
        self.user = User.objects.create_user(
            "user@user.com", "password"
        )
        self.client.force_authenticate(self.user)
        self.url_me = reverse("user:manage_user")

    def test_user_me_detail(self):
        serializer = UserSerializer(self.user)

        res = self.client.get(self.url_me)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_user_me_update(self):
        data = {
            "email": "changed@example.com",
            "password": "changed password",
        }
        res = self.client.put(self.url_me, data)

        serializer = UserSerializer(self.user)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
        self.assertTrue(self.user.check_password(data["password"]))
