from django.views.generic import TemplateView
from django.shortcuts import render


def landing_page(request):
    # Get visible plans or create defaults
    from base.accounts.models import Plan, PlanType

    plans = Plan.objects.filter(is_visible=True).order_by("price_monthly")

    # If no plans, create defaults
    if not plans.exists():
        # Create Basic (Free) plan
        Plan.objects.create(
            type=PlanType.BASIC,
            name="Básico",
            short_description="Para autônomos que estão começando",
            max_clients=10,
            max_jobs=10,
            max_expenses=10,
            max_agenda_events=10,
            price_monthly=0,
            price_quarterly=0,
            price_semester=0,
            is_visible=True,
            highlight=False,
        )

        # Create Professional plan
        Plan.objects.create(
            type=PlanType.TESTER,
            name="Profissional",
            short_description="Para profissionais que precisam de mais",
            max_clients=0,  # unlimited
            max_jobs=0,
            max_expenses=0,
            max_agenda_events=0,
            price_monthly=97,
            price_quarterly=267,
            price_semester=497,
            is_visible=True,
            highlight=True,
        )

        # Create Business plan
        Plan.objects.create(
            type=PlanType.BUSINESS,
            name="Business",
            short_description="Para empresas que gerenciam equipe",
            max_users=10,
            max_clients=0,
            max_jobs=0,
            max_expenses=0,
            max_agenda_events=0,
            price_monthly=197,
            price_quarterly=537,
            price_semester=997,
            is_visible=True,
            highlight=False,
        )

        plans = Plan.objects.filter(is_visible=True).order_by("price_monthly")

    return render(
        request,
        "landingpage/index.html",
        {
            "hide_nav": True,
            "plans": plans,
        },
    )
