from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0014_add_assistente_camera'),
    ]

    operations = [
        migrations.CreateModel(
            name='FCMToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=500, verbose_name='Token FCM')),
                ('device_type', models.CharField(blank=True, max_length=20, verbose_name='Tipo do Dispositivo')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fcm_tokens', to='accounts.user', verbose_name='Usuário')),
            ],
            options={
                'verbose_name': 'Token FCM',
                'verbose_name_plural': 'Tokens FCM',
                'db_table': 'fcm_tokens',
                'ordering': ['-created_at'],
                'unique_together': {('user', 'token')},
            },
        ),
    ]