from django.conf import settings

import mercadopago


class MercadoPagoIntegrationError(ValueError):
    pass


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


def create_preapproval(preapproval_data):
    sdk = get_client()
    response = sdk.preapproval().create(preapproval_data)
    if response.get("status") not in (200, 201):
        details = response.get("response") or {}
        message = str(details.get("message") or "").strip()
        causes = details.get("cause") or []
        cause_text = ""
        if isinstance(causes, list) and causes:
            compact = []
            for item in causes:
                if not isinstance(item, dict):
                    continue
                code = item.get("code")
                desc = item.get("description") or item.get("message")
                if code or desc:
                    compact.append(f"{code or 'cause'}: {desc}")
            if compact:
                cause_text = " | causas: " + "; ".join(compact)
        if "Both payer and collector must be real or test users" in message:
            raise MercadoPagoIntegrationError(
                "Mercado Pago recusou a assinatura: o pagador e o recebedor precisam ser do mesmo ambiente "
                "(ambos teste ou ambos producao)."
            )
        raise MercadoPagoIntegrationError(
            f"Falha ao criar assinatura Mercado Pago: {message or response}{cause_text}"
        )
    return response.get("response", {})


def get_preapproval(preapproval_id):
    sdk = get_client()
    response = sdk.preapproval().get(preapproval_id)
    if response.get("status") != 200:
        raise ValueError(f"Falha ao consultar assinatura Mercado Pago: {response}")
    return response.get("response", {})


def update_preapproval(preapproval_id, update_data):
    sdk = get_client()
    response = sdk.preapproval().update(preapproval_id, update_data)
    if response.get("status") not in (200, 201):
        raise ValueError(f"Falha ao atualizar assinatura Mercado Pago: {response}")
    return response.get("response", {})
