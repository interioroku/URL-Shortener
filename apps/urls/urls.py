from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.urls.views import ShortURLViewSet

router = DefaultRouter()
router.register(r"links", ShortURLViewSet, basename="shorturl")

urlpatterns = [
    path("", include(router.urls)),
]
