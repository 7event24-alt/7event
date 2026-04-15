import os
from datetime import datetime
from django.shortcuts import render
from django.template import TemplateDoesNotExist
from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse


def get_error_info(request):
    """Extract useful error information for reports"""
    return {
        "path": request.path,
        "method": request.method,
        "user": str(request.user) if request.user.is_authenticated else "Anonymous",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def bad_request(request, exception=None):
    """400 - Bad Request"""
    if not settings.DEBUG:
        return HttpResponseRedirect("/")

    error_info = get_error_info(request)
    return render(
        request,
        "errors/error.html",
        {
            "code": 400,
            "error_info": f"Requisição inválida: {request.path}",
            "timestamp": error_info["timestamp"],
        },
        status=400,
    )


def permission_denied(request, exception=None):
    """403 - Permission Denied"""
    if not settings.DEBUG:
        return HttpResponseRedirect("/")

    error_info = get_error_info(request)
    return render(
        request,
        "errors/error.html",
        {
            "code": 403,
            "error_info": f"Acesso negado ao recurso: {request.path}",
            "timestamp": error_info["timestamp"],
        },
        status=403,
    )


def page_not_found(request, exception=None):
    """404 - Page Not Found"""
    if not settings.DEBUG:
        return HttpResponseRedirect("/")

    error_info = get_error_info(request)
    return render(
        request,
        "errors/error.html",
        {
            "code": 404,
            "error_info": f"Página não encontrada: {request.path}",
            "timestamp": error_info["timestamp"],
        },
        status=404,
    )


def server_error(request):
    """500 - Server Error"""
    if not settings.DEBUG:
        try:
            from django.core.mail import send_mail

            error_info = get_error_info(request)
            subject = f"[7Event Error] 500 - {error_info['path']}"
            message = f"""
Um erro ocorreu no sistema 7Event:

Path: {error_info["path"]}
Method: {error_info["method"]}
User: {error_info["user"]}
Timestamp: {error_info["timestamp"]}

Por favor, verifique os logs para mais detalhes.
            """

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [getattr(settings, "ERROR_REPORT_EMAIL", "contato@7event.com.br")],
                fail_silently=True,
            )
        except Exception:
            pass

    if not settings.DEBUG:
        return HttpResponseRedirect("/")

    error_info = get_error_info(request)
    return render(
        request,
        "errors/error.html",
        {
            "code": 500,
            "error_info": "Erro interno do servidor. Nossa equipe foi notificada automaticamente.",
            "timestamp": error_info["timestamp"],
        },
        status=500,
    )
