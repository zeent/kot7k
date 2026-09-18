# Generated manually for KOT7K's tenant identity-provider configuration.

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0002_membership_role"),
    ]

    operations = [
        migrations.CreateModel(
            name="IdentityProvider",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "key",
                    models.CharField(
                        help_text=(
                            "Stable identifier used in API routes and login "
                            "screens."
                        ),
                        max_length=64,
                        validators=[
                            django.core.validators.RegexValidator(
                                message=(
                                    "Use lowercase letters, numbers, hyphens, "
                                    "and underscores."
                                ),
                                regex=(
                                    "^[a-z0-9](?:[a-z0-9_-]{0,62}[a-z0-9])?$"
                                ),
                            )
                        ],
                    ),
                ),
                (
                    "provider_type",
                    models.CharField(
                        choices=[
                            ("local", "Email and password"),
                            ("google", "Google"),
                            ("microsoft", "Microsoft 365"),
                            ("x509", "Digital certificate (X.509/FNMT)"),
                            ("webauthn", "Passkey (WebAuthn)"),
                        ],
                        max_length=16,
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("is_enabled", models.BooleanField(default=False)),
                ("display_order", models.PositiveSmallIntegerField(default=0)),
                (
                    "configuration",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text=(
                            "Non-secret provider settings. Store credentials "
                            "in a secret manager and reference them with "
                            "secret_reference."
                        ),
                    ),
                ),
                (
                    "secret_reference",
                    models.CharField(
                        blank=True,
                        help_text=(
                            "Reference to credentials held outside the database."
                        ),
                        max_length=255,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="identity_providers",
                        to="organizations.organization",
                    ),
                ),
            ],
            options={
                "ordering": ("display_order", "name", "id"),
            },
        ),
        migrations.AddConstraint(
            model_name="identityprovider",
            constraint=models.UniqueConstraint(
                fields=("organization", "key"),
                name="unique_organization_provider_key",
            ),
        ),
        migrations.AddIndex(
            model_name="identityprovider",
            index=models.Index(
                fields=["organization", "is_enabled", "display_order"],
                name="org_idp_enabled_order_idx",
            ),
        ),
    ]
