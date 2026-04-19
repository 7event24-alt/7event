from django.views.generic import TemplateView
from django.shortcuts import render


def landing_page(request):
    # Get visible and active plans from database
    from base.accounts.models import Plan

    plans = Plan.objects.filter(is_visible=True, is_active=True).order_by(
        "price_monthly"
    )

    return render(
        request,
        "landingpage/index.html",
        {
            "hide_nav": True,
            "plans": plans,
        },
    )
