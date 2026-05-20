from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0029_add_personal_limits_to_plan"),
    ]

    operations = [
        migrations.CreateModel(
            name="PersonalTaskReminderDispatch",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "reminder_type",
                    models.CharField(
                        choices=[("1h_before", "1 hora antes")],
                        default="1h_before",
                        max_length=20,
                        verbose_name="Tipo de Lembrete",
                    ),
                ),
                (
                    "sent_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Enviado em"),
                ),
                (
                    "task",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="reminder_dispatches",
                        to="accounts.personaltask",
                        verbose_name="Tarefa",
                    ),
                ),
            ],
            options={
                "verbose_name": "Disparo de Lembrete de Tarefa",
                "verbose_name_plural": "Disparos de Lembrete de Tarefa",
                "db_table": "personal_task_reminder_dispatches",
            },
        ),
        migrations.AddConstraint(
            model_name="personaltaskreminderdispatch",
            constraint=models.UniqueConstraint(
                fields=("task", "reminder_type"), name="uniq_task_reminder_type"
            ),
        ),
    ]
