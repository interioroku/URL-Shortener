from django.db.models import Count
from django.db.models.functions import TruncDate
from apps.urls.models import ClickEvent
from apps.analytics.models import DailyClickCount, CountryClickCount

class AnalyticsAggregationService:
    @staticmethod
    def aggregate_clicks(short_url_id=None):
        """
        Aggregates raw ClickEvent logs into DailyClickCount and CountryClickCount.
        Typically triggered via a daily Celery Beat task or an aggregation trigger.
        """
        clicks = ClickEvent.objects.all()
        if short_url_id:
            clicks = clicks.filter(short_url_id=short_url_id)
            
        # Group by short_url and date, and update DailyClickCount
        daily_groups = (
            clicks.annotate(date=TruncDate("timestamp"))
            .values("short_url_id", "date")
            .annotate(count=Count("id"))
        )
        
        for group in daily_groups:
            DailyClickCount.objects.update_or_create(
                short_url_id=group["short_url_id"],
                date=group["date"],
                defaults={"click_count": group["count"]}
            )

        # Group by short_url, date, and country, and update CountryClickCount
        country_groups = (
            clicks.annotate(date=TruncDate("timestamp"))
            .values("short_url_id", "date", "country")
            .annotate(count=Count("id"))
        )
        
        for group in country_groups:
            CountryClickCount.objects.update_or_create(
                short_url_id=group["short_url_id"],
                date=group["date"],
                country=group.get("country") or "Unknown",
                defaults={"click_count": group["count"]}
            )
