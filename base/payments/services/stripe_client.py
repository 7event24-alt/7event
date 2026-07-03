import stripe
from django.conf import settings


class StripeIntegrationError(ValueError):
    pass


def configure():
    stripe.api_key = settings.STRIPE_API_KEY


def create_product_and_price(plan):
    from django.conf import settings

    if plan.stripe_product_id and plan.stripe_price_id:
        return plan.stripe_product_id, plan.stripe_price_id

    product = stripe.Product.create(
        name=plan.name,
        description=plan.description or None,
        metadata={"plan_id": str(plan.id), "plan_type": plan.type},
    )

    unit_amount = int(float(plan.price_monthly) * 100)
    price = stripe.Price.create(
        product=product.id,
        unit_amount=unit_amount,
        currency=settings.STRIPE_CURRENCY,
        recurring={"interval": "month", "interval_count": 1},
        metadata={"plan_id": str(plan.id)},
    )

    plan.stripe_product_id = product.id
    plan.stripe_price_id = price.id
    plan.save(update_fields=["stripe_product_id", "stripe_price_id"])
    return product.id, price.id


def create_checkout_session(user, plan, request):
    configure()
    _, price_id = create_product_and_price(plan)

    base_url = settings.APP_PUBLIC_URL or request.build_absolute_uri("/").rstrip("/")

    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        customer_email=user.email,
        client_reference_id=str(user.id),
        metadata={
            "user_id": str(user.id),
            "plan_id": str(plan.id),
        },
        success_url=base_url + "/app/planos/pagamento/sucesso/?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=base_url + "/app/planos/pagamento/falha/",
        payment_method_types=["card"],
        locale="pt-BR",
    )
    return session


def retrieve_subscription(subscription_id):
    configure()
    return stripe.Subscription.retrieve(subscription_id)


def cancel_at_period_end(subscription_id):
    configure()
    return stripe.Subscription.update(
        subscription_id,
        cancel_at_period_end=True,
    )


def resume_cancel_at_period_end(subscription_id):
    configure()
    return stripe.Subscription.update(
        subscription_id,
        cancel_at_period_end=False,
    )


def cancel_immediately(subscription_id):
    configure()
    return stripe.Subscription.delete(subscription_id)


def retrieve_invoice(invoice_id):
    configure()
    return stripe.Invoice.retrieve(invoice_id)


def retrieve_customer(customer_id):
    configure()
    return stripe.Customer.retrieve(customer_id)
