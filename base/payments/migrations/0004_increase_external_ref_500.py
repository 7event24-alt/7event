from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0003_increase_external_ref_length'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paymenttransaction',
            name='external_reference',
            field=models.CharField(max_length=500, unique=True),
        ),
    ]
