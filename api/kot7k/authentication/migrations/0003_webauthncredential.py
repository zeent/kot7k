from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("authentication", "0002_externalidentity"), ("organizations", "0005_remove_github_provider"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="WebAuthnCredential",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("credential_id", models.CharField(max_length=1400)), ("public_key", models.BinaryField()),
                ("sign_count", models.PositiveBigIntegerField(default=0)), ("transports", models.JSONField(blank=True, default=list)),
                ("name", models.CharField(default="Passkey", max_length=100)), ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)), ("last_used_at", models.DateTimeField(blank=True, null=True)),
                ("provider", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="webauthn_credentials", to="organizations.identityprovider")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="webauthn_credentials", to=settings.AUTH_USER_MODEL)),
            ], options={"ordering": ("-created_at",)},
        ),
        migrations.AddConstraint(model_name="webauthncredential", constraint=models.UniqueConstraint(fields=("provider", "credential_id"), name="unique_webauthn_provider_credential")),
        migrations.AddIndex(model_name="webauthncredential", index=models.Index(fields=["provider", "user"], name="webauthn_provider_user_idx")),
    ]
