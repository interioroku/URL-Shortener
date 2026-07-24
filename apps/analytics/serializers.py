from rest_framework import serializers
from apps.analytics.models import DailyClickCount, CountryClickCount

class DailyClickCountSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyClickCount
        fields = ['date', 'click_count']

class CountryClickCountSerializer(serializers.ModelSerializer):
    class Meta:
        model = CountryClickCount
        fields = ['date', 'country', 'click_count']
