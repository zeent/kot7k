from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("organizations", "0006_single_installation")]

    operations = [
        migrations.AlterField(
            model_name="identityprovider",
            name="provider_type",
            field=models.CharField(
                choices=[
                    ("local", "Email and password"),
                    ("google", "Google"),
                    ("microsoft", "Microsoft 365"),
                    ("apple", "Apple"),
                    ("x509", "Digital certificate (X.509/FNMT)"),
                    ("webauthn", "Passkey (WebAuthn)"),
                ],
                max_length=16,
            ),
        ),
    ]
