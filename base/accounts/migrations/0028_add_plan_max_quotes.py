from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0027_add_personal_agenda_recurrence_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="plan",
            name="max_quotes",
            field=models.PositiveIntegerField(default=10, verbose_name="Máximo de Orçamentos"),
        ),
    ]
