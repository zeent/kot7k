import django.db.models.deletion
import kot7k.applications.models.oauth_client
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("applications", "0002_single_installation"),
        ("authentication", "0004_user_oidc_subject"),
    ]

    operations = [
        migrations.CreateModel(
            name="OAuthClient",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("client_id", models.CharField(default=kot7k.applications.models.oauth_client.generate_client_id, max_length=255, unique=True)),
                ("client_secret_hash", models.CharField(blank=True, max_length=255)),
                ("is_confidential", models.BooleanField(default=True)),
                ("redirect_uris", models.JSONField(default=list)),
                ("allowed_scopes", models.JSONField(default=kot7k.applications.models.oauth_client.default_allowed_scopes)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("application", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="oauth_client", to="applications.application")),
            ],
            options={"ordering": ("application__name",)},
        ),
        migrations.CreateModel(
            name="AuthorizationCode",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code_hash", models.CharField(max_length=64, unique=True)),
                ("redirect_uri", models.TextField()),
                ("scopes", models.JSONField(default=list)),
                ("nonce", models.CharField(max_length=255)),
                ("code_challenge", models.CharField(max_length=128)),
                ("expires_at", models.DateTimeField()),
                ("used_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("client", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="applications.oauthclient")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="OAuthRefreshToken",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("token_hash", models.CharField(max_length=64, unique=True)),
                ("scopes", models.JSONField(default=list)),
                ("expires_at", models.DateTimeField()),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("client", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="applications.oauthclient")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddIndex(model_name="authorizationcode", index=models.Index(fields=["code_hash", "expires_at"], name="oidc_code_expiry_idx")),
        migrations.AddIndex(model_name="oauthrefreshtoken", index=models.Index(fields=["token_hash", "expires_at"], name="oidc_refresh_expiry_idx")),
    ]
