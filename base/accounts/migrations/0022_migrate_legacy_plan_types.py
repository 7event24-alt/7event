from django.db import migrations, models


def migrate_legacy_plan_types(apps, schema_editor):
    Plan = apps.get_model("accounts", "Plan")

    Plan.objects.filter(type="tester").update(type="free")
    Plan.objects.filter(type="basic").update(type="pro")


def reverse_migrate_legacy_plan_types(apps, schema_editor):
    Plan = apps.get_model("accounts", "Plan")

    Plan.objects.filter(type="free").update(type="tester")
    Plan.objects.filter(type="pro").update(type="basic")


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            migrate_legacy_plan_types,
            reverse_code=reverse_migrate_legacy_plan_types,
        ),
        migrations.AlterField(
            model_name="plan",
            name="type",
            field=models.CharField(
                choices=[
                    ("free", "Grátis"),
                    ("pro", "Profissional"),
                    ("business", "Business"),
                ],
                max_length=20,
                unique=True,
                verbose_name="Tipo",
            ),
        ),
    ]
