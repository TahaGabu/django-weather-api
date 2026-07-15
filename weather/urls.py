from django.urls import path

from . import views

app_name = "weather"

urlpatterns = [
    path("", views.home, name="home"),
    path("api/weather/", views.api_weather, name="api_weather"),
    path("api/advice/", views.api_advice, name="api_advice"),
]
