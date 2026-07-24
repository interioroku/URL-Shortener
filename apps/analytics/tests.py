from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
import datetime

from apps.urls.models import ShortURL, ClickEvent
from apps.analytics.models import DailyClickCount, CountryClickCount
from apps.analytics.services import AnalyticsAggregationService
from apps.analytics.tasks import aggregate_click_data

class AnalyticsServiceTests(TestCase):
    def setUp(self):
        self.short_url = ShortURL.objects.create(
            original_url="https://example.com",
            short_code="examply"
        )
        
    def test_aggregate_clicks(self):
        # Create ClickEvents on different days and countries
        today = timezone.now()
        yesterday = today - datetime.timedelta(days=1)
        
        ClickEvent.objects.create(short_url=self.short_url, timestamp=today, country="United States")
        ClickEvent.objects.create(short_url=self.short_url, timestamp=today, country="United States")
        ClickEvent.objects.create(short_url=self.short_url, timestamp=today, country="Canada")
        ClickEvent.objects.create(short_url=self.short_url, timestamp=yesterday, country="Canada")
        
        # Trigger aggregation
        AnalyticsAggregationService.aggregate_clicks()
        
        # Verify daily stats
        daily_today = DailyClickCount.objects.get(short_url=self.short_url, date=today.date())
        daily_yesterday = DailyClickCount.objects.get(short_url=self.short_url, date=yesterday.date())
        self.assertEqual(daily_today.click_count, 3)
        self.assertEqual(daily_yesterday.click_count, 1)
        
        # Verify country stats
        us_today = CountryClickCount.objects.get(short_url=self.short_url, date=today.date(), country="United States")
        ca_today = CountryClickCount.objects.get(short_url=self.short_url, date=today.date(), country="Canada")
        ca_yesterday = CountryClickCount.objects.get(short_url=self.short_url, date=yesterday.date(), country="Canada")
        self.assertEqual(us_today.click_count, 2)
        self.assertEqual(ca_today.click_count, 1)
        self.assertEqual(ca_yesterday.click_count, 1)

    def test_aggregate_clicks_update_existing(self):
        today = timezone.now()
        
        ClickEvent.objects.create(short_url=self.short_url, timestamp=today, country="Japan")
        AnalyticsAggregationService.aggregate_clicks()
        
        # Verify first count
        daily = DailyClickCount.objects.get(short_url=self.short_url, date=today.date())
        self.assertEqual(daily.click_count, 1)
        
        # Add another event and run aggregation again
        ClickEvent.objects.create(short_url=self.short_url, timestamp=today, country="Japan")
        AnalyticsAggregationService.aggregate_clicks()
        
        daily.refresh_from_db()
        self.assertEqual(daily.click_count, 2)


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class AnalyticsAPITests(APITestCase):
    def setUp(self):
        self.short_url = ShortURL.objects.create(
            original_url="https://example2.com",
            short_code="ex2"
        )
        self.today = timezone.now()
        
        # Create some stats
        self.daily_stat = DailyClickCount.objects.create(
            short_url=self.short_url,
            date=self.today.date(),
            click_count=5
        )
        self.country_stat = CountryClickCount.objects.create(
            short_url=self.short_url,
            date=self.today.date(),
            country="Germany",
            click_count=5
        )

    def test_get_analytics_stats_success(self):
        url = reverse("url_analytics", kwargs={"short_code": "ex2"})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["short_code"], "ex2")
        self.assertEqual(response.data["original_url"], "https://example2.com")
        self.assertEqual(response.data["total_clicks"], 5)
        self.assertEqual(len(response.data["daily_clicks"]), 1)
        self.assertEqual(response.data["daily_clicks"][0]["click_count"], 5)
        self.assertEqual(len(response.data["country_clicks"]), 1)
        self.assertEqual(response.data["country_clicks"][0]["country"], "Germany")

    def test_get_analytics_stats_not_found(self):
        url = reverse("url_analytics", kwargs={"short_code": "nonexistent"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_trigger_aggregation_endpoint(self):
        # Create a click event
        ClickEvent.objects.create(short_url=self.short_url, timestamp=self.today, country="Australia")
        
        url = reverse("trigger_aggregation")
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should now have an aggregate for Australia
        self.assertTrue(CountryClickCount.objects.filter(short_url=self.short_url, country="Australia").exists())


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class AnalyticsCeleryTaskTests(TestCase):
    def test_aggregate_click_data_task(self):
        short_url = ShortURL.objects.create(
            original_url="https://example3.com",
            short_code="ex3"
        )
        today = timezone.now()
        ClickEvent.objects.create(short_url=short_url, timestamp=today, country="India")
        
        # Invoke task
        aggregate_click_data.delay()
        
        # Verify aggregation occurred
        self.assertTrue(DailyClickCount.objects.filter(short_url=short_url).exists())
        self.assertTrue(CountryClickCount.objects.filter(short_url=short_url, country="India").exists())

