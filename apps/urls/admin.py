from django.contrib import admin
from apps.urls.models import ShortURL, ClickEvent

@admin.register(ShortURL)
class ShortURLAdmin(admin.ModelAdmin):
    list_display = ('short_code', 'original_url', 'user', 'created_at', 'expires_at', 'is_active')
    search_fields = ('short_code', 'original_url')
    list_filter = ('is_active', 'created_at', 'expires_at')

@admin.register(ClickEvent)
class ClickEventAdmin(admin.ModelAdmin):
    list_display = ('short_url', 'timestamp', 'ip_address', 'country')
    search_fields = ('short_url__short_code', 'ip_address', 'country')
    list_filter = ('timestamp', 'country')

