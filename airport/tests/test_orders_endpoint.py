from datetime import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from airport.models import Order, Ticket
from airport.serializers import OrderListSerializer, OrderDetailSerializer
from airport.tests.test_flights_endpoint import sample_flight

User = get_user_model()

URL = reverse("airport:order-list")


def detail_url(order_id):
    return reverse("airport:order-detail", args=[order_id])


def sample_order(user, flight=None, places: list[tuple[int, int]] = None):
    order = Order.objects.create(user=user)
    if flight is None:
        flight = sample_flight()
    if places is None:
        Ticket.objects.create(flight=flight, row=1, seat=1, order=order),
        Ticket.objects.create(flight=flight, row=1, seat=2, order=order),
    else:
        for place in places:
            Ticket.objects.create(
                flight=flight,
                row=place[0],
                seat=place[1],
                order=order
            ),
    return order


class UnauthenticatedOrdersTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client: APIClient = APIClient()

    def test_auth_required(self):
        res = self.client.get(URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedOrdersTests(TestCase):
    def setUp(self):
        self.client: APIClient = APIClient()
        self.user = User.objects.create_user(
            "user@user.com", "password"
        )
        self.client.force_authenticate(self.user)

    def test_order_list(self):
        flight = sample_flight()
        sample_order(user=self.user, flight=flight)
        sample_order(
            user=self.user,
            flight=flight,
            places=[(2, 1), (2, 2)])
        serializer = OrderListSerializer(Order.objects.all(), many=True)

        res = self.client.get(URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_order_list_filter_by_created_at(self):
        flight = sample_flight()
        order1 = sample_order(user=self.user, flight=flight)
        order2 = sample_order(
            user=self.user,
            flight=flight,
            places=[(2, 1), (2, 2)])
        order3 = sample_order(
            user=self.user,
            flight=flight,
            places=[(3, 1), (3, 2)])
        order1.created_at = datetime.fromisoformat("2026-07-20T15:30Z")
        order1.save()
        order2.created_at = datetime.fromisoformat("2026-07-22T15:30Z")
        order2.save()
        order3.created_at = datetime.fromisoformat("2026-07-24T15:30Z")
        order3.save()
        serializer1 = OrderListSerializer(order1)
        serializer2 = OrderListSerializer(order2)
        serializer3 = OrderListSerializer(order3)

        res = self.client.get(
            URL,
            {
                "created_before": "2026-07-23",
                "created_after": "2026-07-21",
            }
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn(serializer1.data, res.data["results"])
        self.assertIn(serializer2.data, res.data["results"])
        self.assertNotIn(serializer3.data, res.data["results"])

    def test_order_detail(self):
        order = sample_order(self.user)
        serializer = OrderDetailSerializer(order)

        res = self.client.get(detail_url(order.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_order_create(self):
        flight = sample_flight()
        data = {
            "tickets": [
                {"row": 1, "seat": 1, "flight": flight.id},
                {"row": 1, "seat": 2, "flight": flight.id},
            ]
        }
        res = self.client.post(URL, data, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Order.objects.first().tickets.count(), 2)
        self.assertEqual(Order.objects.first().flight, flight)

    def test_order_update_not_allowed(self):
        order = sample_order(self.user)
        res = self.client.put(
            detail_url(order.id)
        )
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_order_delete_not_allowed(self):
        order = sample_order(self.user)
        res = self.client.delete(detail_url(order.id))
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
