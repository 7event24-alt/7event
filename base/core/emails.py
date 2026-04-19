from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ssl


def send_html_email(to_email, subject, message):
    """Função genérica para enviar emails via SMTP direto"""
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = "7event <noreply@7event.com.br>"
        msg["To"] = to_email
        msg["Subject"] = subject

        # Parte texto plano
        text_part = MIMEText(message, "plain", "utf-8")
        msg.attach(text_part)

        # Criar contexto SSL
        context = ssl.create_default_context()

        # Enviar via SMTP SSL direta (porta 465)
        with smtplib.SMTP_SSL(
            "smtp.hostinger.com", 465, context=context, timeout=30
        ) as server:
            server.login("noreply@7event.com.br", "7Ev13579@")
            server.send_message(msg)

        return True
    except Exception as e:
        print(f"Erro ao enviar email: {e}")
        return False


def send_verification_email(user, verification_url):
    """Envia email de verificação de email usando template HTML"""
    subject = "Confirme seu email - 7event"

    html_message = render_to_string(
        "emails/verification.html", {"user": user, "verification_url": verification_url}
    )

    return send_html_email_with_template(user.email, subject, html_message)


def send_welcome_email(user, login_url=None):
    """Envia email de boas-vindas após cadastro usando template HTML"""
    subject = "Bem-vindo ao 7event!"

    html_message = render_to_string(
        "emails/welcome.html", {"user": user, "login_url": login_url}
    )

    return send_html_email_with_template(user.email, subject, html_message)


def send_new_job_notification(user, job, job_url=None):
    """Envia notificação por email quando novo trabalho é criado usando template HTML"""
    subject = f"Novo Trabalho: {job.title}"

    html_message = render_to_string(
        "emails/new_job.html", {"user": user, "job": job, "job_url": job_url}
    )

    return send_html_email_with_template(user.email, subject, html_message)


def send_job_confirmation_to_client(job):
    """Envia email de confirmação ao cliente quando o trabalho é confirmado"""
    if not job.client or not job.client.email:
        return False

    subject = f"Trabalho Confirmado: {job.title}"

    html_message = render_to_string("emails/job_confirmed.html", {"job": job})

    return send_html_email_with_template(job.client.email, subject, html_message)


def send_html_email_with_template(to_email, subject, html_message):
    """Função para enviar emails com template HTML"""
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = "7event <noreply@7event.com.br>"
        msg["To"] = to_email
        msg["Subject"] = subject

        # Parte texto plano como fallback
        import re

        text_content = re.sub("<[^<]+?>", "", html_message)
        text_part = MIMEText(text_content, "plain", "utf-8")
        msg.attach(text_part)

        # Parte HTML
        html_part = MIMEText(html_message, "html", "utf-8")
        msg.attach(html_part)

        # Criar contexto SSL
        context = ssl.create_default_context()

        # Enviar via SMTP SSL direta (porta 465)
        with smtplib.SMTP_SSL(
            "smtp.hostinger.com", 465, context=context, timeout=30
        ) as server:
            server.login("noreply@7event.com.br", "7Ev13579@")
            server.send_message(msg)

        return True
    except Exception as e:
        print(f"Erro ao enviar email: {e}")
        return False


def send_quote_email(quote, client_email):
    """Envia orçamento por email ao cliente"""
    if not client_email:
        return False

    subject = f"Orçamento: {quote.title}"

    html_message = render_to_string("emails/quote.html", {"quote": quote})

    return send_html_email_with_template(client_email, subject, html_message)


def send_support_reply(support_message):
    """Envia email de resposta ao cliente do suporte"""
    if not support_message.email:
        return False

    subject = f"Re: {support_message.get_subject_display()} - 7event Suporte"

    html_message = render_to_string(
        "emails/support_reply.html", {"message": support_message}
    )

    return send_html_email_with_template(support_message.email, subject, html_message)
