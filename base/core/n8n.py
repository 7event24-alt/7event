import json
import logging
import uuid
from datetime import UTC, datetime
from urllib import error, request

from django.conf import settings


logger = logging.getLogger(__name__)


def _normalize_br_phone(phone):
    digits = "".join(c for c in str(phone or "") if c.isdigit())
    if not digits:
        return ""
    if len(digits) in (10, 11):
        digits = "55" + digits
    return digits


def _post_n8n_payload(payload, timeout=10):
    """Send JSON payload to configured n8n webhook URL."""
    url = (getattr(settings, "N8N_WHATSAPP_WEBHOOK_URL", "") or "").strip()
    token = (getattr(settings, "N8N_WHATSAPP_WEBHOOK_TOKEN", "") or "").strip()

    if not url:
        logger.warning("N8N WhatsApp webhook URL not configured")
        return False, "N8N webhook URL not configured"

    headers = {
        "Content-Type": "application/json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=timeout) as response:
            status_code = response.getcode()
            body = response.read().decode("utf-8", errors="replace")
            if 200 <= status_code < 300:
                return True, body
            return False, body
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        logger.warning("N8N webhook HTTP error %s: %s", exc.code, body)
        return False, body
    except Exception as exc:
        logger.exception("Error sending payload to n8n webhook")
        return False, str(exc)


def send_whatsapp_message(phone, message, timeout=10, extra_payload=None):
    """Send a simple WhatsApp payload to n8n webhook.

    Payload base:
    {
        "numero": "5521991986769",
        "mensagem": "..."
    }
    """
    payload = {
        "numero": _normalize_br_phone(phone),
        "mensagem": str(message or "").strip(),
    }
    if extra_payload and isinstance(extra_payload, dict):
        payload.update(extra_payload)
    return _post_n8n_payload(payload=payload, timeout=timeout)


def send_whatsapp_by_reason(phone, reason, timeout=10, user=None, **context):
    """Monta mensagem por motivo e envia ao n8n.

    Se nao houver template para o motivo, nao faz requisicao.
    """
    from base.core.whatsapp_messages import (
        build_whatsapp_message,
        has_whatsapp_message_template,
    )

    if not has_whatsapp_message_template(reason):
        logger.info("WhatsApp template ausente para motivo '%s'; envio ignorado", reason)
        return False, "template_not_found"

    if user is not None and not getattr(user, "notify_via_whatsapp", True):
        logger.info(
            "WhatsApp desabilitado pelo usuario %s; envio ignorado para '%s'",
            getattr(user, "id", "n/a"),
            reason,
        )
        return False, "user_opted_out_whatsapp"

    message = build_whatsapp_message(reason, **context)
    return send_whatsapp_message(phone=phone, message=message, timeout=timeout)


def send_whatsapp_event(reason, phone, message, timeout=10, **context):
    """Send an event-like payload for realistic n8n flow tests.

    Example payload fields:
    - event_id
    - source
    - event
    - sent_at
    - numero
    - mensagem
    - context
    """
    payload = {
        "event_id": str(uuid.uuid4()),
        "source": "7event",
        "event": str(reason or "").strip(),
        "sent_at": datetime.now(UTC).isoformat(),
        "numero": _normalize_br_phone(phone),
        "mensagem": str(message or "").strip(),
        "context": context or {},
    }
    return _post_n8n_payload(payload=payload, timeout=timeout)
