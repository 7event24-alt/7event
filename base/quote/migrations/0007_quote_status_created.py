from django.db import migrations, models


def migrate_draft_to_created(apps, schema_editor):
    Quote = apps.get_model("quote", "Quote")
    Quote.objects.filter(status="draft").update(status="created")


def reverse_created_to_draft(apps, schema_editor):
    Quote = apps.get_model("quote", "Quote")
    Quote.objects.filter(status="created").update(status="draft")


class Migration(migrations.Migration):

    dependencies = [
        ("quote", "0006_add_created_by"),
    ]

    operations = [
        migrations.RunPython(migrate_draft_to_created, reverse_created_to_draft),
        migrations.AlterField(
            model_name="quote",
            name="hourly_rate",
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Valor da Diária"),
        ),
        migrations.AlterField(
            model_name="quote",
            name="status",
            field=models.CharField(
                choices=[
                    ("created", "Criado"),
                    ("sent", "Enviado"),
                    ("negotiation", "Em Negociação"),
                    ("accepted", "Aceito"),
                    ("rejected", "Recusado"),
                    ("cancelled", "Cancelado"),
                ],
                default="created",
                max_length=20,
                verbose_name="Status",
            ),
        ),
        migrations.AlterField(
            model_name="quote",
            name="work_hours",
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Quantidade de Diárias"),
        ),
    ]
