from rest_framework import serializers
from apps.urls.models import ShortURL

class ShortURLSerializer(serializers.ModelSerializer):
    short_url = serializers.SerializerMethodField()
    is_expired = serializers.ReadOnlyField()

    class Meta:
        model = ShortURL
        fields = [
            "id",
            "original_url",
            "short_code",
            "short_url",
            "created_at",
            "expires_at",
            "is_active",
            "is_expired",
        ]
        read_only_fields = ["id", "short_code", "created_at"]

    def get_short_url(self, obj):
        request = self.context.get("request")
        if request is not None:
            # Build absolute uri (e.g. http://127.0.0.1:8000/xyzabc/)
            return request.build_absolute_uri(f"/{obj.short_code}/")
        return f"/{obj.short_code}/"

    def validate_original_url(self, value):
        # Standard URLField validates layout; we can add additional restrictions here if necessary.
        return value
