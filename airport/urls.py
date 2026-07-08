from django.urls import path, include
from rest_framework import routers

from airport.views import CityViewSet

router = routers.DefaultRouter()
router.register("cities", CityViewSet)

urlpatterns = [
    path("", include(router.urls)),
]

app_name = "airport"
