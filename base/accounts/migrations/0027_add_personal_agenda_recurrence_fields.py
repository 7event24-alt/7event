from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0026_rename_personal_age_user_id_89dd1d_idx_personal_ag_user_id_7b1d73_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="personalagendaevent",
            name="recurrence",
            field=models.CharField(
                choices=[
                    ("none", "Não repetir"),
                    ("daily", "Diariamente"),
                    ("weekly", "Semanalmente"),
                    ("monthly", "Mensalmente"),
                    ("yearly", "Anualmente"),
                ],
                default="none",
                max_length=20,
                verbose_name="Recorrência",
            ),
        ),
        migrations.AddField(
            model_name="personalagendaevent",
            name="recurrence_until",
            field=models.DateField(blank=True, null=True, verbose_name="Repetir até"),
        ),
    ]
