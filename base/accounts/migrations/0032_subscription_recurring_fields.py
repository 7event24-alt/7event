from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0031_systemreminderdispatch"),
    ]

    operations = [
        migrations.AddField(
            model_name="subscription",
            name="billing_anchor_date",
            field=models.DateField(
                blank=True,
                null=True,
                verbose_name="Data âncora da cobrança",
            ),
        ),
        migrations.AddField(
            model_name="subscription",
            name="cancel_at_period_end",
            field=models.BooleanField(default=False, verbose_name="Cancelar no fim do período"),
        ),
        migrations.AddField(
            model_name="subscription",
            name="cancelled_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Cancelado em"),
        ),
        migrations.AddField(
            model_name="subscription",
            name="current_period_end",
            field=models.DateField(blank=True, null=True, verbose_name="Fim do período atual"),
        ),
        migrations.AddField(
            model_name="subscription",
            name="current_period_start",
            field=models.DateField(blank=True, null=True, verbose_name="Início do período atual"),
        ),
        migrations.AddField(
            model_name="subscription",
            name="financial_status",
            field=models.CharField(
                choices=[
                    ("regular", "Regular"),
                    ("inadimplente", "Inadimplente"),
                    ("suspenso", "Suspenso"),
                    ("cancelamento_agendado", "Cancelamento agendado"),
                    ("cancelado", "Cancelado"),
                ],
                default="regular",
                max_length=30,
                verbose_name="Status Financeiro",
            ),
        ),
        migrations.AddField(
            model_name="subscription",
            name="mp_subscription_id",
            field=models.CharField(blank=True, max_length=120, verbose_name="ID assinatura Mercado Pago"),
        ),
        migrations.AddField(
            model_name="subscription",
            name="past_due_since",
            field=models.DateField(blank=True, null=True, verbose_name="Inadimplente desde"),
        ),
        migrations.AddIndex(
            model_name="subscription",
            index=models.Index(fields=["financial_status"], name="sub_fin_status_idx"),
        ),
        migrations.AddIndex(
            model_name="subscription",
            index=models.Index(fields=["next_billing_date"], name="sub_next_billing_idx"),
        ),
    ]
