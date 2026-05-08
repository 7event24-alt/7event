from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0028_add_plan_max_quotes"),
    ]

    operations = [
        migrations.AddField(
            model_name="plan",
            name="max_personal_agenda_events",
            field=models.PositiveIntegerField(default=10, verbose_name="Máximo de Itens de Agenda Pessoal"),
        ),
        migrations.AddField(
            model_name="plan",
            name="max_personal_tasks",
            field=models.PositiveIntegerField(default=10, verbose_name="Máximo de Tarefas Pessoais"),
        ),
    ]
