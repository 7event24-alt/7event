from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
from decimal import Decimal
from base.accounts.models import User, Account, AccountType, Plan
from base.jobs.models import Job, JobStatus, PaymentStatusJob, PaymentType, EventType
from base.clients.models import Client
from base.quote.models import Quote, QuoteStatus
from base.expenses.models import Expense, ExpenseCategory
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Creates robust test data for development"

    def handle(self, *args, **options):
        self.stdout.write("Creating test data...")
        User = get_user_model()

        account, _ = Account.objects.get_or_create(
            slug="empresa-teste",
            defaults={
                "name": "Empresa Teste",
                "account_type": AccountType.COMPANY,
                "plan": Plan.objects.first() or Plan.get_default(),
                "is_active": True,
            },
        )

        user, created = User.objects.get_or_create(
            username="teste",
            defaults={
                "email": "teste@teste.com",
                "first_name": "Usuario",
                "last_name": "Teste",
                "account": account,
                "is_active": True,
            },
        )
        if created:
            user.set_password("teste123")
            user.save()
            self.stdout.write(self.style.SUCCESS("User created: teste / teste123"))

        client_names = [
            "Empresa ABC Ltda",
            "João Silva MEI",
            "Maria Santos",
            "Pedro Costa",
            "Ana Oliveira",
            "Carlos Souza",
            "Julia Almeida",
            "Bruno Lima",
            "Carla Rodrigues",
            "Ricardo Ferreira",
            "Juliana Alves",
            "Fernando Pereira",
            "Renata Gomes",
            "Paulo Dias",
            "Luciana Ribeiro",
            "Marcos Cardoso",
            "Patricia Rocha",
            "Leonardo Torres",
            "Camila Lima",
            "Rodrigo Barbosa",
        ]

        clients = []
        for i, name in enumerate(client_names):
            client, _ = Client.objects.get_or_create(
                email=f"cliente{i}@teste.com",
                defaults={
                    "name": name,
                    "account": account,
                    "phone": f"1199999{4000 + i}",
                },
            )
            clients.append(client)

        statuses = list(JobStatus)
        payment_statuses = list(PaymentStatusJob)
        payment_types = list(PaymentType)
        event_types = list(EventType)
        quote_statuses = list(QuoteStatus)

        base_date = timezone.now().date()

        jobs = []
        for i in range(50):
            start_date = base_date + timedelta(days=random.randint(-30, 60))
            if start_date.weekday() in [5, 6]:
                start_date = start_date + timedelta(days=(7 - start_date.weekday()))

            client = random.choice(clients)
            status = random.choice(statuses)
            status_value = status.value if hasattr(status, "value") else status
            payment_status = random.choice(payment_statuses)
            payment_type = random.choice(payment_types)
            event_type = random.choice(event_types)

            try:
                job = Job.objects.create(
                    account=account,
                    user=user,
                    client=client,
                    title=f"{client.name} - {random.choice(['Casamento', 'Aniversário', 'Formatura', 'Corporativo', 'Event'])}",
                    description=f"Evento teste #{i + 1}",
                    status=status_value,
                    payment_status=payment_status.value
                    if hasattr(payment_status, "value")
                    else payment_status,
                    payment_type=payment_type.value
                    if hasattr(payment_type, "value")
                    else payment_type,
                    event_type=event_type.value
                    if hasattr(event_type, "value")
                    else event_type,
                    start_date=start_date,
                    end_date=start_date + timedelta(days=random.randint(0, 2)),
                    location=f"{random.choice(['Rua', 'Avenida'])} {random.randint(1, 500)}, São Paulo - SP",
                    cache=random.uniform(500, 15000)
                    if status_value != "cancelled"
                    else 0,
                )
                jobs.append(job)
            except Exception as e:
                pass

        job_count = len(jobs)

        quote_count = 0
        for i in range(20):
            client = random.choice(clients)
            quote_status = random.choice(quote_statuses)
            try:
                Quote.objects.create(
                    account=account,
                    client=client,
                    title=f"Orçamento {client.name} #{i + 1}",
                    description=f"Orçamento teste {i + 1}",
                    hourly_rate=Decimal(str(random.uniform(50, 200))),
                    work_hours=Decimal(str(random.randint(2, 12))),
                    labor_cost=Decimal(str(random.uniform(100, 1000))),
                    expenses_cost=Decimal(str(random.uniform(50, 500))),
                    total=Decimal(str(random.uniform(1000, 10000))),
                    status=quote_status.value
                    if hasattr(quote_status, "value")
                    else quote_status,
                )
                quote_count += 1
            except Exception as e:
                pass

        self.stdout.write(
            self.style.SUCCESS(
                f"Test data: teste/teste123 | {len(clients)} clientes | {job_count} trabalhos | {quote_count} orçamentos"
            )
        )
