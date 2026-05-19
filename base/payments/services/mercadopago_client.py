from django.conf import settings

import mercadopago


def get_client():
    token = (settings.MP_ACCESS_TOKEN or "").strip()
    if not token:
        raise ValueError("MP_ACCESS_TOKEN nao configurado")
    return mercadopago.SDK(token)


def create_preference(preference_data):
    sdk = get_client()
    response = sdk.preference().create(preference_data)
    if response.get("status") not in (200, 201):
        raise ValueError(f"Falha ao criar preferencia Mercado Pago: {response}")
    return response.get("response", {})


def get_payment(payment_id):
    sdk = get_client()
    response = sdk.payment().get(payment_id)
    if response.get("status") != 200:
        raise ValueError(f"Falha ao consultar pagamento Mercado Pago: {response}")
    return response.get("response", {})
