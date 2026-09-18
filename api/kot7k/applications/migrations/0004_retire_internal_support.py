from django.db import migrations


def retire_internal_support(apps, schema_editor):
    Application = apps.get_model("applications", "Application")
    # Retain assignments and administrator-edited external applications.
    Application.objects.using(schema_editor.connection.alias).filter(
        key__in=["kot7k-support", "talaia-support"],
        homepage_url="/support",
    ).update(is_active=False)


class Migration(migrations.Migration):
    dependencies = [("applications", "0003_oidc_provider")]
    operations = [migrations.RunPython(retire_internal_support, migrations.RunPython.noop)]
