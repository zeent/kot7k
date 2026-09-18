from django.core.validators import RegexValidator
from django.db import models


application_key_validator = RegexValidator(
    regex=r"^[a-z0-9](?:[a-z0-9_-]{0,62}[a-z0-9])?$",
    message="Use lowercase letters, numbers, hyphens, and underscores.",
)


class Application(models.Model):
    key = models.CharField(max_length=64, unique=True, validators=(application_key_validator,))
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    homepage_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name", "id")

    def __str__(self):
        return self.name
