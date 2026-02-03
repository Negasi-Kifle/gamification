"""URL patterns for the Bonus module HTTP API."""

from django.urls import path

from .views.casino_freebet import CasinoFreeBetDetailView, CasinoFreeBetListCreateView
from .views.health_check import health_check

app_name = "bonus"


urlpatterns = [
    path("health/", health_check, name="health-check"),
    path(
        "casino-freebets/",
        CasinoFreeBetListCreateView.as_view(),
        name="casino-freebet-list-create",
    ),
    path(
        "casino-freebets/<str:public_id>/",
        CasinoFreeBetDetailView.as_view(),
        name="casino-freebet-detail",
    ),
]
