#!/usr/bin/env python
import os
import sys
import django
from datetime import date, timedelta
from decimal import Decimal
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model
from base.accounts.models import Account
from base.clients.models import Client
from base.jobs.models import Job, EventType, JobStatus, PaymentType, PaymentStatusJob
from base.expenses.models import Expense, ExpenseCategory
from base.services.models import Service

User = get_user_model()


def create_seed_data():
    superuser = User.objects.filter(is_superuser=True).first()
    if not superuser:
        print("Superuser not found!")
        return

    account = superuser.account
    if not account:
        print("Superuser has no account!")
        return

    print(f"Creating seed data for account: {account.name}")

    clients_data = [
        {
            "name": "Empresa ABC Ltda",
            "email": "contato@abc.com.br",
            "phone": "11999991111",
            "document": "12345678000199",
        },
        {
            "name": "XYZ Eventos",
            "email": "contato@xyz.com.br",
            "phone": "11999992222",
            "document": "98765432000188",
        },
        {
            "name": "Associação Cultural",
            "email": "cultural@associacao.org.br",
            "phone": "11999993333",
            "document": "45612378000177",
        },
        {
            "name": "Instituto Show",
            "email": "shows@institutshow.com.br",
            "phone": "11999994444",
            "document": "78901234000166",
        },
        {
            "name": "Clube Recreation",
            "email": "eventos@clube.com.br",
            "phone": "11999995555",
            "document": "32165478000155",
        },
    ]

    clients = []
    for c in clients_data:
        client, _ = Client.objects.get_or_create(
            account=account,
            name=c["name"],
            defaults={
                "email": c["email"],
                "phone": c["phone"],
                "document": c["document"],
                "is_active": True,
            },
        )
        clients.append(client)
        print(f"  Created client: {client.name}")

    services_data = [
        {
            "name": "Iluminação Completa",
            "description": "Serviço completo de iluminação",
            "estimated_duration_hours": Decimal("8.00"),
            "hourly_rate": Decimal("500.00"),
            "typical_expenses": Decimal("200.00"),
        },
        {
            "name": "Sonorização",
            "description": "Sistema de som profissional",
            "estimated_duration_hours": Decimal("8.00"),
            "hourly_rate": Decimal("450.00"),
            "typical_expenses": Decimal("150.00"),
        },
        {
            "name": "Video Live",
            "description": "Transmissão ao vivo",
            "estimated_duration_hours": Decimal("4.00"),
            "hourly_rate": Decimal("600.00"),
            "typical_expenses": Decimal("100.00"),
        },
        {
            "name": "Estrutura de Palco",
            "description": "Montagem de estrutura",
            "estimated_duration_hours": Decimal("12.00"),
            "hourly_rate": Decimal("350.00"),
            "typical_expenses": Decimal("500.00"),
        },
        {
            "name": "Operador de Câmera",
            "description": "Operador profissional",
            "estimated_duration_hours": Decimal("8.00"),
            "hourly_rate": Decimal("400.00"),
            "typical_expenses": Decimal("50.00"),
        },
    ]

    services = []
    for s in services_data:
        service, _ = Service.objects.get_or_create(
            account=account,
            name=s["name"],
            defaults={
                "description": s["description"],
                "estimated_duration_hours": s["estimated_duration_hours"],
                "hourly_rate": s["hourly_rate"],
                "typical_expenses": s["typical_expenses"],
                "is_active": True,
            },
        )
        services.append(service)
        print(f"  Created service: {service.name}")

    today = date.today()
    start_date = today - timedelta(days=730)

    event_types = list(EventType.values)
    job_statuses = list(JobStatus.values)
    payment_types = list(PaymentType.values)
    payment_statuses = list(PaymentStatusJob.values)

    jobs_count = 0
    current_date = start_date

    while current_date <= today and jobs_count < 30:
        num_jobs_this_month = random.randint(1, 2)

        for _ in range(num_jobs_this_month):
            if jobs_count >= 30:
                break

            client = random.choice(clients)
            event_type = random.choice(event_types)
            status = random.choice(job_statuses)
            payment_type = random.choice(payment_types)
            payment_status = random.choice(payment_statuses)

            job_title = f"Evento {event_type.replace('_', ' ').title()} - {client.name}"
            cache_value = Decimal(str(random.randint(2000, 15000)))

            job, created = Job.objects.get_or_create(
                account=account,
                user=superuser,
                client=client,
                title=job_title,
                defaults={
                    "event_type": event_type,
                    "start_date": current_date,
                    "end_date": current_date + timedelta(days=random.randint(0, 2)),
                    "location": "São Paulo, SP",
                    "description": f"Evento de {event_type.replace('_', ' ')}",
                    "cache": cache_value,
                    "payment_type": payment_type,
                    "payment_date": current_date
                    - timedelta(days=random.randint(5, 15)),
                    "payment_total": cache_value,
                    "status": status,
                    "payment_status": payment_status,
                },
            )

            if created:
                jobs_count += 1
                print(f"  Created job: {job.title} ({job.start_date})")

                num_expenses = random.randint(2, 4)
                for _ in range(num_expenses):
                    category = random.choice(list(ExpenseCategory.values))
                    Expense.objects.create(
                        account=account,
                        user=superuser,
                        job=job,
                        category=category,
                        value=Decimal(str(random.randint(100, 2000))),
                        date=current_date - timedelta(days=random.randint(1, 10)),
                        description=f"Despesa de {category}",
                    )
                print(f"    Added expenses for job")

        current_date += timedelta(days=random.randint(15, 30))

    print(f"\nCreated {len(clients)} clients")
    print(f"Created {jobs_count} jobs")
    print(f"Created {Expense.objects.filter(account=account).count()} expenses")
    print(f"Created {len(services)} services")
    print("\nDone!")


if __name__ == "__main__":
    create_seed_data()
