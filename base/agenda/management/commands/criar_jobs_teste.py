from datetime import date, time
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from base.clients.models import Client
from base.jobs.models import Job, EventType, JobStatus, PaymentType, PaymentStatusJob
from decimal import Decimal
import random

User = get_user_model()


class Command(BaseCommand):
    help = "Cria jobs de teste para o calendário"

    def handle(self, *args, **options):
        try:
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                self.stdout.write(self.style.ERROR("Nenhum super usuário encontrado"))
                return

            account = user.account
            if not account:
                self.stdout.write(self.style.ERROR("Usuário sem conta"))
                return

            if not Client.objects.exists():
                self.stdout.write(
                    self.style.ERROR(
                        "Nenhum cliente encontrado. Crie clientes primeiro."
                    )
                )
                return

            clients = list(Client.objects.all())
            today = date.today()

            job_titles = [
                "Show de Rock",
                "Casamento João e Maria",
                "Festa de Aniversário 15 anos",
                "Corporativo - Palestra",
                "Formatura",
                "Show de Pop",
                "Eventos Corporativos",
                "Casamento",
                "Aniversário",
                "Festival de Música",
            ]

            locations = [
                "São Paulo, SP - Arena Allianz Parque",
                "São Paulo, SP - Espaço das Américas",
                "São Paulo, SP - Villa Country",
                "São Paulo, SP - Tom Brasil",
                "São Paulo, SP - Centro de Convenções Sul",
                "São Paulo, SP - Teatro Municipal",
                "São Paulo, SP - Allianz Parque",
                "Campinas, SP - Expo D. Pedro",
                "Campinas, SP - Centro de Convenções",
                "Santos, SP - Arena Santos",
                "Ribeirão Preto, SP - Centro de Convenções",
                "São José dos Campos, SP - CenterVale",
                "Sorocaba, SP - Ginásio Municipal",
                "São Bernardo do Campo, SP - Espaço Promodal",
                "Santo André,SP - Teatro Municipal",
            ]

            statuses = list(JobStatus)
            event_types = list(EventType)
            payment_types = list(PaymentType)
            payment_statuses = list(PaymentStatusJob)

            jobs_created = 0
            days_to_create = 30
            start_day = 1

            for day_offset in range(days_to_create):
                current_date = today.replace(day=start_day + day_offset)

                num_jobs_today = random.randint(1, 3)

                for j in range(num_jobs_today):
                    job = Job.objects.create(
                        account=account,
                        client=random.choice(clients),
                        title=f"{random.choice(job_titles)} - {current_date.strftime('%d/%m')}",
                        event_type=random.choice(event_types),
                        start_date=current_date,
                        end_date=current_date,
                        start_time=time(
                            hour=random.randint(14, 20), minute=random.choice([0, 30])
                        ),
                        end_time=time(
                            hour=random.randint(22, 23), minute=random.choice([0, 30])
                        ),
                        location=random.choice(locations),
                        description=f"Evento de teste criado automaticamente para {current_date.strftime('%d/%m/%Y')}",
                        cache=Decimal(str(random.randint(1500, 8000))),
                        payment_type=random.choice(payment_types),
                        payment_status=random.choice(payment_statuses),
                        status=random.choice(statuses),
                    )
                    jobs_created += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"Criados {jobs_created} jobs de teste para os próximos {days_to_create} dias"
                )
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro: {str(e)}"))
