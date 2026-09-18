from django.db import migrations


def enable_django_login(apps, schema_editor):
    Provider = apps.get_model("organizations", "IdentityProvider")
    providers = Provider.objects.using(schema_editor.connection.alias)
    local = providers.filter(provider_type="local").first()
    if local is not None:
        providers.filter(pk=local.pk).update(is_enabled=True)
    else:
        key = "django-local"
        suffix = 1
        while providers.filter(key=key).exists():
            key = f"django-local-{suffix}"
            suffix += 1
        providers.create(key=key, provider_type="local", name="Django", is_enabled=True, display_order=0)


class Migration(migrations.Migration):
    dependencies = [("organizations", "0008_identityprovider_encrypted_secret_and_more")]
    operations = [migrations.RunPython(enable_django_login, migrations.RunPython.noop)]
