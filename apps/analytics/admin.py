from django.contrib import admin
from apps.analytics.models import DailyClickCount, CountryClickCount

@admin.register(DailyClickCount)
class DailyClickCountAdmin(admin.ModelAdmin):
    list_display = ('short_url', 'date', 'click_count')
    search_fields = ('short_url__short_code', 'date')
    list_filter = ('date',)

@admin.register(CountryClickCount)
class CountryClickCountAdmin(admin.ModelAdmin):
    list_display = ('short_url', 'date', 'country', 'click_count')
    search_fields = ('short_url__short_code', 'date', 'country')
    list_filter = ('date', 'country')

