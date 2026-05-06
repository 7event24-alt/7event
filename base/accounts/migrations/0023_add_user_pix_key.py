from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0022_migrate_legacy_plan_types"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="pix_key",
            field=models.CharField(blank=True, default="", max_length=255, verbose_name="Chave PIX"),
        ),
    ]
