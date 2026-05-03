from decimal import Decimal
from django.db.models import Sum


def format_currency(value):
    """Formata um valor decimal para o formato de moeda brasileira."""
    if value is None:
        return "R$ 0,00"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def calculate_total_expenses(job):
    """Calcula o total de despesas de um job."""
    return sum(expense.value for expense in job.expenses.filter(is_active=True))


def calculate_net_profit(job):
    """Calcula o lucro líquido de um job (cache - despesas)."""
    total_expenses = calculate_total_expenses(job)
    cache = job.cache or Decimal("0.00")
    return cache - total_expenses


def calculate_profit_margin(revenue, expenses):
    """Calcula a margem de lucro percentual."""
    if not revenue or revenue == 0:
        return Decimal("0")
    return ((revenue - expenses) / revenue) * 100


def calculate_job_financials(job):
    """Retorna um dict com todos os cálculos financeiros de um job."""
    cache = job.cache or Decimal("0.00")
    total_expenses = calculate_total_expenses(job)
    net_profit = cache - total_expenses
    profit_margin = calculate_profit_margin(cache, total_expenses)

    return {
        "cache": cache,
        "total_expenses": total_expenses,
        "net_profit": net_profit,
        "profit_margin": profit_margin,
    }


def sum_cache(queryset):
    """Soma o cache de um queryset de Jobs."""
    result = queryset.aggregate(total=Sum("cache"))["total"]
    return result or Decimal("0.00")


def sum_partial_payments(queryset):
    """Soma os pagamentos parciais de um queryset de Jobs."""
    result = queryset.aggregate(total=Sum("payment_partial_value"))["total"]
    return result or Decimal("0.00")