from django.urls import path
from apps.analytics.views import URLAnalyticsView, TriggerAggregationView

urlpatterns = [
    path("stats/<str:short_code>/", URLAnalyticsView.as_view(), name="url_analytics"),
    path("aggregate/", TriggerAggregationView.as_view(), name="trigger_aggregation"),
]
