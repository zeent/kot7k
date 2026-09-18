from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


def keep_zeent_applications(apps, schema_editor):
    Application = apps.get_model("applications", "Application")
    Assignment = apps.get_model("applications", "ApplicationAssignment")

    Application.objects.exclude(organization__slug="zeent").delete()
    for assignment in Assignment.objects.select_related("membership").all():
        assignment.user_id = assignment.membership.user_id
        assignment.save(update_fields=("user_id",))


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("applications", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="applicationassignment",
            name="user",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="application_assignments",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(keep_zeent_applications, migrations.RunPython.noop),
        migrations.RemoveConstraint(
            model_name="applicationassignment",
            name="unique_membership_application_role",
        ),
        migrations.RemoveConstraint(
            model_name="application",
            name="unique_organization_application_key",
        ),
        migrations.RemoveField(model_name="applicationassignment", name="membership"),
        migrations.AlterField(
            model_name="applicationassignment",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="application_assignments",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RemoveField(model_name="application", name="organization"),
        migrations.AlterField(
            model_name="application",
            name="key",
            field=models.CharField(
                max_length=64,
                unique=True,
                validators=[django.core.validators.RegexValidator(
                    regex=r"^[a-z0-9](?:[a-z0-9_-]{0,62}[a-z0-9])?$",
                    message="Use lowercase letters, numbers, hyphens, and underscores.",
                )],
            ),
        ),
        migrations.AddConstraint(
            model_name="applicationassignment",
            constraint=models.UniqueConstraint(
                fields=("user", "role"), name="unique_user_application_role"
            ),
        ),
        migrations.AlterModelOptions(
            name="applicationassignment",
            options={"ordering": ("application", "user", "role")},
        ),
    ]
