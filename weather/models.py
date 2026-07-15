from django.db import models


class WeatherLookup(models.Model):
    """Audit log of city lookups (API integration footprint)."""

    query = models.CharField(max_length=120)
    resolved_name = models.CharField(max_length=160, blank=True)
    country = models.CharField(max_length=8, blank=True)
    source = models.CharField(
        max_length=20,
        choices=[
            ("openweather", "OpenWeather"),
            ("demo", "Demo fallback"),
            ("cache", "Cache"),
        ],
        default="openweather",
    )
    temp_c = models.FloatField(null=True, blank=True)
    condition = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.query} → {self.resolved_name or '?'}"


class AdviceRequest(models.Model):
    """Log of AI / rule-based advisory calls."""

    city = models.CharField(max_length=120)
    mode = models.CharField(max_length=20)  # openai | rules
    advice = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.city} ({self.mode})"
