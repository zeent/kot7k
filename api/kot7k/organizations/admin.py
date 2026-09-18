from django.contrib import admin

from .models import IdentityProvider


@admin.register(IdentityProvider)
class IdentityProviderAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "provider_type",
        "is_enabled",
        "display_order",
    )
    list_filter = ("provider_type", "is_enabled")
    search_fields = ("name", "key")
    ordering = ("display_order", "name")
