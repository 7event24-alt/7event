from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0015_add_fcm_token'),
    ]

    operations = [
        migrations.AddField(
            model_name='fcmtoken',
            name='auth',
            field=models.CharField(blank=True, max_length=100, verbose_name='Token Auth'),
        ),
        migrations.AddField(
            model_name='fcmtoken',
            name='subscription',
            field=models.TextField(blank=True, verbose_name='Subscription JSON'),
        ),
        migrations.AddField(
            model_name='fcmtoken',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='Ativo'),
        ),
        migrations.AlterField(
            model_name='fcmtoken',
            name='token',
            field=models.CharField(blank=True, max_length=500, verbose_name='Token P256DH'),
        ),
    ]