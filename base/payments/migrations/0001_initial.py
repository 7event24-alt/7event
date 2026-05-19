from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("accounts", "0029_add_personal_limits_to_plan"),
    ]

    operations = [
        migrations.CreateModel(
            name="PaymentTransaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "provider",
                    models.CharField(
                        choices=[("mercadopago", "Mercado Pago")],
                        default="mercadopago",
                        max_length=30,
                    ),
                ),
                (
                    "billing_period",
                    models.CharField(
                        choices=[
                            ("monthly", "Mensal"),
                            ("quarterly", "Trimestral"),
                            ("semester", "Semestral"),
                        ],
                        default="monthly",
                        max_length=20,
                    ),
                ),
                ("billing_month", models.DateField(help_text="Primeiro dia do mes da cobranca")),
                ("external_reference", models.CharField(max_length=80, unique=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pendente"),
                            ("approved", "Aprovado"),
                            ("rejected", "Recusado"),
                            ("cancelled", "Cancelado"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("currency", models.CharField(default="BRL", max_length=10)),
                ("provider_preference_id", models.CharField(blank=True, max_length=100)),
                ("provider_payment_id", models.CharField(blank=True, max_length=100)),
                ("checkout_url", models.URLField(blank=True)),
                ("due_date", models.DateField()),
                ("grace_limit_date", models.DateField()),
                ("paid_at", models.DateTimeField(blank=True, null=True)),
                ("raw_payload", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "plan",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="accounts.plan",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="payment_transactions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "payment_transactions",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="PaymentWebhookEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "provider",
                    models.CharField(
                        choices=[("mercadopago", "Mercado Pago")],
                        default="mercadopago",
                        max_length=30,
                    ),
                ),
                ("event_id", models.CharField(blank=True, max_length=100, null=True, unique=True)),
                ("topic", models.CharField(blank=True, max_length=100)),
                ("resource_id", models.CharField(blank=True, max_length=120)),
                ("payload", models.JSONField(blank=True, default=dict)),
                (
                    "processing_status",
                    models.CharField(
                        choices=[
                            ("received", "Recebido"),
                            ("processed", "Processado"),
                            ("ignored", "Ignorado"),
                            ("error", "Erro"),
                        ],
                        default="received",
                        max_length=20,
                    ),
                ),
                ("error_message", models.TextField(blank=True)),
                ("processed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "payment_webhook_events",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="paymenttransaction",
            index=models.Index(fields=["billing_month", "status"], name="payment_tran_billing_4fcf61_idx"),
        ),
        migrations.AddIndex(
            model_name="paymenttransaction",
            index=models.Index(fields=["provider_payment_id"], name="payment_tran_provider_3a2163_idx"),
        ),
    ]
