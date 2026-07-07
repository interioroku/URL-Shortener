from django.db import models
from apps.urls.models import ShortURL

class DailyClickCount(models.Model):
    short_url = models.ForeignKey(ShortURL, on_delete=models.CASCADE, related_name='daily_analytics')
    date = models.DateField(db_index=True)
    click_count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('short_url', 'date')
        indexes = [
            models.Index(fields=['short_url', 'date']),
        ]

    def __str__(self):
        return f"{self.short_url.short_code} on {self.date}: {self.click_count} clicks"


class CountryClickCount(models.Model):
    short_url = models.ForeignKey(ShortURL, on_delete=models.CASCADE, related_name='country_analytics')
    date = models.DateField(db_index=True)
    country = models.CharField(max_length=100, default='Unknown')
    click_count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('short_url', 'date', 'country')
        indexes = [
            models.Index(fields=['short_url', 'date', 'country']),
        ]

    def __str__(self):
        return f"{self.short_url.short_code} in {self.country} on {self.date}: {self.click_count} clicks"
