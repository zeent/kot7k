from django.db import migrations


def enable_local_provider(apps, schema_editor):
    Organization = apps.get_model("organizations", "Organization")
    IdentityProvider = apps.get_model("organizations", "IdentityProvider")

    for organization in Organization.objects.iterator():
        IdentityProvider.objects.get_or_create(
            organization=organization,
            key="local",
            defaults={
                "provider_type": "local",
                "name": "Email and password",
                "is_enabled": True,
                "display_order": 100,
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0003_identityprovider"),
    ]

    operations = [
        migrations.RunPython(
            enable_local_provider,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
