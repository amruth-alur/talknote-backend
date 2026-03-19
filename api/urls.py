"""
API URL Configuration for the Notes app.

All note-related endpoints are registered via DRF's router.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import NoteViewSet

router = DefaultRouter()
router.register(r"notes", NoteViewSet, basename="note")

app_name = "api"

urlpatterns = [
    path("", include(router.urls)),
]
