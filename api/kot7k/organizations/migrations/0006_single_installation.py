from django.conf import settings
from django.db import migrations, models
import django.core.validators


def keep_zeent_directory(apps, schema_editor):
    Organization = apps.get_model("organizations", "Organization")
    Membership = apps.get_model("organizations", "Membership")
    IdentityProvider = apps.get_model("organizations", "IdentityProvider")
    User = apps.get_model(*settings.AUTH_USER_MODEL.split("."))

    zeent = Organization.objects.filter(slug="zeent").first()
    if zeent is None:
        if not Organization.objects.exists():
            return
        raise RuntimeError(
            "Cannot convert to a single installation: organization 'zeent' does not exist."
        )

    IdentityProvider.objects.exclude(organization=zeent).delete()
    zeent_user_ids = Membership.objects.filter(organization=zeent).values_list(
        "user_id", flat=True
    )
    User.objects.exclude(id__in=zeent_user_ids).delete()


class Migration(migrations.Migration):
    # PostgreSQL cannot alter IdentityProvider in the same transaction in which
    # cascading deletes have queued foreign-key trigger events for that table.
    # Running each operation in its own transaction lets those events settle
    # before the schema is changed.
    atomic = False

    dependencies = [
        ("applications", "0002_single_installation"),
        ("authentication", "0003_webauthncredential"),
        ("organizations", "0005_remove_github_provider"),
    ]

    operations = [
        migrations.RunPython(keep_zeent_directory, migrations.RunPython.noop),
        migrations.RemoveConstraint(
            model_name="identityprovider",
            name="unique_organization_provider_key",
        ),
        migrations.RemoveIndex(
            model_name="identityprovider",
            name="org_idp_enabled_order_idx",
        ),
        migrations.RemoveField(model_name="identityprovider", name="organization"),
        migrations.AlterField(
            model_name="identityprovider",
            name="key",
            field=models.CharField(
                max_length=64,
                unique=True,
                help_text="Stable identifier used in API routes and login screens.",
                validators=[django.core.validators.RegexValidator(
                    regex=r"^[a-z0-9](?:[a-z0-9_-]{0,62}[a-z0-9])?$",
                    message="Use lowercase letters, numbers, hyphens, and underscores.",
                )],
            ),
        ),
        migrations.AddIndex(
            model_name="identityprovider",
            index=models.Index(
                fields=["is_enabled", "display_order"],
                name="idp_enabled_order_idx",
            ),
        ),
        migrations.DeleteModel(name="Membership"),
        migrations.DeleteModel(name="Organization"),
    ]
