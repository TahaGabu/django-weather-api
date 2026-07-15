from django.contrib import admin

from .models import AdviceRequest, WeatherLookup


@admin.register(WeatherLookup)
class WeatherLookupAdmin(admin.ModelAdmin):
    list_display = ("query", "resolved_name", "country", "temp_c", "condition", "source", "created_at")
    list_filter = ("source", "country")
    search_fields = ("query", "resolved_name")


@admin.register(AdviceRequest)
class AdviceRequestAdmin(admin.ModelAdmin):
    list_display = ("city", "mode", "created_at")
    list_filter = ("mode",)
    search_fields = ("city", "advice")
