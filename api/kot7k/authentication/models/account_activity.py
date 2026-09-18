from django.db import models


class AccountActivity(models.Model):
    class Action(models.TextChoices):
        LOGIN = "login", "Signed in"
        LOGOUT = "logout", "Signed out"
        ROLE_ASSIGNED = "role_assigned", "Role assigned"
        ROLE_REMOVED = "role_removed", "Role removed"

    user = models.ForeignKey(
        "authentication.User", on_delete=models.CASCADE, related_name="account_activities"
    )
    action = models.CharField(max_length=32, choices=Action.choices)
    description = models.CharField(max_length=255)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = [models.Index(fields=("user", "created_at"), name="account_activity_idx")]

    def __str__(self):
        return f"{self.user} · {self.action}"
