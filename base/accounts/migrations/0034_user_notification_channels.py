from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0032_subscription_recurring_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="notify_via_email",
            field=models.BooleanField(default=True, verbose_name="Receber notificações por Email"),
        ),
        migrations.AddField(
            model_name="user",
            name="notify_via_whatsapp",
            field=models.BooleanField(default=True, verbose_name="Receber notificações por WhatsApp"),
        ),
    ]
