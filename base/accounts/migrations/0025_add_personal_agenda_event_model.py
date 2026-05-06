from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0024_merge_20260505_2238"),
    ]

    operations = [
        migrations.CreateModel(
            name="PersonalAgendaEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200, verbose_name="Título")),
                ("date", models.DateField(verbose_name="Data")),
                ("start_time", models.TimeField(verbose_name="Hora de Início")),
                ("end_time", models.TimeField(verbose_name="Hora de Fim")),
                ("location", models.CharField(blank=True, max_length=255, verbose_name="Local")),
                ("description", models.TextField(blank=True, verbose_name="Descrição")),
                (
                    "status",
                    models.CharField(
                        choices=[("pending", "Pendente"), ("completed", "Concluída"), ("cancelled", "Cancelada")],
                        default="pending",
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criada em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Atualizada em")),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="personal_agenda_events",
                        to="accounts.user",
                        verbose_name="Usuário",
                    ),
                ),
            ],
            options={
                "verbose_name": "Agenda Pessoal",
                "verbose_name_plural": "Agenda Pessoal",
                "db_table": "personal_agenda_events",
                "ordering": ["date", "start_time"],
            },
        ),
        migrations.AddIndex(
            model_name="personalagendaevent",
            index=models.Index(fields=["user", "date"], name="personal_age_user_id_89dd1d_idx"),
        ),
        migrations.AddIndex(
            model_name="personalagendaevent",
            index=models.Index(fields=["user", "status"], name="personal_age_user_id_63d8f2_idx"),
        ),
    ]
