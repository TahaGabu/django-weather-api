import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_http_methods

from .models import AdviceRequest, WeatherLookup
from .services import WeatherAPIError, fetch_weather, generate_advice


def home(request):
    city = (request.GET.get("city") or "").strip()
    weather = None
    advice = None
    advice_mode = None
    error = None

    if city:
        try:
            weather = fetch_weather(city)
            WeatherLookup.objects.create(
                query=city,
                resolved_name=weather.get("city", ""),
                country=weather.get("country", ""),
                source=weather.get("source", "openweather"),
                temp_c=weather.get("temp"),
                condition=weather.get("condition", ""),
            )
            advice, advice_mode = generate_advice(weather)
            AdviceRequest.objects.create(city=weather.get("city", city), mode=advice_mode, advice=advice)
        except WeatherAPIError as exc:
            error = str(exc)

    recent = WeatherLookup.objects.all()[:8]
    return render(
        request,
        "weather/home.html",
        {
            "city": city,
            "weather": weather,
            "advice": advice,
            "advice_mode": advice_mode,
            "error": error,
            "recent": recent,
        },
    )


@require_GET
def api_weather(request):
    city = (request.GET.get("city") or "").strip()
    if not city:
        return JsonResponse({"error": "Query param 'city' is required."}, status=400)
    try:
        weather = fetch_weather(city)
        WeatherLookup.objects.create(
            query=city,
            resolved_name=weather.get("city", ""),
            country=weather.get("country", ""),
            source=weather.get("source", "openweather"),
            temp_c=weather.get("temp"),
            condition=weather.get("condition", ""),
        )
        return JsonResponse(weather)
    except WeatherAPIError as exc:
        return JsonResponse({"error": str(exc)}, status=502)


@require_http_methods(["GET", "POST"])
def api_advice(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body.decode() or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON body."}, status=400)
        city = (body.get("city") or "").strip()
    else:
        city = (request.GET.get("city") or "").strip()

    if not city:
        return JsonResponse({"error": "Provide city via query or JSON body."}, status=400)

    try:
        weather = fetch_weather(city)
        advice, mode = generate_advice(weather)
        AdviceRequest.objects.create(city=weather.get("city", city), mode=mode, advice=advice)
        return JsonResponse(
            {
                "city": weather.get("city"),
                "mode": mode,
                "advice": advice,
                "weather": {
                    "temp": weather.get("temp"),
                    "condition": weather.get("condition"),
                    "humidity": weather.get("humidity"),
                },
            }
        )
    except WeatherAPIError as exc:
        return JsonResponse({"error": str(exc)}, status=502)
