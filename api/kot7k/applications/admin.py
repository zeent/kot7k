from django.contrib import admin

from .models import Application, ApplicationAssignment, ApplicationRole, OAuthClient


class ApplicationRoleInline(admin.TabularInline):
    model = ApplicationRole
    extra = 0


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("name", "key", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "key")
    inlines = (ApplicationRoleInline,)


@admin.register(ApplicationRole)
class ApplicationRoleAdmin(admin.ModelAdmin):
    list_display = ("name", "application", "key")
    list_filter = ("application",)
    search_fields = ("name", "key", "application__name")
    autocomplete_fields = ("application",)


@admin.register(ApplicationAssignment)
class ApplicationAssignmentAdmin(admin.ModelAdmin):
    list_display = ("user", "application", "role", "created_at")
    list_filter = ("application", "role")
    search_fields = ("user__email", "application__name", "role__name")
    autocomplete_fields = ("application", "user", "role")


@admin.register(OAuthClient)
class OAuthClientAdmin(admin.ModelAdmin):
    list_display = ("application", "client_id", "is_confidential", "is_active")
    list_filter = ("is_confidential", "is_active")
    search_fields = ("application__name", "client_id")
    readonly_fields = ("client_secret_hash", "created_at", "updated_at")
