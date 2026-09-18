from django.db import migrations, models


def remove_github_providers(apps, schema_editor):
    IdentityProvider = apps.get_model("organizations", "IdentityProvider")
    IdentityProvider.objects.filter(provider_type="github").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0004_enable_local_provider"),
    ]

    operations = [
        migrations.RunPython(
            remove_github_providers,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="identityprovider",
            name="provider_type",
            field=models.CharField(
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
    ]
