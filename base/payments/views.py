import json

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import PaymentStatus, PaymentTransaction, PaymentWebhookEvent, WebhookProcessingStatus
from .services.billing import apply_approved_payment, apply_non_approved_status
from .services.mercadopago_client import get_payment


def _extract_event_data(request, payload):
    event_id = str(payload.get("id") or payload.get("event_id") or "").strip() or None
    topic = str(payload.get("type") or payload.get("topic") or request.GET.get("topic") or "").strip()

    data = payload.get("data") or {}
    resource_id = str(
        data.get("id")
        or payload.get("resource")
        or request.GET.get("data.id")
        or request.GET.get("id")
        or ""
    ).strip()
    return event_id, topic, resource_id


@csrf_exempt
def mercadopago_webhook(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        payload = {}

    event_id, topic, resource_id = _extract_event_data(request, payload)

    if event_id:
        existing = PaymentWebhookEvent.objects.filter(event_id=event_id).first()
        if existing and existing.processing_status in {
            WebhookProcessingStatus.PROCESSED,
            WebhookProcessingStatus.IGNORED,
        }:
            return JsonResponse({"received": True, "deduplicated": True}, status=200)

    event = PaymentWebhookEvent.objects.create(
        event_id=event_id,
        topic=topic,
        resource_id=resource_id,
        payload=payload,
    )

    if not resource_id:
        event.processing_status = WebhookProcessingStatus.IGNORED
        event.error_message = "resource_id ausente"
        event.processed_at = timezone.now()
        event.save(update_fields=["processing_status", "error_message", "processed_at"])
        return JsonResponse({"received": True, "ignored": True}, status=200)

    try:
        payment = get_payment(resource_id)
        external_reference = (payment.get("external_reference") or "").strip()
        if not external_reference:
            event.processing_status = WebhookProcessingStatus.IGNORED
            event.error_message = "external_reference ausente"
            event.processed_at = timezone.now()
            event.save(update_fields=["processing_status", "error_message", "processed_at"])
            return JsonResponse({"received": True, "ignored": True}, status=200)

        transaction_obj = PaymentTransaction.objects.filter(external_reference=external_reference).first()
        if not transaction_obj:
            event.processing_status = WebhookProcessingStatus.IGNORED
            event.error_message = f"transacao nao encontrada para {external_reference}"
            event.processed_at = timezone.now()
            event.save(update_fields=["processing_status", "error_message", "processed_at"])
            return JsonResponse({"received": True, "ignored": True}, status=200)

        if transaction_obj.status == PaymentStatus.APPROVED:
            event.processing_status = WebhookProcessingStatus.IGNORED
            event.error_message = "transacao ja aprovada"
            event.processed_at = timezone.now()
            event.save(update_fields=["processing_status", "error_message", "processed_at"])
            return JsonResponse({"received": True, "already_approved": True}, status=200)

        payment_status = (payment.get("status") or "").strip().lower()
        if payment_status == PaymentStatus.APPROVED:
            apply_approved_payment(transaction_obj, payment)
        else:
            apply_non_approved_status(transaction_obj, payment)

        event.processing_status = WebhookProcessingStatus.PROCESSED
        event.processed_at = timezone.now()
        event.save(update_fields=["processing_status", "processed_at"])
        return JsonResponse({"received": True, "processed": True}, status=200)
    except Exception as exc:
        event.processing_status = WebhookProcessingStatus.ERROR
        event.error_message = str(exc)[:2000]
        event.processed_at = timezone.now()
        event.save(update_fields=["processing_status", "error_message", "processed_at"])
        return JsonResponse({"received": True, "error": "processing_failed"}, status=200)
