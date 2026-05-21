from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0030_personaltaskreminderdispatch"),
    ]

    operations = [
        migrations.CreateModel(
            name="SystemReminderDispatch",
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
                    "entity_type",
                    models.CharField(
                        choices=[
                            ("task", "Tarefa"),
                            ("agenda_event", "Evento de Agenda"),
                            ("job", "Trabalho"),
                        ],
                        max_length=20,
                        verbose_name="Tipo de Entidade",
                    ),
                ),
                ("entity_id", models.PositiveIntegerField(verbose_name="ID da Entidade")),
                (
                    "reminder_type",
                    models.CharField(max_length=40, verbose_name="Tipo de Lembrete"),
                ),
                ("slot_date", models.DateField(verbose_name="Data de Referência")),
                (
                    "slot_label",
                    models.CharField(default="exact", max_length=20, verbose_name="Slot"),
                ),
                (
                    "sent_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Enviado em"),
                ),
            ],
            options={
                "verbose_name": "Disparo de Lembrete",
                "verbose_name_plural": "Disparos de Lembrete",
                "db_table": "system_reminder_dispatches",
            },
        ),
        migrations.AddConstraint(
            model_name="systemreminderdispatch",
            constraint=models.UniqueConstraint(
                fields=(
                    "entity_type",
                    "entity_id",
                    "reminder_type",
                    "slot_date",
                    "slot_label",
                ),
                name="uniq_system_reminder_dispatch",
            ),
        ),
        migrations.AddIndex(
            model_name="systemreminderdispatch",
            index=models.Index(fields=["entity_type", "entity_id"], name="system_remin_entity__6e5a5f_idx"),
        ),
        migrations.AddIndex(
            model_name="systemreminderdispatch",
            index=models.Index(fields=["slot_date", "reminder_type"], name="system_remin_slot_da_8a5d64_idx"),
        ),
    ]
