import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("authentication", "0003_webauthncredential")]

    operations = [
        migrations.AddField(
            model_name="user",
            name="oidc_subject",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
