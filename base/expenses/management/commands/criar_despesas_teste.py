from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from base.jobs.models import Job
from base.expenses.models import Expense, ExpenseCategory
from decimal import Decimal
import random

User = get_user_model()


class Command(BaseCommand):
    help = "Cria despesas de teste vinculadas a jobs"

    def handle(self, *args, **options):
        try:
            user = User.objects.filter(is_superuser=True).first()
            if not user or not user.account:
                self.stdout.write(self.style.ERROR("Usuário ou conta não encontrada"))
                return

            jobs = list(Job.objects.filter(account=user.account)[:20])
            if not jobs:
                self.stdout.write(self.style.ERROR("Nenhum job encontrado"))
                return

            categories = list(ExpenseCategory)
            descriptions = {
                "equipment": [
                    "Aluguel de som",
                    "Aluguel de luz",
                    "Equipamento de vídeo",
                    "Instrumentos musicais",
                ],
                "transport": [
                    "Transporte de equipe",
                    "Frete de equipamentos",
                    "Translado",
                    "Combustível",
                ],
                "food": ["Coffee break", "Almoço equipe", "Lanches", "Refeições"],
                "accommodation": ["Hotel equipe", "Aluguel de espaço", "Hostel"],
                "marketing": ["Divulgação", "Material gráfico", "Redes sociais"],
                "fee": ["Taxa de inúmera", "Taxa de organização", "Comissão"],
                "other": ["Material de escritório", "Outros custos", "Suprimentos"],
            }

            expenses_created = 0
            for job in jobs:
                num_expenses = random.randint(1, 3)
                for _ in range(num_expenses):
                    category = random.choice(categories)
                    desc_list = descriptions.get(category.value, ["Despesa geral"])

                    expense = Expense.objects.create(
                        account=user.account,
                        user=user,
                        job=job,
                        category=category,
                        value=Decimal(str(random.randint(100, 1500))),
                        date=job.start_date - timedelta(days=random.randint(1, 5)),
                        description=random.choice(desc_list),
                    )
                    expenses_created += 1

            self.stdout.write(
                self.style.SUCCESS(f"Criadas {expenses_created} despesas de teste")
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro: {str(e)}"))
