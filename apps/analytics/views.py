from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.urls.models import ShortURL
from apps.analytics.models import DailyClickCount, CountryClickCount
from apps.analytics.serializers import DailyClickCountSerializer, CountryClickCountSerializer
from apps.analytics.services import AnalyticsAggregationService

class URLAnalyticsView(APIView):
    """
    API endpoint that returns aggregated daily and country click analytics for a given short code.
    """
    def get(self, request, short_code):
        try:
            # We look up by short_code and active state
            short_url = ShortURL.objects.get(short_code=short_code, is_active=True)
        except ShortURL.DoesNotExist:
            return Response(
                {"error": "Shortened URL not found or is inactive."}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        daily_stats = DailyClickCount.objects.filter(short_url=short_url).order_by('date')
        country_stats = CountryClickCount.objects.filter(short_url=short_url).order_by('date', 'country')
        
        daily_serialized = DailyClickCountSerializer(daily_stats, many=True).data
        country_serialized = CountryClickCountSerializer(country_stats, many=True).data
        
        return Response({
            "short_code": short_code,
            "original_url": short_url.original_url,
            "total_clicks": sum(item['click_count'] for item in daily_serialized),
            "daily_clicks": daily_serialized,
            "country_clicks": country_serialized
        }, status=status.HTTP_200_OK)


class TriggerAggregationView(APIView):
    """
    Management API view to manually run the click analytics aggregation.
    """
    def post(self, request):
        try:
            AnalyticsAggregationService.aggregate_clicks()
            return Response(
                {"message": "Analytics aggregation completed successfully."},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to aggregate analytics: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

