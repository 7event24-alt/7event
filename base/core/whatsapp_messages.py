"""Mensagens padrao para disparos de WhatsApp via n8n.

Centraliza textos por motivo/evento para evitar duplicacao e facilitar manutencao.
"""

from string import Template


WHATSAPP_MESSAGE_TEMPLATES = {
 "payment_approved": Template(
        "Oi, *$nome*!\n\n"
        "Seu pagamento foi aprovado com sucesso. 🎉\n"
        "Seu plano *$plano* já está ativo! ✅\n\n"
        "*_7event_*"
    ),
    # "payment_pending": Template(
    #     "Oi, *$nome*!\n\n"
    #     "Recebemos sua solicitação de pagamento e ela está pendente. ⏳\n"
    #     "Assim que houver a confirmação, seu plano será atualizado automaticamente.\n\n"
    #     "*_7event_*"
    # ),
    # "payment_failed": Template(
    #     "Oi, *$nome*!\n\n"
    #     "Não conseguimos aprovar seu pagamento. ❌\n"
    #     "Você pode tentar novamente no painel de planos do 7event.\n\n"
    #     "*_7event_*"
    # ),
    "user_registered": Template(
        "Oi, *$nome*!\n\n"
        "Cadastro realizado com sucesso! ✨\n"
        "Agora confirme seu e-mail para ativar sua conta. 📩\n\n"
        "*_7event_*"
    ),
    "user_activated": Template(
        "Parabéns, *$nome*!\n\n"
        "Sua conta foi ativada com sucesso. 🚀\n"
        "Bem-vindo(a) ao *7event*!"
    ),
    # "plan_downgraded_cutoff": Template(
    #     "Oi, *$nome*!\n\n"
    #     "Seu plano foi ajustado para FREE por falta de pagamento até o dia 15. ⚠️\n"
    #     "Ao regularizar, seu acesso ao plano pago é reativado automaticamente.\n\n"
    #     "*_7event_*"
    # ),
}


def get_whatsapp_message_template_keys():
    """Retorna a lista de motivos/eventos suportados."""
    return sorted(WHATSAPP_MESSAGE_TEMPLATES.keys())


def build_whatsapp_message(reason, **context):
    """Monta mensagem a partir do motivo e contexto.

    Exemplo:
        build_whatsapp_message("payment_approved", nome="Bia", plano="PRO")
    """
    if reason not in WHATSAPP_MESSAGE_TEMPLATES:
        raise ValueError(f"Motivo de mensagem nao suportado: {reason}")

    template = WHATSAPP_MESSAGE_TEMPLATES[reason]
    default_context = {
        "nome": "",
        "plano": "",
    }
    default_context.update(context)
    return template.safe_substitute(default_context).strip()
