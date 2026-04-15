from django.views.generic import TemplateView
from django.shortcuts import render


def landing_page(request):
    # Get visible plans from database - same as system plans page
    from base.accounts.models import Plan

    plans = Plan.objects.filter(is_visible=True).order_by("price_monthly")

    return render(
        request,
        "landingpage/index.html",
        {
            "hide_nav": True,
            "plans": plans,
        },
    )
