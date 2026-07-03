from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0004_increase_external_ref_500'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paymenttransaction',
            name='checkout_url',
            field=models.URLField(blank=True, max_length=500),
        ),
    ]
